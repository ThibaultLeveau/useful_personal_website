"""Focused catalog, authorization, query, and projection tests for M12."""

# ruff: noqa: D101, D102, D103, D105, D107

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Self
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth import require_full_admin_session
from app.common.domain.actors import ActorContext
from app.common.domain.pagination import PageRequest
from app.common.security.authorization import AuthorizationDeniedError
from app.config import Environment, Settings
from app.main import create_app
from app.modules.audit.domain import (
    AUDIT_EVENT_CATALOG,
    ActorType,
    AuditEntry,
    AuditOutcome,
    AuditQuery,
    AuditValidationError,
    validate_audit_entry,
)
from app.modules.audit.service import AuditEntryNotFoundError, AuditQueryService
from app.modules.identity.domain import SessionView

ENTRY_ID = UUID("0198abc0-0000-7000-8000-000000000051")
ADMIN_ID = UUID("0198abc0-0000-7000-8000-000000000052")
NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


def entry(**overrides: object) -> AuditEntry:
    values: dict[str, object] = {
        "id": ENTRY_ID,
        "event_type": "project.published",
        "actor_type": ActorType.ADMINISTRATOR,
        "actor_id": ADMIN_ID,
        "actor_label_snapshot": None,
        "resource_type": "project",
        "resource_id": ENTRY_ID,
        "request_id": "audit-request-1",
        "occurred_at": NOW,
        "outcome": AuditOutcome.SUCCESS,
        "ip_pseudonym": None,
        "metadata": {"version": 2, "fields": "published_revision"},
        "schema_version": 1,
    }
    values.update(overrides)
    return AuditEntry(**values)  # type: ignore[arg-type]


class FakeRepository:
    def __init__(self, items: tuple[AuditEntry, ...]) -> None:
        self.items = items
        self.last_query: AuditQuery | None = None

    async def list(
        self, query: AuditQuery, page: PageRequest
    ) -> tuple[tuple[AuditEntry, ...], int]:
        self.last_query = query
        return self.items[page.offset : page.offset + page.page_size], len(self.items)

    async def get(self, entry_id: UUID) -> AuditEntry | None:
        return next((item for item in self.items if item.id == entry_id), None)


class FakeUow:
    def __init__(self, repository: FakeRepository) -> None:
        self.audit = repository

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


def service(items: tuple[AuditEntry, ...] = (entry(),)) -> AuditQueryService:
    repository = FakeRepository(items)
    return AuditQueryService(lambda: FakeUow(repository))  # type: ignore[arg-type]


def test_catalog_covers_required_families_and_validates_safe_metadata() -> None:
    """The frozen catalog covers every M1-M11 family and accepts bounded facts."""
    required_prefixes = {
        "admin.",
        "api_token.",
        "profile.",
        "website_settings.",
        "navigation.",
        "skill.",
        "experience.",
        "project.",
        "blog.",
        "page.",
        "media.",
        "contact.",
    }
    assert all(
        any(event.startswith(prefix) for event in AUDIT_EVENT_CATALOG)
        for prefix in required_prefixes
    )
    validate_audit_entry(entry())


@pytest.mark.parametrize(
    "unsafe",
    [
        entry(event_type="unknown.event"),
        entry(metadata={"password": "never"}),
        entry(metadata={"fields": "private\ncontent", "version": 2}),
        entry(schema_version=2),
    ],
)
def test_catalog_fails_closed_for_unknown_or_unsafe_facts(unsafe: AuditEntry) -> None:
    with pytest.raises(AuditValidationError):
        validate_audit_entry(unsafe)


def test_query_rejects_unknown_events_ambiguous_dates_and_unbounded_ids() -> None:
    with pytest.raises(AuditValidationError):
        AuditQuery(event_type="invented.event")
    with pytest.raises(AuditValidationError):
        AuditQuery(occurred_from=NOW, occurred_to=NOW - timedelta(seconds=1))
    with pytest.raises(AuditValidationError):
        AuditQuery(request_id="x" * 129)


async def test_service_is_admin_only_and_returns_deterministic_page_metadata() -> None:
    audit = service()
    result = await audit.list(
        ActorContext.administrator(ADMIN_ID),
        AuditQuery(event_type="project.published"),
        PageRequest(),
    )
    assert result.items[0].id == ENTRY_ID
    assert result.metadata.total_items == 1
    with pytest.raises(AuthorizationDeniedError):
        await audit.list(ActorContext.public(), AuditQuery(), PageRequest())


async def test_detail_is_admin_only_and_not_found_is_non_disclosing() -> None:
    audit = service()
    assert (await audit.get(ActorContext.administrator(ADMIN_ID), ENTRY_ID)).id == ENTRY_ID
    with pytest.raises(AuditEntryNotFoundError):
        await audit.get(
            ActorContext.administrator(ADMIN_ID),
            UUID("0198abc0-0000-7000-8000-000000000099"),
        )


async def _admin_session() -> SessionView:
    return SessionView(
        administrator_id=ADMIN_ID,
        display_name="Synthetic Owner",
        must_change_password=False,
        idle_expires_at=NOW + timedelta(hours=1),
        absolute_expires_at=NOW + timedelta(hours=12),
        session_id=UUID("0198abc0-0000-7000-8000-000000000053"),
    )


async def test_audit_api_is_private_correlated_and_rejects_query_ambiguity() -> None:
    application = create_app(settings=Settings(environment=Environment.TEST))
    application.state.audit_query_service = service()
    application.dependency_overrides[require_full_admin_session] = _admin_session
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/admin/audit?event_type=project.published")
        duplicate = await client.get(
            "/api/v1/admin/audit?event_type=project.published&event_type=project.published"
        )
        unsupported = await client.get("/api/v1/admin/audit?metadata=private")
        detail = await client.get(f"/api/v1/admin/audit/{ENTRY_ID}")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["meta"]["request_id"] == response.headers["X-Request-ID"]
    assert "ip_pseudonym" not in response.text
    assert duplicate.status_code == 422
    assert unsupported.status_code == 422
    assert detail.status_code == 200
