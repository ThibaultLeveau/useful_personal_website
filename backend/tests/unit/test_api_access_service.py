"""API-token application-service lifecycle and fail-closed branch tests."""

# mypy: disable-error-code="no-untyped-def,var-annotated"
# ruff: noqa: ANN001, ANN002, ANN003, ANN202, ARG002, D103, PT018, TC001

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Self, cast
from uuid import UUID, uuid4

import pytest

from app.modules.api_access.domain import ApiTokenMetadata, ApiTokenScope
from app.modules.api_access.ports import ApiTokenUnitOfWorkFactory
from app.modules.api_access.security import digest_api_token, issue_api_token
from app.modules.api_access.service import (
    ApiTokenAuthenticationError,
    ApiTokenConfiguration,
    ApiTokenConflictError,
    ApiTokenNotFoundError,
    ApiTokenRateLimitedError,
    ApiTokenService,
)

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)
OWNER = uuid4()
PEPPER = b"api-token-test-pepper-is-at-least-32-bytes"


class _Audit:
    def __init__(self) -> None:
        self.entries = []

    def append(self, entry) -> None:
        self.entries.append(entry)


class _RateLimits:
    allowed = True
    retry = 17
    calls: list[bool]

    def __init__(self) -> None:
        self.calls = []

    async def admit_api_token(self, _subject, _now, *, valid: bool):
        self.calls.append(valid)
        return self.allowed, self.retry


class _Tokens:
    def __init__(self) -> None:
        self.items: dict[UUID, ApiTokenMetadata] = {}
        self.auth: dict[str, tuple[ApiTokenMetadata, bytes, str]] = {}
        self.active_total = 0
        self.duplicate = False
        self.fail_revoke = False
        self.touched: list[UUID] = []

    async def database_now(self):
        return NOW

    async def add(self, *, metadata, secret_digest, key_version, owner_id, display_suffix):
        self.items[metadata.id] = metadata
        self.auth[metadata.public_id] = (metadata, secret_digest, key_version)

    async def list(self, **_values):
        values = tuple(self.items.values())
        return values, len(values)

    async def get_metadata(self, token_id, *, for_update=False):
        return self.items.get(token_id)

    async def find_auth(self, public_id):
        return self.auth.get(public_id)

    async def revoke(self, token_id, *, expected_version, now, reason):
        if self.fail_revoke:
            raise LookupError
        item = self.items[token_id]
        updated = replace(
            item,
            revoked_at=now,
            revocation_reason=reason,
            version=item.version + 1,
        )
        self.items[token_id] = updated
        if token_id in {value[0].id for value in self.auth.values()}:
            _old, digest, key_version = self.auth[item.public_id]
            self.auth[item.public_id] = (updated, digest, key_version)

    async def touch_used(self, token_id, *, now):
        self.touched.append(token_id)

    async def active_count(self, _owner_id, *, now):
        return self.active_total

    async def name_exists(self, _owner_id, _name, *, exclude_id=None):
        return self.duplicate


class _Uow:
    def __init__(self) -> None:
        self.tokens = _Tokens()
        self.audit = _Audit()
        self.rate_limits = _RateLimits()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


def _service(uow: _Uow, *, maximum: int = 50) -> ApiTokenService:
    return ApiTokenService(
        cast("ApiTokenUnitOfWorkFactory", lambda: uow),
        ApiTokenConfiguration(PEPPER, "key-v1", maximum),
    )


async def _created(service: ApiTokenService):
    return await service.create(
        owner_id=OWNER,
        name="  release   automation ",
        scopes=frozenset({ApiTokenScope.CONTENT_READ}),
        expires_at=NOW + timedelta(days=30),
        confirm_no_expiry=False,
        request_id="request-create",
    )


async def test_token_lifecycle_lists_rotates_revokes_and_audits() -> None:
    uow = _Uow()
    service = _service(uow)
    created = await _created(service)
    assert created.metadata.name == "release automation"
    assert len(uow.audit.entries) == 1 and uow.commits == 1

    items, total, now = await service.list(owner_id=OWNER, offset=0, limit=20, status=None)
    assert items == (created.metadata,) and total == 1 and now == NOW
    found, found_now = await service.get(created.metadata.id)
    assert found == created.metadata and found_now == NOW

    rotated = await service.rotate(
        created.metadata.id,
        owner_id=OWNER,
        expected_version=1,
        expires_at=None,
        confirm_no_expiry=True,
        request_id="request-rotate",
    )
    assert rotated.metadata.rotated_from_id == created.metadata.id
    assert uow.tokens.items[created.metadata.id].revocation_reason == "rotated"

    revoked = await service.revoke(
        rotated.metadata.id,
        owner_id=OWNER,
        expected_version=1,
        request_id="request-revoke",
    )
    assert revoked.revocation_reason == "administrator_revoked"
    assert [entry.event_type for entry in uow.audit.entries] == [
        "api_token.created",
        "api_token.rotated",
        "api_token.revoked",
    ]


async def test_token_create_and_lookup_reject_limits_duplicates_and_absence() -> None:
    uow = _Uow()
    service = _service(uow, maximum=1)
    uow.tokens.active_total = 1
    with pytest.raises(ApiTokenConflictError):
        await _created(service)

    uow.tokens.active_total = 0
    uow.tokens.duplicate = True
    with pytest.raises(ValueError, match="invalid"):
        await _created(service)
    with pytest.raises(ApiTokenNotFoundError):
        await service.get(uuid4())


@pytest.mark.parametrize("operation", ["revoke", "rotate"])
async def test_token_mutations_reject_missing_stale_and_storage_conflicts(operation: str) -> None:
    uow = _Uow()
    service = _service(uow)
    token_id = uuid4()
    kwargs = {
        "owner_id": OWNER,
        "expected_version": 1,
        "request_id": "request-mutate",
    }
    if operation == "rotate":
        kwargs.update(expires_at=None, confirm_no_expiry=True)
    with pytest.raises(ApiTokenNotFoundError):
        await getattr(service, operation)(token_id, **kwargs)

    created = await _created(service)
    kwargs["expected_version"] = 99
    with pytest.raises(ApiTokenConflictError):
        await getattr(service, operation)(created.metadata.id, **kwargs)

    kwargs["expected_version"] = 1
    uow.tokens.fail_revoke = True
    with pytest.raises(ApiTokenConflictError):
        await getattr(service, operation)(created.metadata.id, **kwargs)


async def test_token_authentication_accepts_valid_scope_and_records_usage() -> None:
    uow = _Uow()
    service = _service(uow)
    created = await _created(service)
    actor = await service.authenticate(
        created.plaintext,
        required_scopes=frozenset({ApiTokenScope.CONTENT_READ}),
        request_id="request-use",
    )
    assert actor.actor_id == created.metadata.id
    assert uow.tokens.touched == [created.metadata.id]
    assert uow.audit.entries[-1].event_type == "api_token.used"


async def test_token_authentication_fails_closed_for_all_invalid_states() -> None:
    uow = _Uow()
    service = _service(uow)
    with pytest.raises(ApiTokenAuthenticationError):
        await service.authenticate("malformed", required_scopes=frozenset(), request_id="bad")

    issued = issue_api_token(PEPPER)
    item = ApiTokenMetadata(
        id=uuid4(),
        public_id=issued.public_id,
        name="reader",
        display_suffix=issued.display_suffix,
        scopes=frozenset({ApiTokenScope.CONTENT_READ}),
        created_at=NOW,
        expires_at=None,
        last_used_at=None,
        revoked_at=None,
        revocation_reason=None,
        rotated_from_id=None,
        version=1,
    )
    uow.tokens.items[item.id] = item
    wrong_digest = digest_api_token(PEPPER, item.public_id, "wrong")
    uow.tokens.auth[item.public_id] = (item, wrong_digest, "key-v1")
    with pytest.raises(ApiTokenAuthenticationError):
        await service.authenticate(issued.plaintext, required_scopes=frozenset(), request_id="bad")

    uow.tokens.auth[item.public_id] = (item, issued.digest, "old-key")
    with pytest.raises(ApiTokenAuthenticationError):
        await service.authenticate(issued.plaintext, required_scopes=frozenset(), request_id="bad")

    uow.tokens.auth[item.public_id] = (item, issued.digest, "key-v1")
    with pytest.raises(ApiTokenAuthenticationError):
        await service.authenticate(
            issued.plaintext,
            required_scopes=frozenset({ApiTokenScope.MEDIA_WRITE}),
            request_id="bad",
        )

    uow.rate_limits.allowed = False
    with pytest.raises(ApiTokenRateLimitedError) as raised:
        await service.authenticate(
            issued.plaintext, required_scopes=frozenset(), request_id="limited"
        )
    assert raised.value.retry_after == 17
