"""Profile application service and publication facade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.common.domain.actors import ActorContext, ActorType
from app.common.domain.concurrency import require_matching_version
from app.common.security.authorization import AccessPolicy, require_authorized
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7
from app.modules.media.domain import (
    MediaOwnerType,
    MediaUsageRole,
    MediaUse,
    MediaUsePurpose,
)
from app.modules.profile.domain import ProfileSnapshot, ProfileValues, PublicProfile, public_profile

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.modules.profile.ports import ProfileUnitOfWorkFactory

_READ_POLICY = AccessPolicy(
    resource="profile",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_UPDATE_POLICY = AccessPolicy(
    resource="profile",
    action="update",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)


@dataclass(frozen=True, slots=True)
class UpdateProfileCommand:
    """Complete singleton profile replacement."""

    actor: ActorContext
    if_match: str | None
    request_id: str
    values: ProfileValues


class ProfileService:
    """Authorize and transact profile reads, updates, and public projection."""

    def __init__(
        self,
        uow_factory: ProfileUnitOfWorkFactory,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Store deterministic transaction and time seams."""
        self._uow_factory = uow_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def admin_get(self, actor: ActorContext) -> ProfileSnapshot:
        """Return the complete profile to an authorized administrator."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return uow.profile.snapshot(await uow.profile.get())

    async def update(self, command: UpdateProfileCommand) -> ProfileSnapshot:
        """Replace the profile with optimistic concurrency and audit coupling."""
        require_authorized(command.actor, _UPDATE_POLICY)
        async with self._uow_factory() as uow:
            state = await uow.profile.get(for_update=True)
            require_matching_version(command.if_match, current_version=state.version)
            now = self._clock()
            usages = (
                (
                    MediaUse(
                        asset_id=command.values.profile_image_id,
                        owner_type=MediaOwnerType.PROFILE,
                        owner_id=state.id,
                        role=MediaUsageRole.PROFILE_IMAGE,
                        position=0,
                        purpose=MediaUsePurpose.MEANINGFUL,
                        alt_text=(
                            f"Portrait of {command.values.full_name}"
                            if command.values.full_name
                            else "Profile portrait"
                        ),
                        caption=None,
                        public=True,
                    ),
                )
                if command.values.profile_image_id is not None
                else ()
            )
            await uow.media.replace_owner_usages(
                owner_type=MediaOwnerType.PROFILE.value,
                owner_id=state.id,
                usages=usages,
                now=now,
            )
            uow.profile.replace(state, command.values, now=now)
            uow.audit.append(
                AuditEntry(
                    id=uuid7(),
                    event_type="profile.updated",
                    actor_type=AuditActorType.ADMINISTRATOR,
                    actor_id=command.actor.actor_id,
                    actor_label_snapshot=None,
                    resource_type="profile",
                    resource_id=state.id,
                    request_id=command.request_id,
                    occurred_at=now,
                    outcome=AuditOutcome.SUCCESS,
                    ip_pseudonym=None,
                    metadata={"version": state.version},
                    schema_version=1,
                )
            )
            snapshot = uow.profile.snapshot(state)
            await uow.commit()
            return snapshot

    async def public_get(self) -> PublicProfile:
        """Return only explicitly approved public fields."""
        async with self._uow_factory() as uow:
            return public_profile(uow.profile.snapshot(await uow.profile.get()))
