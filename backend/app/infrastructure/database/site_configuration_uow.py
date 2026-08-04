"""SQLAlchemy repositories and UoW for the M3 site-configuration modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from sqlalchemy import delete, select

from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.idempotency import IdempotencyRepository
from app.infrastructure.database.media import MediaRepository
from app.infrastructure.database.site_configuration import (
    FooterColumnRecord,
    FooterItemRecord,
    FooterRecord,
    NavigationItemRecord,
    NavigationMenuRecord,
    ProfileRecord,
    WebsiteSettingsRecord,
)
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.identity.domain import uuid7
from app.modules.navigation.domain import (
    FooterColumn,
    FooterItem,
    FooterItemKind,
    FooterTree,
    LinkKind,
    LinkTarget,
    NavigationItem,
    NavigationTree,
)
from app.modules.profile.domain import (
    ContactPreference,
    ProfileSnapshot,
    ProfileValues,
    PublicProfileField,
)
from app.modules.profile.domain import (
    SocialLink as ProfileSocialLink,
)
from app.modules.settings.domain import (
    AnalyticsProvider,
    ThemePolicy,
    WebsiteSettingsSnapshot,
    WebsiteSettingsValues,
)
from app.modules.settings.domain import (
    SocialLink as SettingsSocialLink,
)

if TYPE_CHECKING:
    from datetime import datetime
    from types import TracebackType
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.infrastructure.database.session import AsyncSessionFactory
    from app.modules.navigation.ports import NavigationUnitOfWork
    from app.modules.profile.ports import ProfileState, ProfileUnitOfWork
    from app.modules.settings.ports import WebsiteSettingsState, WebsiteSettingsUnitOfWork


class ProfileRepository:
    """Translate the profile singleton between ORM and domain values."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned session."""
        self._session = session

    async def get(self, *, for_update: bool = False) -> ProfileRecord:
        """Load the singleton profile, optionally locking it."""
        statement = select(ProfileRecord).where(ProfileRecord.singleton_key == 1)
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one()

    def replace(self, state: ProfileState, values: ProfileValues, *, now: datetime) -> None:
        """Replace allow-listed fields and advance the version."""
        state.full_name = values.full_name
        state.professional_title = values.professional_title
        state.short_biography = values.short_biography
        state.full_biography = values.full_biography
        state.profile_image_id = values.profile_image_id
        state.location = values.location
        state.availability = values.availability
        state.email = values.email
        state.social_links = [
            {"label": link.label, "url": link.url} for link in values.social_links
        ]
        state.github_url = values.github_url
        state.linkedin_url = values.linkedin_url
        state.personal_values = list(values.personal_values)
        state.work_preferences = list(values.work_preferences)
        state.resume_url = values.resume_url
        state.contact_preference = values.contact_preference.value
        state.public_fields = sorted(field.value for field in values.public_fields)
        state.updated_at = now
        state.version += 1

    def snapshot(self, state: ProfileState) -> ProfileSnapshot:
        """Map mutable persistence state to an immutable snapshot."""
        return ProfileSnapshot(
            id=state.id,
            full_name=state.full_name,
            professional_title=state.professional_title,
            short_biography=state.short_biography,
            full_biography=state.full_biography,
            profile_image_id=state.profile_image_id,
            location=state.location,
            availability=state.availability,
            email=state.email,
            social_links=tuple(
                ProfileSocialLink(label=link["label"], url=link["url"])
                for link in state.social_links
            ),
            github_url=state.github_url,
            linkedin_url=state.linkedin_url,
            personal_values=tuple(state.personal_values),
            work_preferences=tuple(state.work_preferences),
            resume_url=state.resume_url,
            contact_preference=ContactPreference(state.contact_preference),
            public_fields=frozenset(PublicProfileField(field) for field in state.public_fields),
            created_at=state.created_at,
            updated_at=state.updated_at,
            version=state.version,
        )


class WebsiteSettingsRepository:
    """Translate the non-secret settings singleton."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned session."""
        self._session = session

    async def get(self, *, for_update: bool = False) -> WebsiteSettingsRecord:
        """Load the singleton settings, optionally locking them."""
        statement = select(WebsiteSettingsRecord).where(WebsiteSettingsRecord.singleton_key == 1)
        if for_update:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).scalar_one()

    def replace(
        self,
        state: WebsiteSettingsState,
        values: WebsiteSettingsValues,
        *,
        now: datetime,
    ) -> None:
        """Replace allow-listed non-secret fields and advance the version."""
        state.website_name = values.website_name
        state.default_title = values.default_title
        state.default_description = values.default_description
        state.logo_media_id = values.logo_media_id
        state.favicon_media_id = values.favicon_media_id
        state.social_image_media_id = values.social_image_media_id
        state.default_locale = values.default_locale
        state.timezone = values.timezone
        state.theme_policy = values.theme_policy.value
        state.primary_color = values.primary_color
        state.accent_color = values.accent_color
        state.contact_email = values.contact_email
        state.contact_phone = values.contact_phone
        state.social_links = [
            {"label": link.label, "url": link.url} for link in values.social_links
        ]
        state.seo_title_suffix = values.seo_title_suffix
        state.seo_description = values.seo_description
        state.analytics_provider = values.analytics_provider.value
        state.analytics_public_id = values.analytics_public_id
        state.public_availability = values.public_availability
        state.updated_at = now
        state.version += 1

    def snapshot(self, state: WebsiteSettingsState) -> WebsiteSettingsSnapshot:
        """Map mutable persistence state to an immutable snapshot."""
        return WebsiteSettingsSnapshot(
            id=state.id,
            website_name=state.website_name,
            default_title=state.default_title,
            default_description=state.default_description,
            logo_media_id=state.logo_media_id,
            favicon_media_id=state.favicon_media_id,
            social_image_media_id=state.social_image_media_id,
            default_locale=state.default_locale,
            timezone=state.timezone,
            theme_policy=ThemePolicy(state.theme_policy),
            primary_color=state.primary_color,
            accent_color=state.accent_color,
            contact_email=state.contact_email,
            contact_phone=state.contact_phone,
            social_links=tuple(
                SettingsSocialLink(label=link["label"], url=link["url"])
                for link in state.social_links
            ),
            seo_title_suffix=state.seo_title_suffix,
            seo_description=state.seo_description,
            analytics_provider=AnalyticsProvider(state.analytics_provider),
            analytics_public_id=state.analytics_public_id,
            public_availability=state.public_availability,
            created_at=state.created_at,
            updated_at=state.updated_at,
            version=state.version,
        )


class NavigationRepository:
    """Load or atomically replace the complete primary navigation tree."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned session."""
        self._session = session

    async def get(self, *, for_update: bool = False) -> NavigationTree:
        """Load the aggregate in a bounded two-query plan."""
        statement = select(NavigationMenuRecord).where(NavigationMenuRecord.singleton_key == 1)
        if for_update:
            statement = statement.with_for_update()
        menu = (await self._session.execute(statement)).scalar_one()
        rows = (
            await self._session.execute(
                select(NavigationItemRecord)
                .where(NavigationItemRecord.menu_id == menu.id)
                .order_by(
                    NavigationItemRecord.parent_id.asc().nullsfirst(),
                    NavigationItemRecord.position,
                    NavigationItemRecord.id,
                )
            )
        ).scalars()
        return NavigationTree(
            id=menu.id,
            items=tuple(
                NavigationItem(
                    id=row.id,
                    parent_id=row.parent_id,
                    label=row.label,
                    link_kind=LinkKind(row.link_kind),
                    href=row.href,
                    target=LinkTarget(row.target),
                    visible=row.visible,
                    position=row.position,
                    version=row.version,
                )
                for row in rows
            ),
            version=menu.version,
        )

    async def replace(
        self,
        tree: NavigationTree,
        *,
        expected_version: int,
        now: datetime,
    ) -> NavigationTree:
        """Delete and recreate the validated complete tree atomically."""
        menu = (
            await self._session.execute(
                select(NavigationMenuRecord)
                .where(NavigationMenuRecord.singleton_key == 1)
                .with_for_update()
            )
        ).scalar_one()
        if menu.id != tree.id or menu.version != expected_version:
            msg = "navigation aggregate changed while locked"
            raise RuntimeError(msg)
        await self._session.execute(
            delete(NavigationItemRecord).where(NavigationItemRecord.menu_id == menu.id)
        )
        await self._session.flush()
        roots = [item for item in tree.items if item.parent_id is None]
        children = [item for item in tree.items if item.parent_id is not None]
        for item in roots:
            self._session.add(self._record(menu.id, item, now))
        await self._session.flush()
        for item in children:
            self._session.add(self._record(menu.id, item, now))
        menu.updated_at = now
        menu.version += 1
        await self._session.flush()
        return NavigationTree(id=menu.id, items=tree.items, version=menu.version)

    @staticmethod
    def _record(menu_id: UUID, item: NavigationItem, now: datetime) -> NavigationItemRecord:
        """Translate one validated domain node."""
        return NavigationItemRecord(
            id=item.id,
            menu_id=menu_id,
            parent_id=item.parent_id,
            label=item.label,
            link_kind=item.link_kind.value,
            href=item.href,
            target=item.target.value,
            visible=item.visible,
            position=item.position,
            created_at=now,
            updated_at=now,
            version=1,
        )


class FooterRepository:
    """Load or atomically replace the complete footer tree."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the caller-owned session."""
        self._session = session

    async def get(self, *, for_update: bool = False) -> FooterTree:
        """Load the aggregate in at most three queries."""
        statement = select(FooterRecord).where(FooterRecord.singleton_key == 1)
        if for_update:
            statement = statement.with_for_update()
        footer = (await self._session.execute(statement)).scalar_one()
        columns = list(
            (
                await self._session.execute(
                    select(FooterColumnRecord)
                    .where(FooterColumnRecord.footer_id == footer.id)
                    .order_by(FooterColumnRecord.position, FooterColumnRecord.id)
                )
            ).scalars()
        )
        column_ids = [column.id for column in columns]
        items_by_column: dict[object, list[FooterItemRecord]] = {
            column_id: [] for column_id in column_ids
        }
        if column_ids:
            items = (
                await self._session.execute(
                    select(FooterItemRecord)
                    .where(FooterItemRecord.column_id.in_(column_ids))
                    .order_by(
                        FooterItemRecord.column_id, FooterItemRecord.position, FooterItemRecord.id
                    )
                )
            ).scalars()
            for item in items:
                items_by_column[item.column_id].append(item)
        return FooterTree(
            id=footer.id,
            copyright_text=footer.copyright_text,
            columns=tuple(
                FooterColumn(
                    id=column.id,
                    title=column.title,
                    visible=column.visible,
                    position=column.position,
                    items=tuple(self._item(item) for item in items_by_column[column.id]),
                    version=column.version,
                )
                for column in columns
            ),
            version=footer.version,
        )

    async def replace(
        self,
        tree: FooterTree,
        *,
        expected_version: int,
        now: datetime,
    ) -> FooterTree:
        """Delete and recreate the validated complete footer atomically."""
        footer = (
            await self._session.execute(
                select(FooterRecord).where(FooterRecord.singleton_key == 1).with_for_update()
            )
        ).scalar_one()
        if footer.id != tree.id or footer.version != expected_version:
            msg = "footer aggregate changed while locked"
            raise RuntimeError(msg)
        column_ids = select(FooterColumnRecord.id).where(FooterColumnRecord.footer_id == footer.id)
        await self._session.execute(
            delete(FooterItemRecord).where(FooterItemRecord.column_id.in_(column_ids))
        )
        await self._session.execute(
            delete(FooterColumnRecord).where(FooterColumnRecord.footer_id == footer.id)
        )
        await self._session.flush()
        for column in tree.columns:
            self._session.add(
                FooterColumnRecord(
                    id=column.id,
                    footer_id=footer.id,
                    title=column.title,
                    visible=column.visible,
                    position=column.position,
                    created_at=now,
                    updated_at=now,
                    version=1,
                )
            )
        await self._session.flush()
        for column in tree.columns:
            for item in column.items:
                self._session.add(
                    FooterItemRecord(
                        id=item.id,
                        column_id=column.id,
                        label=item.label,
                        link_kind=item.link_kind.value,
                        item_kind=item.item_kind.value,
                        href=item.href,
                        target=item.target.value,
                        visible=item.visible,
                        position=item.position,
                        created_at=now,
                        updated_at=now,
                        version=1,
                    )
                )
        footer.copyright_text = tree.copyright_text
        footer.updated_at = now
        footer.version += 1
        await self._session.flush()
        return FooterTree(
            id=footer.id,
            copyright_text=footer.copyright_text,
            columns=tree.columns,
            version=footer.version,
        )

    @staticmethod
    def _item(row: FooterItemRecord) -> FooterItem:
        return FooterItem(
            id=row.id,
            label=row.label,
            link_kind=LinkKind(row.link_kind),
            item_kind=FooterItemKind(row.item_kind),
            href=row.href,
            target=LinkTarget(row.target),
            visible=row.visible,
            position=row.position,
            version=row.version,
        )


class SqlAlchemySiteConfigurationUnitOfWork:
    """Bind all M3 repositories to one shared transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        """Store the session factory without opening a connection."""
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.profile: ProfileRepository
        self.settings: WebsiteSettingsRepository
        self.navigation: NavigationRepository
        self.footer: FooterRepository
        self.audit: AuditRepository
        self.idempotency: IdempotencyRepository
        self.media: MediaRepository

    async def __aenter__(self) -> Self:
        """Open the transaction and bind repository adapters."""
        await self._inner.__aenter__()
        self.profile = ProfileRepository(self._inner.session)
        self.settings = WebsiteSettingsRepository(self._inner.session)
        self.navigation = NavigationRepository(self._inner.session)
        self.footer = FooterRepository(self._inner.session)
        self.audit = AuditRepository(self._inner.session)
        self.idempotency = IdempotencyRepository(self._inner.session)
        self.media = MediaRepository(self._inner.session, id_factory=uuid7)
        return self

    async def commit(self) -> None:
        """Commit at the application-service boundary."""
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Delegate rollback and resource cleanup."""
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class SqlAlchemySiteConfigurationUnitOfWorkFactory:
    """Create structurally typed profile/settings/navigation transactions."""

    session_factory: AsyncSessionFactory

    def profile(self) -> ProfileUnitOfWork:
        """Create a profile-typed transaction."""
        return cast(
            "ProfileUnitOfWork", SqlAlchemySiteConfigurationUnitOfWork(self.session_factory)
        )

    def settings(self) -> WebsiteSettingsUnitOfWork:
        """Create a settings-typed transaction."""
        return cast(
            "WebsiteSettingsUnitOfWork",
            SqlAlchemySiteConfigurationUnitOfWork(self.session_factory),
        )

    def navigation(self) -> NavigationUnitOfWork:
        """Create a navigation-typed transaction."""
        return cast(
            "NavigationUnitOfWork",
            SqlAlchemySiteConfigurationUnitOfWork(self.session_factory),
        )
