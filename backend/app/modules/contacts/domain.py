"""Contact domain values and lifecycle invariants."""
# ruff: noqa: D101, D102, D107, EM101

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class ContactState(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class ContactValidationError(ValueError):
    def __init__(self, path: str, code: str) -> None:
        super().__init__("contact input is invalid")
        self.path = path
        self.code = code


@dataclass(frozen=True, slots=True)
class ContactSubmission:
    id: UUID
    name: str
    email: str
    subject: str
    message: str
    consented_at: datetime
    policy_version: str
    source: str
    state: ContactState
    read_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int

    def transition(self, target: ContactState, *, now: datetime) -> ContactSubmission:
        allowed = {
            ContactState.UNREAD: {ContactState.READ},
            ContactState.READ: {ContactState.ARCHIVED},
            ContactState.ARCHIVED: {ContactState.READ},
        }
        if target not in allowed[self.state]:
            raise ContactValidationError("state", "invalid_transition")
        return replace(
            self,
            state=target,
            read_at=now if target is ContactState.READ else self.read_at,
            archived_at=now if target is ContactState.ARCHIVED else None,
            updated_at=now,
            version=self.version + 1,
        )
