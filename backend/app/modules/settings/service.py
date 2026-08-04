"""Website-settings application service and public facade."""

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
from app.modules.settings.domain import (
    PublicSiteSettings,
    WebsiteSettingsSnapshot,
    WebsiteSettingsValues,
    public_settings,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.modules.settings.ports import WebsiteSettingsUnitOfWorkFactory

_READ_POLICY = AccessPolicy(
    resource="website_settings",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_UPDATE_POLICY = AccessPolicy(
    resource="website_settings",
    action="update",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)


@dataclass(frozen=True, slots=True)
class UpdateWebsiteSettingsCommand:
    """Complete settings replacement input."""

    actor: ActorContext
    if_match: str | None
    request_id: str
    values: WebsiteSettingsValues


class WebsiteSettingsService:
    """Authorize and transact settings reads, updates, and public projection."""

    def __init__(
        self,
        uow_factory: WebsiteSettingsUnitOfWorkFactory,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Store deterministic transaction and time seams."""
        self._uow_factory = uow_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    async def admin_get(self, actor: ActorContext) -> WebsiteSettingsSnapshot:
        """Return complete non-secret settings to an administrator."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            return uow.settings.snapshot(await uow.settings.get())

    async def update(self, command: UpdateWebsiteSettingsCommand) -> WebsiteSettingsSnapshot:
        """Replace settings with optimistic concurrency and audit coupling."""
        require_authorized(command.actor, _UPDATE_POLICY)
        async with self._uow_factory() as uow:
            state = await uow.settings.get(for_update=True)
            require_matching_version(command.if_match, current_version=state.version)
            now = self._clock()
            uses = []
            title = command.values.website_name or "Website"
            if command.values.logo_media_id is not None:
                uses.append(
                    MediaUse(
                        asset_id=command.values.logo_media_id,
                        owner_type=MediaOwnerType.WEBSITE_SETTINGS,
                        owner_id=state.id,
                        role=MediaUsageRole.SITE_LOGO,
                        position=0,
                        purpose=MediaUsePurpose.MEANINGFUL,
                        alt_text=f"{title} logo",
                        caption=None,
                        public=True,
                    )
                )
            if command.values.favicon_media_id is not None:
                uses.append(
                    MediaUse(
                        asset_id=command.values.favicon_media_id,
                        owner_type=MediaOwnerType.WEBSITE_SETTINGS,
                        owner_id=state.id,
                        role=MediaUsageRole.SITE_FAVICON,
                        position=0,
                        purpose=MediaUsePurpose.DECORATIVE,
                        alt_text="",
                        caption=None,
                        public=True,
                    )
                )
            if command.values.social_image_media_id is not None:
                uses.append(
                    MediaUse(
                        asset_id=command.values.social_image_media_id,
                        owner_type=MediaOwnerType.WEBSITE_SETTINGS,
                        owner_id=state.id,
                        role=MediaUsageRole.SITE_SOCIAL_IMAGE,
                        position=0,
                        purpose=MediaUsePurpose.MEANINGFUL,
                        alt_text=f"{title} social preview",
                        caption=None,
                        public=True,
                    )
                )
            await uow.media.replace_owner_usages(
                owner_type=MediaOwnerType.WEBSITE_SETTINGS.value,
                owner_id=state.id,
                usages=tuple(uses),
                now=now,
            )
            uow.settings.replace(state, command.values, now=now)
            uow.audit.append(
                AuditEntry(
                    id=uuid7(),
                    event_type="website_settings.updated",
                    actor_type=AuditActorType.ADMINISTRATOR,
                    actor_id=command.actor.actor_id,
                    actor_label_snapshot=None,
                    resource_type="website_settings",
                    resource_id=state.id,
                    request_id=command.request_id,
                    occurred_at=now,
                    outcome=AuditOutcome.SUCCESS,
                    ip_pseudonym=None,
                    metadata={"version": state.version},
                    schema_version=1,
                )
            )
            snapshot = uow.settings.snapshot(state)
            await uow.commit()
            return snapshot

    async def public_get(self) -> PublicSiteSettings:
        """Return the deliberate public settings projection."""
        async with self._uow_factory() as uow:
            return public_settings(uow.settings.snapshot(await uow.settings.get()))
