"""Explicit, deterministic, production-refusing fictional demo-content seed."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import SecretStr

from app.config import Environment
from app.infrastructure.database import DatabaseConfig, create_database_runtime
from app.infrastructure.database.audit import AuditRepository
from app.infrastructure.database.site_configuration_uow import (
    FooterRepository,
    NavigationRepository,
    ProfileRepository,
    WebsiteSettingsRepository,
)
from app.infrastructure.database.skills_uow import CategoryRepository, SkillRepository
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from app.modules.audit.domain import ActorType, AuditEntry, AuditOutcome
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
    validate_footer,
    validate_navigation,
)
from app.modules.profile.domain import (
    ContactPreference,
    ProfileSnapshot,
    ProfileValues,
    PublicProfileField,
)
from app.modules.settings.domain import (
    AnalyticsProvider,
    ThemePolicy,
    WebsiteSettingsSnapshot,
    WebsiteSettingsValues,
)
from app.modules.skills.domain import Skill, SkillCategory

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import TracebackType
    from typing import Self

    from app.infrastructure.database.session import AsyncSessionFactory

EXIT_INVALID_INPUT = 2
EXIT_PRODUCTION_REFUSED = 4
DEMO_REQUEST_ID = "seed-demo"
DEMO_ROOT_ID = UUID("00000000-0000-7000-8000-000000000341")
DEMO_ABOUT_ID = UUID("00000000-0000-7000-8000-000000000342")
DEMO_FOOTER_COLUMN_ID = UUID("00000000-0000-7000-8000-000000000343")
DEMO_FOOTER_ITEM_ID = UUID("00000000-0000-7000-8000-000000000344")
DEMO_SKILLS_NAVIGATION_ID = UUID("00000000-0000-7000-8000-000000000345")
DEMO_SKILLS_FOOTER_ITEM_ID = UUID("00000000-0000-7000-8000-000000000346")
DEMO_ENGINEERING_CATEGORY_ID = UUID("00000000-0000-7000-8000-000000000347")
DEMO_PRODUCT_CATEGORY_ID = UUID("00000000-0000-7000-8000-000000000348")
DEMO_PYTHON_SKILL_ID = UUID("00000000-0000-7000-8000-000000000351")
DEMO_API_DESIGN_SKILL_ID = UUID("00000000-0000-7000-8000-000000000352")
DEMO_INTERNAL_TOOLING_SKILL_ID = UUID("00000000-0000-7000-8000-000000000353")
DEMO_ACCESSIBILITY_SKILL_ID = UUID("00000000-0000-7000-8000-000000000354")
DEMO_DESIGN_SYSTEMS_SKILL_ID = UUID("00000000-0000-7000-8000-000000000355")


class _DemoSeedUnitOfWork:
    """Compose M3 and M4 repositories into one all-or-nothing seed transaction."""

    def __init__(self, session_factory: AsyncSessionFactory) -> None:
        self._inner = SqlAlchemyUnitOfWork(session_factory)
        self.profile: ProfileRepository
        self.settings: WebsiteSettingsRepository
        self.navigation: NavigationRepository
        self.footer: FooterRepository
        self.categories: CategoryRepository
        self.skills: SkillRepository
        self.audit: AuditRepository

    async def __aenter__(self) -> Self:
        await self._inner.__aenter__()
        session = self._inner.session
        self.profile = ProfileRepository(session)
        self.settings = WebsiteSettingsRepository(session)
        self.navigation = NavigationRepository(session)
        self.footer = FooterRepository(session)
        self.categories = CategoryRepository(session)
        self.skills = SkillRepository(session)
        self.audit = AuditRepository(session)
        return self

    async def commit(self) -> None:
        await self._inner.commit()

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._inner.__aexit__(exception_type, exception, traceback)


@dataclass(frozen=True, slots=True)
class DemoSeedResult:
    """Safe aggregate-only outcome suitable for operator output."""

    profile_id: UUID
    settings_id: UUID
    navigation_id: UUID
    footer_id: UUID
    changed_aggregates: int
    navigation_items: int
    footer_columns: int
    footer_items: int
    skill_categories: int
    skills: int


def _profile_values() -> ProfileValues:
    return ProfileValues(
        full_name="Avery Vale — Fictional Demo",
        professional_title="Independent product engineer",
        short_biography=(
            "A fictional portfolio owner demonstrating privacy-aware site configuration."
        ),
        full_biography=None,
        profile_image_id=None,
        location=None,
        availability=None,
        email=None,
        social_links=(),
        github_url=None,
        linkedin_url=None,
        personal_values=("Clarity", "Craft", "Care"),
        work_preferences=("Thoughtful collaboration", "Sustainable pace"),
        resume_url=None,
        contact_preference=ContactPreference.NONE,
        public_fields=frozenset(
            {
                PublicProfileField.FULL_NAME,
                PublicProfileField.PROFESSIONAL_TITLE,
                PublicProfileField.SHORT_BIOGRAPHY,
                PublicProfileField.PERSONAL_VALUES,
                PublicProfileField.WORK_PREFERENCES,
            }
        ),
    )


def _settings_values() -> WebsiteSettingsValues:
    return WebsiteSettingsValues(
        website_name="Vale Studio — Fictional Demo",
        default_title="Independent product engineering",
        default_description="A fictional personal-site configuration used for local demonstration.",
        logo_media_id=None,
        favicon_media_id=None,
        social_image_media_id=None,
        default_locale="en",
        timezone="UTC",
        theme_policy=ThemePolicy.SYSTEM,
        primary_color="#315C87",
        accent_color="#C56A3A",
        contact_email=None,
        contact_phone=None,
        social_links=(),
        seo_title_suffix="Vale Studio",
        seo_description="Fictional demonstration portfolio content.",
        analytics_provider=AnalyticsProvider.NONE,
        analytics_public_id=None,
        public_availability=None,
    )


def _navigation(current: NavigationTree) -> NavigationTree:
    tree = NavigationTree(
        id=current.id,
        items=(
            NavigationItem(
                id=DEMO_ROOT_ID,
                parent_id=None,
                label="Home",
                link_kind=LinkKind.INTERNAL,
                href="/",
                target=LinkTarget.SAME_WINDOW,
                visible=True,
                position=0,
            ),
            NavigationItem(
                id=DEMO_ABOUT_ID,
                parent_id=None,
                label="About",
                link_kind=LinkKind.INTERNAL,
                href="/about",
                target=LinkTarget.SAME_WINDOW,
                visible=True,
                position=1,
            ),
            NavigationItem(
                id=DEMO_SKILLS_NAVIGATION_ID,
                parent_id=None,
                label="Skills",
                link_kind=LinkKind.INTERNAL,
                href="/skills",
                target=LinkTarget.SAME_WINDOW,
                visible=True,
                position=2,
            ),
        ),
        version=current.version,
    )
    validate_navigation(tree.items)
    return tree


def _footer(current: FooterTree) -> FooterTree:
    tree = FooterTree(
        id=current.id,
        copyright_text="Fictional demo content. No rights claim is asserted.",
        columns=(
            FooterColumn(
                id=DEMO_FOOTER_COLUMN_ID,
                title="Explore",
                visible=True,
                position=0,
                items=(
                    FooterItem(
                        id=DEMO_FOOTER_ITEM_ID,
                        label="About",
                        link_kind=LinkKind.INTERNAL,
                        item_kind=FooterItemKind.LINK,
                        href="/about",
                        target=LinkTarget.SAME_WINDOW,
                        visible=True,
                        position=0,
                    ),
                    FooterItem(
                        id=DEMO_SKILLS_FOOTER_ITEM_ID,
                        label="Skills",
                        link_kind=LinkKind.INTERNAL,
                        item_kind=FooterItemKind.LINK,
                        href="/skills",
                        target=LinkTarget.SAME_WINDOW,
                        visible=True,
                        position=1,
                    ),
                ),
            ),
        ),
        version=current.version,
    )
    validate_footer(tree.columns)
    return tree


def _profile_matches(snapshot: ProfileSnapshot, values: ProfileValues) -> bool:
    return (
        snapshot.full_name,
        snapshot.professional_title,
        snapshot.short_biography,
        snapshot.full_biography,
        snapshot.location,
        snapshot.availability,
        snapshot.email,
        snapshot.social_links,
        snapshot.github_url,
        snapshot.linkedin_url,
        snapshot.personal_values,
        snapshot.work_preferences,
        snapshot.resume_url,
        snapshot.contact_preference,
        snapshot.public_fields,
    ) == (
        values.full_name,
        values.professional_title,
        values.short_biography,
        values.full_biography,
        values.location,
        values.availability,
        values.email,
        values.social_links,
        values.github_url,
        values.linkedin_url,
        values.personal_values,
        values.work_preferences,
        values.resume_url,
        values.contact_preference,
        values.public_fields,
    )


def _settings_matches(
    snapshot: WebsiteSettingsSnapshot,
    values: WebsiteSettingsValues,
) -> bool:
    return (
        snapshot.website_name,
        snapshot.default_title,
        snapshot.default_description,
        snapshot.default_locale,
        snapshot.timezone,
        snapshot.theme_policy,
        snapshot.primary_color,
        snapshot.accent_color,
        snapshot.contact_email,
        snapshot.contact_phone,
        snapshot.social_links,
        snapshot.seo_title_suffix,
        snapshot.seo_description,
        snapshot.analytics_provider,
        snapshot.analytics_public_id,
        snapshot.public_availability,
    ) == (
        values.website_name,
        values.default_title,
        values.default_description,
        values.default_locale,
        values.timezone,
        values.theme_policy,
        values.primary_color,
        values.accent_color,
        values.contact_email,
        values.contact_phone,
        values.social_links,
        values.seo_title_suffix,
        values.seo_description,
        values.analytics_provider,
        values.analytics_public_id,
        values.public_availability,
    )


def _navigation_matches(current: NavigationTree, target: NavigationTree) -> bool:
    return tuple(
        (
            item.id,
            item.parent_id,
            item.label,
            item.link_kind,
            item.href,
            item.target,
            item.visible,
            item.position,
        )
        for item in current.items
    ) == tuple(
        (
            item.id,
            item.parent_id,
            item.label,
            item.link_kind,
            item.href,
            item.target,
            item.visible,
            item.position,
        )
        for item in target.items
    )


def _footer_matches(current: FooterTree, target: FooterTree) -> bool:
    current_values = (
        current.copyright_text,
        tuple(
            (
                column.id,
                column.title,
                column.visible,
                column.position,
                tuple(
                    (
                        item.id,
                        item.label,
                        item.link_kind,
                        item.item_kind,
                        item.href,
                        item.target,
                        item.visible,
                        item.position,
                    )
                    for item in column.items
                ),
            )
            for column in current.columns
        ),
    )
    target_values = (
        target.copyright_text,
        tuple(
            (
                column.id,
                column.title,
                column.visible,
                column.position,
                tuple(
                    (
                        item.id,
                        item.label,
                        item.link_kind,
                        item.item_kind,
                        item.href,
                        item.target,
                        item.visible,
                        item.position,
                    )
                    for item in column.items
                ),
            )
            for column in target.columns
        ),
    )
    return current_values == target_values


def _skill_catalog(now: datetime) -> tuple[tuple[SkillCategory, ...], tuple[Skill, ...]]:
    categories = (
        SkillCategory(
            id=DEMO_ENGINEERING_CATEGORY_ID,
            name="Engineering",
            slug="engineering",
            description="Reliable systems shaped around clear contracts and humane operations.",
            position=0,
            created_at=now,
            updated_at=now,
            version=1,
        ),
        SkillCategory(
            id=DEMO_PRODUCT_CATEGORY_ID,
            name="Product craft",
            slug="product-craft",
            description="Interfaces that make complex work feel calm and understandable.",
            position=1,
            created_at=now,
            updated_at=now,
            version=1,
        ),
    )
    skills = (
        Skill(
            id=DEMO_PYTHON_SKILL_ID,
            name="Python",
            slug="python",
            category_id=DEMO_ENGINEERING_CATEGORY_ID,
            description="Typed application services, durable background work, and focused tests.",
            proficiency_label="Advanced",
            proficiency_score=92,
            years_experience=Decimal("8.50"),
            icon_key="python",
            position=0,
            featured=True,
            visible=True,
            created_at=now,
            updated_at=now,
            version=1,
        ),
        Skill(
            id=DEMO_API_DESIGN_SKILL_ID,
            name="API design",
            slug="api-design",
            category_id=DEMO_ENGINEERING_CATEGORY_ID,
            description="Versioned HTTP contracts with explicit failure and concurrency semantics.",
            proficiency_label="Advanced",
            proficiency_score=90,
            years_experience=Decimal("7.25"),
            icon_key="api",
            position=1,
            featured=False,
            visible=True,
            created_at=now,
            updated_at=now,
            version=1,
        ),
        Skill(
            id=DEMO_INTERNAL_TOOLING_SKILL_ID,
            name="Internal tooling",
            slug="internal-tooling",
            category_id=DEMO_ENGINEERING_CATEGORY_ID,
            description="A private draft used to demonstrate publication controls.",
            proficiency_label="Practiced",
            proficiency_score=81,
            years_experience=Decimal("5.00"),
            icon_key="tools",
            position=2,
            featured=False,
            visible=False,
            created_at=now,
            updated_at=now,
            version=1,
        ),
        Skill(
            id=DEMO_ACCESSIBILITY_SKILL_ID,
            name="Accessible interfaces",
            slug="accessible-interfaces",
            category_id=DEMO_PRODUCT_CATEGORY_ID,
            description=(
                "Keyboard-ready, semantic experiences tested with real assistive constraints."
            ),
            proficiency_label="Advanced",
            proficiency_score=89,
            years_experience=Decimal("6.75"),
            icon_key="accessibility",
            position=0,
            featured=True,
            visible=True,
            created_at=now,
            updated_at=now,
            version=1,
        ),
        Skill(
            id=DEMO_DESIGN_SYSTEMS_SKILL_ID,
            name="Design systems",
            slug="design-systems",
            category_id=DEMO_PRODUCT_CATEGORY_ID,
            description="Reusable foundations that align visual language, code, and content.",
            proficiency_label="Practiced",
            proficiency_score=84,
            years_experience=Decimal("5.50"),
            icon_key="components",
            position=1,
            featured=False,
            visible=True,
            created_at=now,
            updated_at=now,
            version=1,
        ),
    )
    return categories, skills


def _skill_catalog_matches(
    current_categories: tuple[SkillCategory, ...],
    current_skills: tuple[Skill, ...],
    target_categories: tuple[SkillCategory, ...],
    target_skills: tuple[Skill, ...],
) -> bool:
    def category_values(category: SkillCategory) -> tuple[object, ...]:
        return (
            category.id,
            category.name,
            category.slug,
            category.description,
            category.position,
        )

    def skill_values(skill: Skill) -> tuple[object, ...]:
        return (
            skill.id,
            skill.name,
            skill.slug,
            skill.category_id,
            skill.description,
            skill.proficiency_label,
            skill.proficiency_score,
            skill.years_experience,
            skill.icon_key,
            skill.position,
            skill.featured,
            skill.visible,
        )

    return tuple(map(category_values, current_categories)) == tuple(
        map(category_values, target_categories)
    ) and tuple(map(skill_values, current_skills)) == tuple(map(skill_values, target_skills))


async def _converge_skill_catalog(
    uow: _DemoSeedUnitOfWork,
    target_categories: tuple[SkillCategory, ...],
    target_skills: tuple[Skill, ...],
) -> bool:
    current_categories = await uow.categories.list_all(for_update=True)
    current_skill_values: list[Skill] = []
    for category in current_categories:
        current_skill_values.extend(await uow.skills.list_by_category(category.id, for_update=True))
    current_skills = tuple(current_skill_values)
    if _skill_catalog_matches(
        current_categories,
        current_skills,
        target_categories,
        target_skills,
    ):
        return False
    for skill in current_skills:
        await uow.skills.delete(skill)
    for category in current_categories:
        await uow.categories.delete(category)
    for category in target_categories:
        await uow.categories.add(category)
    for skill in target_skills:
        await uow.skills.add(skill)
    return True


async def seed_demo(session_factory: AsyncSessionFactory) -> DemoSeedResult:
    """Converge all implemented demo aggregates in one explicit transaction."""
    now = datetime.now(UTC)
    changed = 0
    profile_values = _profile_values()
    settings_values = _settings_values()
    target_categories, target_skills = _skill_catalog(now)
    async with _DemoSeedUnitOfWork(session_factory) as uow:
        profile_state = await uow.profile.get(for_update=True)
        profile_snapshot = uow.profile.snapshot(profile_state)
        if not _profile_matches(profile_snapshot, profile_values):
            uow.profile.replace(profile_state, profile_values, now=now)
            changed += 1

        settings_state = await uow.settings.get(for_update=True)
        settings_snapshot = uow.settings.snapshot(settings_state)
        if not _settings_matches(settings_snapshot, settings_values):
            uow.settings.replace(settings_state, settings_values, now=now)
            changed += 1

        current_navigation = await uow.navigation.get(for_update=True)
        target_navigation = _navigation(current_navigation)
        if not _navigation_matches(current_navigation, target_navigation):
            current_navigation = await uow.navigation.replace(
                target_navigation,
                expected_version=current_navigation.version,
                now=now,
            )
            changed += 1

        current_footer = await uow.footer.get(for_update=True)
        target_footer = _footer(current_footer)
        if not _footer_matches(current_footer, target_footer):
            current_footer = await uow.footer.replace(
                target_footer,
                expected_version=current_footer.version,
                now=now,
            )
            changed += 1

        if await _converge_skill_catalog(uow, target_categories, target_skills):
            changed += 1

        if changed:
            uow.audit.append(
                AuditEntry(
                    id=uuid7(),
                    event_type="demo.seeded",
                    actor_type=ActorType.SYSTEM,
                    actor_id=None,
                    actor_label_snapshot=None,
                    resource_type="demo_content",
                    resource_id=None,
                    request_id=DEMO_REQUEST_ID,
                    occurred_at=now,
                    outcome=AuditOutcome.SUCCESS,
                    ip_pseudonym=None,
                    metadata={"changed_aggregates": changed},
                    schema_version=1,
                )
            )
        await uow.commit()
        return DemoSeedResult(
            profile_id=profile_state.id,
            settings_id=settings_state.id,
            navigation_id=current_navigation.id,
            footer_id=current_footer.id,
            changed_aggregates=changed,
            navigation_items=len(target_navigation.items),
            footer_columns=len(target_footer.columns),
            footer_items=sum(len(column.items) for column in target_footer.columns),
            skill_categories=len(target_categories),
            skills=len(target_skills),
        )


async def _run() -> int:
    environment = os.environ.get("APP_ENVIRONMENT", Environment.DEVELOPMENT).casefold()
    if environment == Environment.PRODUCTION:
        sys.stderr.write("Demo seed refused: production environment is not writable.\n")
        return EXIT_PRODUCTION_REFUSED
    database_url = os.environ.get("APP_DATABASE_URL")
    if not database_url:
        sys.stderr.write("APP_DATABASE_URL is required.\n")
        return EXIT_INVALID_INPUT
    runtime = create_database_runtime(DatabaseConfig(url=SecretStr(database_url)))
    try:
        result = await seed_demo(runtime.session_factory)
    finally:
        await runtime.dispose()
    sys.stdout.write(
        "Demo seed complete: "
        f"changed={result.changed_aggregates} "
        f"profile={result.profile_id} settings={result.settings_id} "
        f"navigation={result.navigation_id} footer={result.footer_id} "
        f"navigation_items={result.navigation_items} "
        f"footer_columns={result.footer_columns} footer_items={result.footer_items}\n"
        f"skill_categories={result.skill_categories} skills={result.skills}\n"
    )
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    """Run the explicit demo seed; no startup path imports this command."""
    parser = argparse.ArgumentParser(description="Seed fictional local demo content.")
    parser.parse_args(arguments)
    try:
        return asyncio.run(_run())
    except (RuntimeError, ValueError):
        sys.stderr.write("Demo seed failed without applying partial content.\n")
        return EXIT_INVALID_INPUT


if __name__ == "__main__":  # pragma: no cover - exercised as an operator process.
    raise SystemExit(main())
