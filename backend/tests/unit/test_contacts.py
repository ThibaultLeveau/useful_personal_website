"""Contact lifecycle and proof regression tests."""
# ruff: noqa: D103, I001, PT018, TC001

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4
import pytest
from app.modules.contacts.domain import ContactState, ContactSubmission, ContactValidationError
from app.modules.contacts.ports import ContactUnitOfWorkFactory
from app.modules.contacts.service import ContactConfiguration, ContactService


def _contact(state: ContactState = ContactState.UNREAD) -> ContactSubmission:
    now = datetime(2026, 8, 4, tzinfo=UTC)
    return ContactSubmission(
        id=uuid4(),
        name="Ada",
        email="ada@example.test",
        subject="Hello",
        message="A private note",
        consented_at=now,
        policy_version="privacy-v1",
        source="contact_page",
        state=state,
        read_at=None if state is ContactState.UNREAD else now,
        archived_at=now if state is ContactState.ARCHIVED else None,
        created_at=now,
        updated_at=now,
        version=1,
    )


def test_contact_state_machine_and_timestamps() -> None:
    now = datetime(2026, 8, 5, tzinfo=UTC)
    read = _contact().transition(ContactState.READ, now=now)
    assert read.read_at == now and read.version == 2
    archived = read.transition(ContactState.ARCHIVED, now=now + timedelta(hours=1))
    restored = archived.transition(ContactState.READ, now=now + timedelta(hours=2))
    assert restored.archived_at is None and restored.version == 4


def test_contact_cannot_skip_from_unread_to_archived() -> None:
    with pytest.raises(ContactValidationError):
        _contact().transition(ContactState.ARCHIVED, now=datetime.now(UTC))


def test_contact_form_proof_is_deterministic_and_time_bound() -> None:
    service = ContactService(
        cast("ContactUnitOfWorkFactory", object()),
        ContactConfiguration("privacy-v1", "contact_page", 2, 3600, b"x" * 32, "key-v1"),
    )
    now = datetime(2026, 8, 4, 12, tzinfo=UTC)
    first = service.form_context(now=now)
    second = service.form_context(now=now)
    assert first == second
    assert len(first.proof) == 64
