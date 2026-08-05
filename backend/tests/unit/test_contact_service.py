"""Contact application-service persistence, lifecycle, and abuse-control tests."""

# mypy: disable-error-code="arg-type,no-untyped-def,var-annotated"
# ruff: noqa: ANN001, ANN002, ANN003, ANN202, ARG002, D103, PT018, TC001

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Self, cast
from uuid import UUID, uuid4

import pytest

from app.common.application.idempotency import IdempotencyDecision, IdempotencyDecisionType
from app.modules.contacts.domain import ContactState, ContactSubmission, ContactValidationError
from app.modules.contacts.ports import ContactUnitOfWorkFactory
from app.modules.contacts.service import (
    ContactConfiguration,
    ContactConflictError,
    ContactNotFoundError,
    ContactRateLimitedError,
    ContactRejectedError,
    ContactService,
)

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)
ACTOR = uuid4()


def _contact(state: ContactState = ContactState.UNREAD) -> ContactSubmission:
    return ContactSubmission(
        id=uuid4(),
        name="Ada",
        email="ada@example.test",
        subject="Hello",
        message="Message",
        consented_at=NOW,
        policy_version="privacy-v1",
        source="contact_page",
        state=state,
        read_at=None,
        archived_at=None,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )


class _Audit:
    def __init__(self) -> None:
        self.entries = []

    def append(self, entry) -> None:
        self.entries.append(entry)


class _RateLimits:
    allowed = True
    retry = 23

    async def admit_contact(self, _digest, _now):
        return self.allowed, self.retry


class _Idempotency:
    def __init__(self) -> None:
        self.decision = IdempotencyDecision(IdempotencyDecisionType.ACQUIRED, uuid4())
        self.completed = []

    async def acquire(self, _request):
        return self.decision

    async def complete(self, record_id, outcome, *, completed_at):
        self.completed.append((record_id, outcome, completed_at))


class _Contacts:
    def __init__(self) -> None:
        self.items: dict[UUID, ContactSubmission] = {}
        self.fail_update = False
        self.fail_delete = False
        self.purge_counts: list[int] = []

    async def database_now(self):
        return NOW + timedelta(hours=1)

    async def add(self, contact):
        self.items[contact.id] = contact

    async def get(self, contact_id, *, for_update=False):
        return self.items.get(contact_id)

    async def list(self, **_values):
        values = tuple(self.items.values())
        return values, len(values)

    async def update(self, contact, *, expected_version):
        if self.fail_update:
            raise LookupError
        self.items[contact.id] = contact

    async def delete(self, contact_id, *, expected_version):
        if self.fail_delete or self.items[contact_id].version != expected_version:
            raise LookupError
        del self.items[contact_id]

    async def purge(self, *, before, limit):
        return self.purge_counts.pop(0)


class _Uow:
    def __init__(self) -> None:
        self.contacts = _Contacts()
        self.rate_limits = _RateLimits()
        self.idempotency = _Idempotency()
        self.audit = _Audit()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


def _service(uow: _Uow) -> ContactService:
    return ContactService(
        cast("ContactUnitOfWorkFactory", lambda: uow),
        ContactConfiguration("privacy-v1", "contact_page", 0, 3600, b"x" * 32, "key-v1"),
    )


async def _submit(service: ContactService, **changes) -> None:
    context = service.form_context()
    values = {
        "name": " Ada ",
        "email": "ADA@EXAMPLE.TEST ",
        "subject": " Hello ",
        "message": " Message ",
        "consent": True,
        "policy_version": context.policy_version,
        "source": context.source,
        "issued_at": context.issued_at,
        "proof": context.proof,
        "honeypot": "",
        "idempotency_key": "contact-key-12345678",
        "client_ip": "192.0.2.1",
        "request_id": "request-contact",
    }
    values.update(changes)
    await service.submit(**values)


async def test_contact_submission_normalizes_persists_completes_and_audits() -> None:
    uow = _Uow()
    await _submit(_service(uow))
    item = next(iter(uow.contacts.items.values()))
    assert item.name == "Ada" and item.email == "ada@example.test"
    assert len(uow.idempotency.completed) == 1
    assert uow.audit.entries[0].event_type == "contact.submitted"
    assert uow.commits == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"email": "invalid"},
        {"consent": False},
        {"policy_version": "old"},
    ],
)
async def test_contact_submission_validates_public_fields(changes: dict[str, object]) -> None:
    with pytest.raises(ContactValidationError):
        await _submit(_service(_Uow()), **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"source": "forged"},
        {"honeypot": "bot"},
        {"proof": "invalid"},
    ],
)
async def test_contact_submission_rejects_automation_signals(changes: dict[str, object]) -> None:
    with pytest.raises(ContactRejectedError):
        await _submit(_service(_Uow()), **changes)


async def test_contact_submission_rate_limit_replay_and_admission_conflict() -> None:
    uow = _Uow()
    service = _service(uow)
    uow.rate_limits.allowed = False
    with pytest.raises(ContactRateLimitedError) as raised:
        await _submit(service)
    assert raised.value.retry_after == 23

    uow.rate_limits.allowed = True
    uow.idempotency.decision = IdempotencyDecision(
        IdempotencyDecisionType.REPLAY,
        uuid4(),
        outcome=__import__(
            "app.common.application.idempotency", fromlist=["IdempotencyOutcome"]
        ).IdempotencyOutcome(response_status=202, result_code="contact.accepted"),
    )
    await _submit(service)
    assert not uow.contacts.items

    uow.idempotency.decision = IdempotencyDecision(IdempotencyDecisionType.IN_PROGRESS)
    with pytest.raises(ContactRejectedError):
        await _submit(service)


async def test_contact_query_transition_delete_and_conflict_paths() -> None:
    uow = _Uow()
    service = _service(uow)
    item = _contact()
    uow.contacts.items[item.id] = item
    listed, total = await service.list(
        state=None, created_from=None, created_to=None, offset=0, limit=20, oldest_first=False
    )
    assert listed == (item,) and total == 1
    assert await service.get(item.id) == item
    with pytest.raises(ContactNotFoundError):
        await service.get(uuid4())

    with pytest.raises(ContactConflictError):
        await service.transition(
            item.id, ContactState.READ, expected_version=9, actor_id=ACTOR, request_id="stale"
        )
    uow.contacts.fail_update = True
    with pytest.raises(ContactConflictError):
        await service.transition(
            item.id, ContactState.READ, expected_version=1, actor_id=ACTOR, request_id="race"
        )
    uow.contacts.fail_update = False
    changed = await service.transition(
        item.id, ContactState.READ, expected_version=1, actor_id=ACTOR, request_id="read"
    )
    assert changed.state is ContactState.READ

    uow.contacts.fail_delete = True
    with pytest.raises(ContactConflictError):
        await service.delete(item.id, expected_version=2, actor_id=ACTOR, request_id="delete-race")
    uow.contacts.fail_delete = False
    await service.delete(item.id, expected_version=2, actor_id=ACTOR, request_id="delete")
    with pytest.raises(ContactNotFoundError):
        await service.delete(uuid4(), expected_version=1, actor_id=ACTOR, request_id="missing")


async def test_contact_purge_is_dry_run_first_and_batches_apply() -> None:
    uow = _Uow()
    service = _service(uow)
    uow.contacts.items[_contact().id] = _contact()
    _cutoff, eligible = await service.purge(retention_days=365, batch_size=2, apply=False)
    assert eligible == 1
    uow.contacts.purge_counts = [2, 2, 1]
    _cutoff, deleted = await service.purge(retention_days=365, batch_size=2, apply=True)
    assert deleted == 5 and uow.commits == 3
