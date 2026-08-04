"""Disclosure-safe audit list and detail contracts."""

# ruff: noqa: TC001, TC003

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.v1.schemas import ApiModel
from app.modules.audit.domain import ActorType, AuditOutcome


class AuditEntryData(ApiModel):
    """Safe projection that deliberately excludes IP pseudonyms."""

    id: UUID
    event_type: str = Field(max_length=80)
    actor_type: ActorType
    actor_id: UUID | None
    actor_label: str | None = Field(default=None, max_length=80)
    resource_type: str | None = Field(default=None, max_length=80)
    resource_id: UUID | None
    request_id: str = Field(max_length=128)
    occurred_at: datetime
    outcome: AuditOutcome
    metadata: dict[str, str]
    schema_version: int = Field(ge=1)


class AuditEventCatalogData(ApiModel):
    """Exact filter options backed by the frozen server catalog."""

    events: list[str]
