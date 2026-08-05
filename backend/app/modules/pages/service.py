"""Page commands, immutable publication, preview/export, and public projection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import TYPE_CHECKING, Any, cast

from app.common.application.idempotency import (
    IdempotencyDecision,
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.content_policy import parse_content
from app.common.domain.actors import ActorContext, ActorType
from app.common.domain.concurrency import require_matching_version
from app.common.domain.pagination import Page as CollectionPage
from app.common.domain.pagination import PageRequest, page_metadata
from app.common.domain.temporal import require_utc
from app.common.security.authorization import AccessPolicy, require_authorized
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.blog.service import BlogNotFoundError
from app.modules.experiences.service import ExperienceNotFoundError
from app.modules.identity.domain import uuid7
from app.modules.media.domain import (
    MediaOwnerType,
    MediaUsageRole,
    MediaUse,
    MediaUsePurpose,
)
from app.modules.pages.domain import (
    AdminPageView,
    Page,
    PageBlock,
    PageBlockValues,
    PageRevision,
    PageRevisionValues,
    PageRouteKind,
    PageSnapshot,
    PageValidationError,
    PublicPageRoute,
    derive_page_lifecycle,
    normalize_page_slug,
    page_canonical_path,
    validate_block_values,
    validate_revision_values,
    validate_route_identity,
)
from app.modules.pages.registry import (
    REGISTRY_MANIFEST,
    BlockType,
    ReferenceKind,
    ReferenceRole,
    StrictConfig,
    deserialize_config,
)
from app.modules.projects.service import ProjectNotFoundError
from app.modules.skills.service import SkillsNotFoundError

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.common.content_policy import SafeRenderedContent
    from app.modules.blog.domain import PostReferenceSummary
    from app.modules.experiences.domain import ExperienceReferenceSummary
    from app.modules.pages.ports import (
        BlogReferencePort,
        ExperienceReferencePort,
        PagesUnitOfWork,
        PagesUnitOfWorkFactory,
        ProfilePublicPort,
        ProjectReferencePort,
        SkillReferencePort,
    )
    from app.modules.profile.domain import PublicProfile
    from app.modules.projects.domain import ProjectReferenceSummary
    from app.modules.skills.domain import SkillReferenceSummary

_READ_POLICY = AccessPolicy(
    resource="pages",
    action="read",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
_WRITE_POLICY = AccessPolicy(
    resource="pages",
    action="write",
    allowed_actor_types=frozenset({ActorType.ADMINISTRATOR_SESSION}),
)
MAXIMUM_EXPORT_BYTES = 2_000_000
_PUBLICATION_REQUIREMENTS_UNMET = "publication_requirements_unmet"
_NOT_PUBLISHED = "not_published"
_HOME_CANNOT_BE_DELETED = "home_cannot_be_deleted"
_HOME_CANNOT_BE_DUPLICATED = "home_cannot_be_duplicated"
_AUTOMATIC_SELECTIONS: dict[BlockType, tuple[ReferenceKind, bool | None]] = {
    BlockType.SKILLS_GRID: (ReferenceKind.SKILL, None),
    BlockType.FEATURED_SKILLS: (ReferenceKind.SKILL, True),
    BlockType.EXPERIENCE_SUMMARY: (ReferenceKind.EXPERIENCE, None),
    BlockType.EXPERIENCE_LIST: (ReferenceKind.EXPERIENCE, None),
    BlockType.PROJECT_GRID: (ReferenceKind.PROJECT, None),
    BlockType.FEATURED_PROJECTS: (ReferenceKind.PROJECT, True),
    BlockType.LATEST_POSTS: (ReferenceKind.POST, None),
}


class PageNotFoundError(Exception):
    """A page or block is absent from the authorized scope."""


class PageRouteConflictError(Exception):
    """A Home identity or normalized custom slug is already reserved."""


class PagePublicationError(Exception):
    """A lifecycle action is invalid or public requirements are unmet."""

    def __init__(self, code: str, issues: tuple[PublicationIssue, ...] = ()) -> None:
        """Retain a stable lifecycle code and safe linked issues."""
        super().__init__("page publication rejected")
        self.code = code
        self.issues = issues


class PageReferenceError(Exception):
    """A normalized reference is absent, unusable, or capability-staged."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain a safe field path and stable provider-state code."""
        super().__init__("page reference rejected")
        self.path = path
        self.code = code


class PageIdempotencyRejectedError(Exception):
    """An idempotent page action conflicts or remains in progress."""

    def __init__(self, decision: IdempotencyDecision) -> None:
        """Retain only the shared admission decision."""
        super().__init__("page idempotency admission rejected")
        self.decision = decision


@dataclass(frozen=True, slots=True)
class PublicationIssue:
    """Safe linked issue for preview and publication validation."""

    block_id: UUID
    path: str
    code: str


@dataclass(frozen=True, slots=True)
class ResolvedReference:
    """Public-safe generic provider projection for one normalized target."""

    kind: ReferenceKind
    target_id: UUID
    label: str
    href: str | None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class PublicPageBlock:
    """Validated renderer-ready block plus public-safe reference values."""

    block: PageBlock
    config: StrictConfig
    references: tuple[ResolvedReference, ...]
    profile: PublicProfile | None = None
    rendered: SafeRenderedContent | None = None


@dataclass(frozen=True, slots=True)
class PublicPage:
    """One effective public page with a single frozen revision."""

    id: UUID
    route_kind: PageRouteKind
    slug: str | None
    title: str
    description: str
    seo_title: str
    seo_description: str
    canonical_path: str
    canonical_url: str | None
    published_at: datetime
    blocks: tuple[PublicPageBlock, ...]


@dataclass(frozen=True, slots=True)
class PagePreview:
    """Private draft through the canonical registry path."""

    snapshot: PageSnapshot
    blocks: tuple[PublicPageBlock, ...]
    issues: tuple[PublicationIssue, ...]
    banner: str = "Draft preview - not public"
    noindex: bool = True


@dataclass(frozen=True, slots=True)
class PageExport:
    """Bounded canonical non-persisting JSON export."""

    page_id: UUID
    manifest: dict[str, Any]
    checksum: str
    filename: str


@dataclass(frozen=True, slots=True)
class CreatePageCommand:
    """Idempotent creation of Home or one custom page draft."""

    actor: ActorContext
    request_id: str
    idempotency_key: str
    canonical_payload: bytes
    route_kind: PageRouteKind
    slug: str | None
    values: PageRevisionValues
    visible: bool = True
    navigation_visible: bool = False


@dataclass(frozen=True, slots=True)
class SavePageCommand:
    """Complete optimistic replacement of mutable page metadata."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None
    route_kind: PageRouteKind
    slug: str | None
    values: PageRevisionValues
    visible: bool
    navigation_visible: bool


@dataclass(frozen=True, slots=True)
class DuplicatePageCommand:
    """Idempotent deep copy of one custom page to a new route."""

    actor: ActorContext
    request_id: str
    source_page_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    slug: str
    title: str | None = None


@dataclass(frozen=True, slots=True)
class AddBlockCommand:
    """Idempotent insertion of one typed draft block."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    values: PageBlockValues
    position: int | None = None


@dataclass(frozen=True, slots=True)
class UpdateBlockCommand:
    """Optimistic replacement of one typed draft block."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    block_id: UUID
    if_match: str | None
    values: PageBlockValues


@dataclass(frozen=True, slots=True)
class BlockActionCommand:
    """Optimistic identifier-only block action."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    block_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class DuplicateBlockCommand:
    """Idempotent adjacent deep copy of one draft block."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    block_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes


@dataclass(frozen=True, slots=True)
class ReorderBlocksCommand:
    """Idempotent complete-list block reorder."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    ordered_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class PublishPageCommand:
    """Idempotent publication now or at an absolute UTC instant."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ReschedulePageCommand:
    """Idempotent schedule-metadata-only mutation."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes
    publish_at: datetime


@dataclass(frozen=True, slots=True)
class PageMutationCommand:
    """Optimistic page lifecycle mutation."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None


@dataclass(frozen=True, slots=True)
class UnpublishPageCommand:
    """Idempotent immediate removal of public eligibility."""

    actor: ActorContext
    request_id: str
    page_id: UUID
    if_match: str | None
    idempotency_key: str
    canonical_payload: bytes


class PageService:
    """Authorize, validate, and transact the configurable-page slice."""

    def __init__(  # noqa: PLR0913 - provider ports are the composition contract.
        self,
        uow_factory: PagesUnitOfWorkFactory,
        skills: SkillReferencePort,
        experiences: ExperienceReferencePort,
        projects: ProjectReferencePort,
        posts: BlogReferencePort,
        profile: ProfilePublicPort,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Bind transaction, provider, time, and identifier seams."""
        self._uow_factory = uow_factory
        self._skills = skills
        self._experiences = experiences
        self._projects = projects
        self._posts = posts
        self._profile = profile
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    async def admin_list(
        self, actor: ActorContext, request: PageRequest
    ) -> CollectionPage[AdminPageView]:
        """Return retained pages with database-time lifecycle labels."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            now = await uow.pages.database_now()
            snapshots, total = await uow.pages.list_pages(
                offset=request.offset, limit=request.page_size
            )
            items = tuple(
                AdminPageView(snapshot, derive_page_lifecycle(snapshot, database_now=now))
                for snapshot in snapshots
            )
            return CollectionPage(items, page_metadata(request, total_items=total))

    async def admin_get(self, actor: ActorContext, page_id: UUID) -> AdminPageView:
        """Return one authorized page aggregate."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, page_id)
            return AdminPageView(
                snapshot,
                derive_page_lifecycle(snapshot, database_now=await uow.pages.database_now()),
            )

    async def create(self, command: CreatePageCommand) -> PageSnapshot:
        """Create one stable route and an empty initial draft."""
        require_authorized(command.actor, _WRITE_POLICY)
        route_kind, slug, values = self._validated_identity_and_values(
            command.route_kind, command.slug, command.values
        )
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            if await uow.pages.route_exists(route_kind, slug):
                raise PageRouteConflictError
            page_id, revision_id = self._id_factory(), self._id_factory()
            page = Page(
                id=page_id,
                route_kind=route_kind,
                slug=slug,
                visible=command.visible,
                navigation_visible=command.navigation_visible,
                position=await uow.pages.next_position(),
                draft_revision_id=revision_id,
                published_revision_id=None,
                publish_at=None,
                unpublished_at=None,
                created_at=now,
                updated_at=now,
                version=1,
            )
            revision = PageRevision(
                id=revision_id,
                page_id=page_id,
                revision_number=1,
                based_on_revision_id=None,
                values=values,
                blocks=(),
                frozen=False,
                created_by=self._actor_id(command.actor),
                created_at=now,
                updated_at=now,
            )
            await uow.pages.add_page(page, revision)
            snapshot = PageSnapshot(page, revision, None)
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.created",
                page_id,
                1,
                ("route", "metadata"),
            )
            await self._complete(uow, decision, snapshot, "page.created", 201)
            await uow.commit()
            return snapshot

    async def save(self, command: SavePageCommand) -> PageSnapshot:
        """Save page metadata without mutating live content."""
        require_authorized(command.actor, _WRITE_POLICY)
        route_kind, slug, values = self._validated_identity_and_values(
            command.route_kind, command.slug, command.values
        )
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            if (
                snapshot.page.route_kind is PageRouteKind.HOME
                and route_kind is not PageRouteKind.HOME
            ):
                raise PageValidationError(path="route_kind", code="home_route_immutable")
            if await uow.pages.route_exists(route_kind, slug, excluding_id=command.page_id):
                raise PageRouteConflictError
            await self._validate_references(uow, snapshot.draft.blocks, for_publication=False)
            now = self._clock()
            updated = await uow.pages.save_draft(
                snapshot,
                values=values,
                route_kind=route_kind,
                slug=slug,
                visible=command.visible,
                navigation_visible=command.navigation_visible,
                now=now,
            )
            if updated.published is not None:
                await self._replace_revision_media(
                    uow,
                    updated.published,
                    now=now,
                    public=command.visible,
                )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.saved",
                updated.page.id,
                updated.page.version,
                ("route", "metadata", "visibility"),
            )
            await uow.commit()
            return updated

    async def duplicate(self, command: DuplicatePageCommand) -> PageSnapshot:
        """Deep-copy one custom draft with fresh aggregate and child IDs."""
        require_authorized(command.actor, _WRITE_POLICY)
        slug = normalize_page_slug(command.slug)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/duplicate",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            source = await self._get(uow, command.source_page_id, for_update=True)
            require_matching_version(command.if_match, current_version=source.page.version)
            if source.page.route_kind is PageRouteKind.HOME:
                raise PagePublicationError(_HOME_CANNOT_BE_DUPLICATED)
            if await uow.pages.route_exists(PageRouteKind.CUSTOM, slug):
                raise PageRouteConflictError
            page_id, revision_id = self._id_factory(), self._id_factory()
            blocks = tuple(
                PageBlock(
                    id=self._id_factory(),
                    revision_id=revision_id,
                    position=block.position,
                    values=block.values,
                    references=block.references,
                    created_at=now,
                    updated_at=now,
                )
                for block in source.draft.blocks
            )
            values = validate_revision_values(
                PageRevisionValues(
                    title=command.title or f"{source.draft.values.title} copy",
                    description=source.draft.values.description,
                    seo_title=source.draft.values.seo_title,
                    seo_description=source.draft.values.seo_description,
                    canonical_url=None,
                )
            )
            page = Page(
                id=page_id,
                route_kind=PageRouteKind.CUSTOM,
                slug=slug,
                visible=False,
                navigation_visible=False,
                position=await uow.pages.next_position(),
                draft_revision_id=revision_id,
                published_revision_id=None,
                publish_at=None,
                unpublished_at=None,
                created_at=now,
                updated_at=now,
                version=1,
            )
            revision = PageRevision(
                id=revision_id,
                page_id=page_id,
                revision_number=1,
                based_on_revision_id=None,
                values=values,
                blocks=blocks,
                frozen=False,
                created_by=self._actor_id(command.actor),
                created_at=now,
                updated_at=now,
            )
            for block in blocks:
                await self._replace_block_media(uow, block, now=now, public=False)
            await uow.pages.add_page(page, revision)
            duplicate = PageSnapshot(page, revision, None)
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.duplicated",
                page.id,
                page.version,
                ("source_page", "route", "blocks"),
            )
            await self._complete(uow, decision, duplicate, "page.duplicated", 201)
            await uow.commit()
            return duplicate

    async def add_block(self, command: AddBlockCommand) -> PageSnapshot:
        """Insert one strict current-version block."""
        require_authorized(command.actor, _WRITE_POLICY)
        values, references = validate_block_values(command.values)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/blocks",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            block = PageBlock(
                id=self._id_factory(),
                revision_id=snapshot.draft.id,
                position=len(snapshot.draft.blocks),
                values=values,
                references=references,
                created_at=now,
                updated_at=now,
            )
            await self._validate_references(uow, (block,), for_publication=False)
            await self._replace_block_media(uow, block, now=now, public=False)
            updated = await uow.pages.add_block(
                snapshot,
                block,
                position=len(snapshot.draft.blocks)
                if command.position is None
                else command.position,
                now=now,
            )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.block_added",
                updated.page.id,
                updated.page.version,
                ("block_type",),
            )
            await self._complete(uow, decision, updated, "page.block_added", 201)
            await uow.commit()
            return updated

    async def update_block(self, command: UpdateBlockCommand) -> PageSnapshot:
        """Replace one draft block and regenerate normalized references."""
        require_authorized(command.actor, _WRITE_POLICY)
        values, references = validate_block_values(command.values)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            self._block(snapshot, command.block_id)
            candidate = PageBlock(
                command.block_id,
                snapshot.draft.id,
                0,
                values,
                references,
                now,
                now,
            )
            await self._validate_references(uow, (candidate,), for_publication=False)
            await self._replace_block_media(uow, candidate, now=now, public=False)
            updated = await uow.pages.update_block(
                snapshot, command.block_id, values, references, now=now
            )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.block_updated",
                updated.page.id,
                updated.page.version,
                ("block",),
            )
            await uow.commit()
            return updated

    async def duplicate_block(self, command: DuplicateBlockCommand) -> PageSnapshot:
        """Create one independent adjacent block copy."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/blocks/{block_id}/duplicate",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            self._block(snapshot, command.block_id)
            updated = await uow.pages.duplicate_block(snapshot, command.block_id, now=now)
            previous_ids = {item.id for item in snapshot.draft.blocks}
            duplicate = next(item for item in updated.draft.blocks if item.id not in previous_ids)
            await self._replace_block_media(uow, duplicate, now=now, public=False)
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.block_duplicated",
                updated.page.id,
                updated.page.version,
                ("block",),
            )
            await self._complete(uow, decision, updated, "page.block_duplicated", 200)
            await uow.commit()
            return updated

    async def set_block_visibility(
        self, command: BlockActionCommand, *, visible: bool
    ) -> PageSnapshot:
        """Hide or show one draft block."""
        return await self._simple_block_action(command, action="show" if visible else "hide")

    async def delete_block(self, command: BlockActionCommand) -> PageSnapshot:
        """Delete one mutable block and reindex atomically."""
        return await self._simple_block_action(command, action="delete")

    async def reorder_blocks(self, command: ReorderBlocksCommand) -> PageSnapshot:
        """Replace the complete draft block order."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/blocks/reorder",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            self._require_complete_order(
                command.ordered_ids, tuple(item.id for item in snapshot.draft.blocks)
            )
            updated = await uow.pages.reorder_blocks(snapshot, command.ordered_ids, now=now)
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.blocks_reordered",
                updated.page.id,
                updated.page.version,
                ("order",),
            )
            await self._complete(uow, decision, updated, "page.blocks_reordered", 200)
            await uow.commit()
            return updated

    async def preview(self, actor: ActorContext, page_id: UUID) -> PagePreview:
        """Resolve the draft through the canonical registry path."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, page_id)
            blocks, issues = await self._project_blocks(uow, snapshot, snapshot.draft, preview=True)
            return PagePreview(snapshot, blocks, issues)

    async def export(self, actor: ActorContext, page_id: UUID) -> PageExport:
        """Return a bounded canonical read-only manifest."""
        require_authorized(actor, _READ_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, page_id)
        manifest = self._export_manifest(snapshot)
        encoded = json.dumps(
            manifest, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode()
        if len(encoded) > MAXIMUM_EXPORT_BYTES:
            raise PageValidationError(path="export", code="export_too_large")
        checksum = sha256(encoded).hexdigest()
        return PageExport(page_id, manifest, checksum, f"page-{page_id}.json")

    async def publish(self, command: PublishPageCommand) -> PageSnapshot:
        """Freeze one revision and deep-copy the next draft."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/publish",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            issues = await self._validate_references(
                uow, snapshot.draft.blocks, for_publication=True
            )
            if issues:
                raise PagePublicationError(_PUBLICATION_REQUIREMENTS_UNMET, issues)
            database_now = await uow.pages.database_now()
            publish_at = command.publish_at or database_now
            require_utc(publish_at)
            updated = await uow.pages.publish(
                snapshot,
                publish_at=publish_at,
                next_revision_id=self._id_factory(),
                actor_id=self._actor_id(command.actor),
                now=now,
            )
            if snapshot.published is not None and snapshot.published.id != snapshot.draft.id:
                await self._replace_revision_media(
                    uow,
                    snapshot.published,
                    now=now,
                    public=False,
                    active=False,
                )
            if updated.published is None:
                raise PagePublicationError(_NOT_PUBLISHED)
            await self._replace_revision_media(
                uow,
                updated.published,
                now=now,
                public=updated.page.visible,
            )
            await self._replace_revision_media(
                uow,
                updated.draft,
                now=now,
                public=False,
            )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.published",
                updated.page.id,
                updated.page.version,
                ("publication",),
            )
            await self._complete(uow, decision, updated, "page.published", 200)
            await uow.commit()
            return updated

    async def reschedule(self, command: ReschedulePageCommand) -> PageSnapshot:
        """Change only the effective publication instant."""
        require_authorized(command.actor, _WRITE_POLICY)
        require_utc(command.publish_at)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/reschedule",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            updated = await uow.pages.reschedule(snapshot, publish_at=command.publish_at, now=now)
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.rescheduled",
                updated.page.id,
                updated.page.version,
                ("publish_at",),
            )
            await self._complete(uow, decision, updated, "page.rescheduled", 200)
            await uow.commit()
            return updated

    async def unpublish(self, command: UnpublishPageCommand) -> PageSnapshot:
        """Immediately remove public eligibility while retaining history."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            decision = await self._acquire(
                uow,
                command.actor,
                "/api/v1/admin/pages/{page_id}/unpublish",
                command.idempotency_key,
                command.canonical_payload,
                now,
            )
            replay = await self._replayed(uow, decision)
            if replay is not None:
                return replay
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            if snapshot.page.published_revision_id is None:
                raise PagePublicationError(_NOT_PUBLISHED)
            updated = await uow.pages.unpublish(snapshot, now=now)
            if snapshot.published is not None:
                await self._replace_revision_media(
                    uow,
                    snapshot.published,
                    now=now,
                    public=False,
                    active=False,
                )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.unpublished",
                updated.page.id,
                updated.page.version,
                ("publication",),
            )
            await self._complete(uow, decision, updated, "page.unpublished", 200)
            await uow.commit()
            return updated

    async def delete(self, command: PageMutationCommand) -> PageSnapshot:
        """Soft-delete one custom page while reserving its slug."""
        require_authorized(command.actor, _WRITE_POLICY)
        now = self._clock()
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            if snapshot.page.route_kind is PageRouteKind.HOME:
                raise PagePublicationError(_HOME_CANNOT_BE_DELETED)
            updated = await uow.pages.soft_delete(snapshot, now=now)
            await self._replace_revision_media(
                uow,
                snapshot.draft,
                now=now,
                public=False,
                active=False,
            )
            if snapshot.published is not None and snapshot.published.id != snapshot.draft.id:
                await self._replace_revision_media(
                    uow,
                    snapshot.published,
                    now=now,
                    public=False,
                    active=False,
                )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                "page.deleted",
                updated.page.id,
                updated.page.version,
                ("deleted",),
            )
            await uow.commit()
            return updated

    async def public_home(self) -> PublicPage:
        """Return only the effective frozen Home projection."""
        async with self._uow_factory() as uow:
            snapshot = await uow.pages.get_public_home()
            if snapshot is None:
                raise PageNotFoundError
            return await self._public(uow, snapshot)

    async def public_routes(self, request: PageRequest) -> CollectionPage[PublicPageRoute]:
        """Return bounded effective route facts for sitemap/discovery consumers."""
        async with self._uow_factory() as uow:
            targets, total = await uow.pages.list_public_routes(
                offset=request.offset, limit=request.page_size
            )
        items = tuple(
            PublicPageRoute(
                id=target.id,
                canonical_path=target.canonical_path,
                title=target.title,
                published_at=target.publish_at,
                updated_at=target.updated_at,
            )
            for target in targets
            if target.title is not None and target.publish_at is not None
        )
        return CollectionPage(items, page_metadata(request, total_items=total))

    async def public_custom(self, slug: str) -> PublicPage:
        """Return only an effective normalized custom-page projection."""
        normalized = normalize_page_slug(slug)
        async with self._uow_factory() as uow:
            snapshot = await uow.pages.get_public_custom(normalized)
            if snapshot is None:
                raise PageNotFoundError
            return await self._public(uow, snapshot)

    async def _simple_block_action(
        self, command: BlockActionCommand, *, action: str
    ) -> PageSnapshot:
        require_authorized(command.actor, _WRITE_POLICY)
        async with self._uow_factory() as uow:
            snapshot = await self._get(uow, command.page_id, for_update=True)
            require_matching_version(command.if_match, current_version=snapshot.page.version)
            self._block(snapshot, command.block_id)
            now = self._clock()
            if action in {"hide", "show"}:
                updated = await uow.pages.set_block_visibility(
                    snapshot, command.block_id, visible=action == "show", now=now
                )
            elif action == "delete":
                updated = await uow.pages.delete_block(snapshot, command.block_id, now=now)
            else:
                raise PageNotFoundError
            if action == "delete":
                original = self._block(snapshot, command.block_id)
                await self._replace_block_media(
                    uow,
                    original,
                    now=now,
                    public=False,
                    active=False,
                )
            else:
                changed = self._block(updated, command.block_id)
                await self._replace_block_media(
                    uow,
                    changed,
                    now=now,
                    public=False,
                    active=action == "show",
                )
            self._audit(
                uow,
                command.actor,
                command.request_id,
                {
                    "hide": "page.block_hidden",
                    "show": "page.block_shown",
                    "delete": "page.block_deleted",
                }[action],
                updated.page.id,
                updated.page.version,
                ("block",),
            )
            await uow.commit()
            return updated

    async def _public(self, uow: PagesUnitOfWork, snapshot: PageSnapshot) -> PublicPage:
        revision = snapshot.published
        if revision is None or snapshot.page.publish_at is None:
            raise PageNotFoundError
        blocks, issues = await self._project_blocks(uow, snapshot, revision, preview=False)
        del issues
        return PublicPage(
            id=snapshot.page.id,
            route_kind=snapshot.page.route_kind,
            slug=snapshot.page.slug,
            title=revision.values.title,
            description=revision.values.description,
            seo_title=revision.values.seo_title or revision.values.title,
            seo_description=revision.values.seo_description or revision.values.description,
            canonical_path=page_canonical_path(snapshot.page),
            canonical_url=revision.values.canonical_url,
            published_at=snapshot.page.publish_at,
            blocks=blocks,
        )

    async def _project_blocks(
        self, uow: PagesUnitOfWork, snapshot: PageSnapshot, revision: PageRevision, *, preview: bool
    ) -> tuple[tuple[PublicPageBlock, ...], tuple[PublicationIssue, ...]]:
        candidates = (
            revision.blocks
            if preview
            else tuple(block for block in revision.blocks if block.values.visible)
        )
        issues = await self._validate_references(uow, candidates, for_publication=not preview)
        resolved = await self._resolved_references(uow, snapshot, candidates)
        profile = (
            await self._profile.public_get()
            if any(
                block.values.block_type in {BlockType.HERO, BlockType.PROFILE_SUMMARY}
                for block in candidates
            )
            else None
        )
        blocks: list[PublicPageBlock] = []
        for block in candidates:
            try:
                config = deserialize_config(
                    block.values.block_type, block.values.schema_version, block.values.config
                )
            except Exception:  # noqa: BLE001 - corrupted stored data fails closed.
                issues += (PublicationIssue(block.id, "config", "unsupported_or_invalid_config"),)
                continue
            include_profile = block.values.block_type is BlockType.PROFILE_SUMMARY or (
                block.values.block_type is BlockType.HERO
                and bool(getattr(config, "include_profile_evidence", False))
            )
            block_profile = (
                profile if include_profile and self._profile_available(profile) else None
            )
            rendered = (
                parse_content(cast("Any", config).source).rendered
                if block.values.block_type is BlockType.RICH_TEXT
                else None
            )
            if include_profile and block_profile is None:
                issues += (
                    PublicationIssue(block.id, "config.profile", "required_profile_unavailable"),
                )
            if not preview and any(
                issue.block_id == block.id and issue.code.startswith("required_")
                for issue in issues
            ):
                continue
            blocks.append(
                PublicPageBlock(
                    block,
                    config,
                    resolved.get(block.id, ()),
                    block_profile,
                    rendered,
                )
            )
        return tuple(blocks), issues

    @staticmethod
    def _profile_available(profile: PublicProfile | None) -> bool:
        if profile is None:
            return False
        return any(
            value is not None
            for value in (
                profile.full_name,
                profile.professional_title,
                profile.short_biography,
                profile.full_biography,
                profile.location,
                profile.availability,
                profile.email,
                profile.social_links,
                profile.github_url,
                profile.linkedin_url,
                profile.personal_values,
                profile.work_preferences,
                profile.resume_url,
                profile.contact_preference,
            )
        )

    @classmethod
    async def _replace_revision_media(
        cls,
        uow: PagesUnitOfWork,
        revision: PageRevision,
        *,
        now: datetime,
        public: bool,
        active: bool = True,
    ) -> None:
        """Materialize every page-block media use for one revision state."""
        for block in revision.blocks:
            await cls._replace_block_media(
                uow,
                block,
                now=now,
                public=public and block.values.visible,
                active=active and block.values.visible,
            )

    @staticmethod
    async def _replace_block_media(
        uow: PagesUnitOfWork,
        block: PageBlock,
        *,
        now: datetime,
        public: bool,
        active: bool = True,
    ) -> None:
        """Replace the exact contextual media use owned by one page block."""
        media_references = tuple(
            reference
            for reference in block.references
            if reference.kind is ReferenceKind.MEDIA
            and reference.role is ReferenceRole.MEDIA_PRIMARY
        )
        uses: tuple[MediaUse, ...] = ()
        if media_references:
            reference = media_references[0]
            config = block.values.config
            alt_text = config.get("alt")
            caption = config.get("caption")
            focal_point = config.get("focal_point", "center")
            if not isinstance(alt_text, str):
                raise PageValidationError(path="config.alt", code="invalid_text")
            focal_coordinates = {
                "center": (50, 50),
                "top": (50, 0),
                "bottom": (50, 100),
                "left": (0, 50),
                "right": (100, 50),
            }
            focal_x, focal_y = (
                focal_coordinates.get(focal_point, (50, 50))
                if isinstance(focal_point, str)
                else (50, 50)
            )
            uses = (
                MediaUse(
                    asset_id=reference.target_id,
                    owner_type=MediaOwnerType.PAGE_BLOCK,
                    owner_id=block.id,
                    role=MediaUsageRole.PAGE_PRIMARY,
                    position=0,
                    purpose=MediaUsePurpose.MEANINGFUL,
                    alt_text=alt_text,
                    caption=caption if isinstance(caption, str) else None,
                    focal_x=focal_x,
                    focal_y=focal_y,
                    active=active,
                    public=public,
                ),
            )
        await uow.media.replace_owner_usages(
            owner_type=MediaOwnerType.PAGE_BLOCK.value,
            owner_id=block.id,
            usages=uses,
            now=now,
        )

    async def _validate_references(
        self, uow: PagesUnitOfWork, blocks: tuple[PageBlock, ...], *, for_publication: bool
    ) -> tuple[PublicationIssue, ...]:
        visible_blocks = tuple(
            block for block in blocks if block.values.visible or not for_publication
        )
        by_kind = self._group_references(visible_blocks)
        issues: list[PublicationIssue] = []
        summaries = await self._provider_summaries(by_kind)
        page_targets = {
            item.id: item
            for item in await uow.pages.reference_targets(by_kind.get(ReferenceKind.PAGE, ()))
        }
        database_now = (
            await uow.pages.database_now()
            if for_publication and by_kind.get(ReferenceKind.PAGE)
            else None
        )
        for block in visible_blocks:
            for reference in block.references:
                path = f"blocks.{block.id}.references.{reference.position}"
                if reference.kind is ReferenceKind.MEDIA:
                    # Owner materialization validates existence/readiness transactionally.
                    continue
                if reference.kind is ReferenceKind.PAGE:
                    target = page_targets.get(reference.target_id)
                    if target is None or target.deleted:
                        raise PageReferenceError(path=path, code="page_not_found")
                    if (
                        for_publication
                        and reference.required
                        and (
                            database_now is None
                            or not target.visible
                            or target.publish_at is None
                            or target.publish_at > database_now
                            or target.title is None
                        )
                    ):
                        issues.append(PublicationIssue(block.id, path, "required_page_unavailable"))
                    continue
                summary = summaries.get((reference.kind, reference.target_id))
                if summary is None:
                    raise PageReferenceError(path=path, code=f"{reference.kind.value}_not_found")
                if for_publication and reference.required and not self._summary_public(summary):
                    issues.append(
                        PublicationIssue(
                            block.id, path, f"required_{reference.kind.value}_unavailable"
                        )
                    )
        return tuple(issues)

    async def _resolved_references(
        self, uow: PagesUnitOfWork, snapshot: PageSnapshot, blocks: tuple[PageBlock, ...]
    ) -> dict[UUID, tuple[ResolvedReference, ...]]:
        summaries = await self._provider_summaries(self._group_references(blocks))
        automatic = await self._automatic_provider_summaries(blocks)
        grouped = self._group_references(blocks)
        page_targets = {
            item.id: item
            for item in await uow.pages.reference_targets(grouped.get(ReferenceKind.PAGE, ()))
        }
        result: dict[UUID, tuple[ResolvedReference, ...]] = {}
        now = await uow.pages.database_now()
        for block in blocks:
            projected: list[ResolvedReference] = []
            for reference in block.references:
                if reference.kind is ReferenceKind.MEDIA:
                    continue
                if reference.kind is ReferenceKind.PAGE:
                    target = page_targets.get(reference.target_id)
                    if (
                        target is not None
                        and not target.deleted
                        and target.visible
                        and target.publish_at is not None
                        and target.publish_at <= now
                        and target.title is not None
                    ):
                        projected.append(
                            ResolvedReference(
                                reference.kind,
                                target.id,
                                target.title,
                                target.canonical_path,
                            )
                        )
                    continue
                summary = summaries.get((reference.kind, reference.target_id))
                resolved = self._summary_projection(reference.kind, summary)
                if resolved is not None:
                    projected.append(resolved)
            selection = _AUTOMATIC_SELECTIONS.get(block.values.block_type)
            if selection is not None and not any(
                reference.kind is selection[0] for reference in block.references
            ):
                maximum = self._maximum_items(block)
                for summary in automatic.get(selection, ())[:maximum]:
                    resolved = self._summary_projection(selection[0], summary)
                    if resolved is not None:
                        projected.append(resolved)
            result[block.id] = tuple(projected)
        del snapshot
        return result

    async def _automatic_provider_summaries(
        self, blocks: tuple[PageBlock, ...]
    ) -> dict[tuple[ReferenceKind, bool | None], tuple[object, ...]]:
        requirements: dict[tuple[ReferenceKind, bool | None], int] = {}
        for block in blocks:
            selection = _AUTOMATIC_SELECTIONS.get(block.values.block_type)
            if selection is None or any(
                reference.kind is selection[0] for reference in block.references
            ):
                continue
            maximum = self._maximum_items(block)
            requirements[selection] = max(requirements.get(selection, 0), maximum)
        resolvers = {
            ReferenceKind.SKILL: self._skills.list_public,
            ReferenceKind.EXPERIENCE: self._experiences.list_public,
            ReferenceKind.PROJECT: self._projects.list_public,
            ReferenceKind.POST: self._posts.list_public,
        }
        result: dict[tuple[ReferenceKind, bool | None], tuple[object, ...]] = {}
        for selection, maximum in requirements.items():
            kind, featured = selection
            if maximum > 0:
                result[selection] = tuple(await resolvers[kind](maximum, featured=featured))
        return result

    @staticmethod
    def _maximum_items(block: PageBlock) -> int:
        value = block.values.config.get("maximum_items", 0)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    async def _provider_summaries(
        self, grouped: dict[ReferenceKind, tuple[UUID, ...]]
    ) -> dict[tuple[ReferenceKind, UUID], object]:
        result: dict[tuple[ReferenceKind, UUID], object] = {}
        calls = (
            (ReferenceKind.SKILL, self._skills.resolve),
            (ReferenceKind.EXPERIENCE, self._experiences.resolve),
            (ReferenceKind.PROJECT, self._projects.resolve),
            (ReferenceKind.POST, self._posts.resolve),
        )
        for kind, resolver in calls:
            ids = grouped.get(kind, ())
            if ids:
                try:
                    resolved = await resolver(ids)
                except (
                    SkillsNotFoundError,
                    ExperienceNotFoundError,
                    ProjectNotFoundError,
                    BlogNotFoundError,
                ) as error:
                    raise PageReferenceError(
                        path="references", code=f"{kind.value}_not_found"
                    ) from error
                for summary in resolved:
                    result[(kind, summary.id)] = summary
        return result

    @staticmethod
    def _group_references(blocks: tuple[PageBlock, ...]) -> dict[ReferenceKind, tuple[UUID, ...]]:
        return {
            kind: tuple(
                dict.fromkeys(
                    reference.target_id
                    for block in blocks
                    for reference in block.references
                    if reference.kind is kind
                )
            )
            for kind in ReferenceKind
        }

    @staticmethod
    def _summary_public(summary: object) -> bool:
        public = getattr(summary, "public", None)
        return bool(public is not None or getattr(summary, "visible", False))

    @staticmethod
    def _summary_projection(  # noqa: PLR0911 - closed provider kinds are explicit.
        kind: ReferenceKind, summary: object | None
    ) -> ResolvedReference | None:
        if summary is None or not PageService._summary_public(summary):
            return None
        if kind is ReferenceKind.SKILL:
            skill = cast("SkillReferenceSummary", summary)
            return ResolvedReference(kind, skill.id, skill.name, f"/skills#{skill.slug}")
        if kind is ReferenceKind.EXPERIENCE:
            experience = cast("ExperienceReferenceSummary", summary)
            public_experience = experience.public
            if public_experience is None:
                return None
            return ResolvedReference(
                kind,
                experience.id,
                f"{public_experience.role_title} at {public_experience.company_name}",
                "/experience",
            )
        if kind is ReferenceKind.PROJECT:
            project = cast("ProjectReferenceSummary", summary)
            public_project = project.public
            if public_project is None:
                return None
            return ResolvedReference(
                kind,
                project.id,
                public_project.name,
                f"/projects/{public_project.slug}",
            )
        if kind is ReferenceKind.POST:
            post = cast("PostReferenceSummary", summary)
            public_post = post.public
            if public_post is None:
                return None
            return ResolvedReference(
                kind,
                post.id,
                public_post.title,
                f"/blog/{public_post.slug}",
                public_post.excerpt,
            )
        return None

    @staticmethod
    def _validated_identity_and_values(
        route_kind: PageRouteKind, slug: str | None, values: PageRevisionValues
    ) -> tuple[PageRouteKind, str | None, PageRevisionValues]:
        return (
            route_kind,
            validate_route_identity(route_kind, slug),
            validate_revision_values(values),
        )

    @staticmethod
    async def _get(
        uow: PagesUnitOfWork, page_id: UUID, *, for_update: bool = False
    ) -> PageSnapshot:
        snapshot = await uow.pages.get_page(page_id, for_update=for_update)
        if snapshot is None or snapshot.page.deleted_at is not None:
            raise PageNotFoundError
        return snapshot

    @staticmethod
    def _block(snapshot: PageSnapshot, block_id: UUID) -> PageBlock:
        block = next((item for item in snapshot.draft.blocks if item.id == block_id), None)
        if block is None:
            raise PageNotFoundError
        return block

    @staticmethod
    def _require_complete_order(proposed: tuple[UUID, ...], current: tuple[UUID, ...]) -> None:
        if len(proposed) != len(set(proposed)):
            raise PageValidationError(path="ordered_ids", code="duplicate_id")
        if set(proposed) != set(current):
            raise PageValidationError(path="ordered_ids", code="incomplete_order")

    @staticmethod
    def _actor_id(actor: ActorContext) -> UUID:
        if actor.actor_id is None:
            raise PageNotFoundError
        return actor.actor_id

    @staticmethod
    async def _acquire(  # noqa: PLR0913 - admission inputs are explicit.
        uow: PagesUnitOfWork,
        actor: ActorContext,
        route: str,
        key: str,
        payload: bytes,
        now: datetime,
    ) -> IdempotencyDecision:
        decision = await uow.idempotency.acquire(
            IdempotencyRequest.create(
                actor=actor, route=route, key=key, canonical_payload=payload, requested_at=now
            )
        )
        if decision.decision not in {
            IdempotencyDecisionType.ACQUIRED,
            IdempotencyDecisionType.REPLAY,
        }:
            raise PageIdempotencyRejectedError(decision)
        return decision

    async def _replayed(
        self, uow: PagesUnitOfWork, decision: IdempotencyDecision
    ) -> PageSnapshot | None:
        if decision.decision is not IdempotencyDecisionType.REPLAY:
            return None
        if decision.outcome is None or decision.outcome.resource_id is None:
            raise PageNotFoundError
        return await self._get(uow, decision.outcome.resource_id)

    @staticmethod
    async def _complete(
        uow: PagesUnitOfWork,
        decision: IdempotencyDecision,
        snapshot: PageSnapshot,
        code: str,
        status: int,
    ) -> None:
        if decision.record_id is None:
            raise PageNotFoundError
        await uow.idempotency.complete(
            decision.record_id,
            IdempotencyOutcome(
                response_status=status,
                result_code=code,
                resource_type="page",
                resource_id=snapshot.page.id,
                resource_version=snapshot.page.version,
            ),
            completed_at=snapshot.page.updated_at,
        )

    def _audit(  # noqa: PLR0913 - safe audit facts are explicit.
        self,
        uow: PagesUnitOfWork,
        actor: ActorContext,
        request_id: str,
        event_type: str,
        resource_id: UUID,
        version: int,
        fields: tuple[str, ...],
    ) -> None:
        uow.audit.append(
            AuditEntry(
                id=self._id_factory(),
                event_type=event_type,
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=actor.actor_id,
                actor_label_snapshot=None,
                resource_type="page",
                resource_id=resource_id,
                request_id=request_id,
                occurred_at=self._clock(),
                outcome=AuditOutcome.SUCCESS,
                ip_pseudonym=None,
                metadata={"version": version, "fields": ",".join(fields)},
                schema_version=1,
            )
        )

    @staticmethod
    def _export_manifest(snapshot: PageSnapshot) -> dict[str, Any]:
        revision = snapshot.draft
        return {
            "format": "upw-page-export",
            "format_version": 1,
            "registry": list(REGISTRY_MANIFEST),
            "page": {
                "route_kind": snapshot.page.route_kind.value,
                "slug": snapshot.page.slug,
                "visible": snapshot.page.visible,
                "navigation_visible": snapshot.page.navigation_visible,
                "title": revision.values.title,
                "description": revision.values.description,
                "seo_title": revision.values.seo_title,
                "seo_description": revision.values.seo_description,
                "canonical_url": revision.values.canonical_url,
                "blocks": [
                    {
                        "block_type": block.values.block_type.value,
                        "schema_version": block.values.schema_version,
                        "position": block.position,
                        "visible": block.values.visible,
                        "title": block.values.title,
                        "subtitle": block.values.subtitle,
                        "description": block.values.description,
                        "theme": block.values.theme.value,
                        "layout": block.values.layout.value,
                        "responsive": {
                            "hide_on_small": block.values.responsive.hide_on_small,
                            "hide_on_large": block.values.responsive.hide_on_large,
                            "density": block.values.responsive.density,
                        },
                        "config": block.values.config,
                        "references": [
                            {
                                "kind": reference.kind.value,
                                "target_id": str(reference.target_id),
                                "role": reference.role.value,
                                "position": reference.position,
                                "required": reference.required,
                            }
                            for reference in block.references
                        ],
                    }
                    for block in revision.blocks
                ],
            },
        }
