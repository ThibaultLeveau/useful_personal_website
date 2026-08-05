"""Persistence-neutral controlled audit facts."""

# ruff: noqa: C420, D105, EM101, PLR2004, TRY003

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class ActorType(StrEnum):
    """Controlled M1 audit actor types."""

    ADMINISTRATOR = "administrator"
    ANONYMOUS = "anonymous"
    SYSTEM = "system"


class AuditOutcome(StrEnum):
    """Controlled M1 audit outcomes."""

    DENIED = "denied"
    FAILURE = "failure"
    SUCCESS = "success"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Allow-listed append-only audit entry."""

    id: UUID
    event_type: str
    actor_type: ActorType
    actor_id: UUID | None
    actor_label_snapshot: str | None
    resource_type: str | None
    resource_id: UUID | None
    request_id: str
    occurred_at: datetime
    outcome: AuditOutcome
    ip_pseudonym: bytes | None
    metadata: dict[str, str | int | bool | None]
    schema_version: int


@dataclass(frozen=True, slots=True)
class AuditEventDefinition:
    """Versioned metadata allow-list for one durable event identifier."""

    metadata_keys: frozenset[str] = frozenset()


_VERSION_FIELDS = AuditEventDefinition(frozenset({"version", "fields"}))
_NO_METADATA = AuditEventDefinition()

AUDIT_EVENT_CATALOG: dict[str, AuditEventDefinition] = {
    **{
        event: _NO_METADATA
        for event in (
            "admin.login_rate_limited",
            "admin.login_failed",
            "admin.login_succeeded",
            "admin.logout",
            "admin.password_change_failed",
            "admin.password_changed",
        )
    },
    "admin.bootstrap_succeeded": AuditEventDefinition(frozenset({"source"})),
    **{
        event: _VERSION_FIELDS
        for event in (
            "profile.updated",
            "website_settings.updated",
            "navigation.updated",
            "footer.updated",
            "skill_category.created",
            "skill_category.updated",
            "skill_category.deleted",
            "skill_category.reordered",
            "skill.created",
            "skill.updated",
            "skill.deleted",
            "skill.reordered",
            "experience.created",
            "experience.draft_saved",
            "experience.published",
            "experience.rescheduled",
            "experience.unpublished",
            "experience.visibility_changed",
            "experience.reordered",
            "experience.deleted",
            "project.created",
            "project.draft_saved",
            "project.published",
            "project.rescheduled",
            "project.unpublished",
            "project.visible_changed",
            "project.featured_changed",
            "project.reordered",
            "project.deleted",
            "blog.post_created",
            "blog.draft_saved",
            "blog.post_published",
            "blog.post_rescheduled",
            "blog.post_unpublished",
            "blog.post_visibility_changed",
            "blog.posts_reordered",
            "blog.post_deleted",
            "blog.taxonomy_created",
            "blog.taxonomy_updated",
            "blog.taxonomies_reordered",
            "blog.taxonomy_deleted",
            "page.created",
            "page.saved",
            "page.duplicated",
            "page.block_added",
            "page.block_updated",
            "page.block_duplicated",
            "page.blocks_reordered",
            "page.block_hidden",
            "page.block_shown",
            "page.block_deleted",
            "page.published",
            "page.rescheduled",
            "page.unpublished",
            "page.deleted",
        )
    },
    "media.upload.accepted": AuditEventDefinition(frozenset({"byte_size", "status"})),
    "media.upload.ready": AuditEventDefinition(
        frozenset({"format", "width", "height", "byte_size", "variant_count"})
    ),
    "media.metadata.updated": _VERSION_FIELDS,
    "media.delete.requested": AuditEventDefinition(frozenset({"version"})),
    "media.delete.completed": AuditEventDefinition(frozenset({"object_count"})),
    "media.upload.failed": AuditEventDefinition(frozenset({"reason"})),
    "contact.submitted": AuditEventDefinition(frozenset({"policy_version", "source"})),
    "contact.unread": AuditEventDefinition(frozenset({"prior_state"})),
    "contact.read": AuditEventDefinition(frozenset({"prior_state"})),
    "contact.archived": AuditEventDefinition(frozenset({"prior_state"})),
    "contact.deleted": AuditEventDefinition(frozenset({"prior_state"})),
    "api_token.created": AuditEventDefinition(frozenset({"scope_count", "has_expiry", "rotated"})),
    "api_token.rotated": AuditEventDefinition(frozenset({"predecessor_id", "scope_count"})),
    "api_token.revoked": AuditEventDefinition(frozenset({"reason"})),
    "api_token.used": AuditEventDefinition(frozenset({"required_scope_count"})),
    "demo.seeded": AuditEventDefinition(frozenset({"changed_aggregates"})),
    "audit.retention_executed": AuditEventDefinition(
        frozenset({"deleted_count", "retention_days", "run_id"})
    ),
}

_SAFE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_FORBIDDEN_METADATA_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "cookie",
    "csrf",
    "email",
    "message",
    "body",
    "raw_ip",
    "storage_key",
    "connection",
    "sql",
    "stack",
)


class AuditValidationError(ValueError):
    """An audit fact is outside the frozen safe catalog."""


def validate_audit_entry(entry: AuditEntry) -> None:
    """Fail closed before an unknown or unsafe fact reaches persistence."""
    definition = AUDIT_EVENT_CATALOG.get(entry.event_type)
    if definition is None or _SAFE_IDENTIFIER.fullmatch(entry.event_type) is None:
        raise AuditValidationError("unknown audit event")
    if entry.schema_version != 1:
        raise AuditValidationError("unsupported audit schema version")
    if len(entry.request_id) > 128 or any(ch in entry.request_id for ch in "\r\n"):
        raise AuditValidationError("invalid audit correlation")
    if entry.actor_label_snapshot is not None and (
        len(entry.actor_label_snapshot) > 80
        or _SAFE_IDENTIFIER.fullmatch(entry.actor_label_snapshot) is None
    ):
        raise AuditValidationError("invalid safe actor label")
    keys = frozenset(entry.metadata)
    if keys - definition.metadata_keys:
        raise AuditValidationError("audit metadata key is not allowed")
    if any(
        fragment in key.casefold() for key in keys for fragment in _FORBIDDEN_METADATA_FRAGMENTS
    ):
        raise AuditValidationError("forbidden audit metadata key")
    for value in entry.metadata.values():
        if isinstance(value, str) and (len(value) > 128 or "\r" in value or "\n" in value):
            raise AuditValidationError("audit metadata value is not bounded")


@dataclass(frozen=True, slots=True)
class AuditQuery:
    """Typed exact-match and UTC interval filters for administrator inspection."""

    event_type: str | None = None
    actor_type: ActorType | None = None
    actor_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    outcome: AuditOutcome | None = None
    occurred_from: datetime | None = None
    occurred_to: datetime | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        if self.event_type is not None and self.event_type not in AUDIT_EVENT_CATALOG:
            raise AuditValidationError("unknown event filter")
        if (
            self.resource_type is not None
            and _SAFE_IDENTIFIER.fullmatch(self.resource_type) is None
        ):
            raise AuditValidationError("invalid resource filter")
        if self.request_id is not None and (
            not self.request_id
            or len(self.request_id) > 128
            or any(ch in self.request_id for ch in "\r\n")
        ):
            raise AuditValidationError("invalid request filter")
        if self.occurred_from is not None and self.occurred_from.utcoffset() is None:
            raise AuditValidationError("from date must be timezone-aware")
        if self.occurred_to is not None and self.occurred_to.utcoffset() is None:
            raise AuditValidationError("to date must be timezone-aware")
        if (
            self.occurred_from is not None
            and self.occurred_to is not None
            and self.occurred_from >= self.occurred_to
        ):
            raise AuditValidationError("date interval must be half-open")
