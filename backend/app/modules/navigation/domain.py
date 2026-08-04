"""Navigation/footer trees, link policy, and deterministic order rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from uuid import UUID

REGISTERED_INTERNAL_ROUTES = frozenset({"/", "/about", "/skills"})
MAXIMUM_ROOT_ITEMS = 24
MAXIMUM_CHILD_ITEMS = 16
MAXIMUM_FOOTER_COLUMNS = 8
MAXIMUM_FOOTER_ITEMS = 16
CONTROL_CHARACTER_BOUNDARY = 32


class TreeValidationError(ValueError):
    """A tree, order, parent, or link violates the published contract."""

    def __init__(self, *, path: str, code: str) -> None:
        """Retain a safe field path and stable validation code."""
        super().__init__("navigation or footer input is invalid")
        self.path = path
        self.code = code


class LinkKind(StrEnum):
    """Supported navigation destination categories."""

    INTERNAL = "internal"
    EXTERNAL = "external"


class LinkTarget(StrEnum):
    """Supported browser target behaviors."""

    SAME_WINDOW = "same_window"
    NEW_WINDOW = "new_window"


class FooterItemKind(StrEnum):
    """Semantic footer link categories."""

    LINK = "link"
    SOCIAL = "social"
    LEGAL = "legal"


@dataclass(frozen=True, slots=True)
class NavigationItem:
    """One flat tree node with an optional root parent."""

    id: UUID
    parent_id: UUID | None
    label: str
    link_kind: LinkKind
    href: str
    target: LinkTarget
    visible: bool
    position: int
    version: int = 1


@dataclass(frozen=True, slots=True)
class NavigationTree:
    """Versioned complete primary navigation aggregate."""

    id: UUID
    items: tuple[NavigationItem, ...]
    version: int


@dataclass(frozen=True, slots=True)
class FooterItem:
    """One ordered footer destination."""

    id: UUID
    label: str
    link_kind: LinkKind
    item_kind: FooterItemKind
    href: str
    target: LinkTarget
    visible: bool
    position: int
    version: int = 1


@dataclass(frozen=True, slots=True)
class FooterColumn:
    """One ordered group of footer destinations."""

    id: UUID
    title: str
    visible: bool
    position: int
    items: tuple[FooterItem, ...]
    version: int = 1


@dataclass(frozen=True, slots=True)
class FooterTree:
    """Versioned complete footer aggregate."""

    id: UUID
    copyright_text: str | None
    columns: tuple[FooterColumn, ...]
    version: int


def _validate_href(kind: LinkKind, href: str, target: LinkTarget, path: str) -> None:
    if (
        not href
        or href != href.strip()
        or any(ord(character) < CONTROL_CHARACTER_BOUNDARY for character in href)
    ):
        raise TreeValidationError(path=path, code="invalid_url")
    if kind is LinkKind.INTERNAL:
        if href not in REGISTERED_INTERNAL_ROUTES or target is not LinkTarget.SAME_WINDOW:
            raise TreeValidationError(path=path, code="unknown_internal_route")
        return
    parsed = urlsplit(href)
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or "\\" in href
    ):
        raise TreeValidationError(path=path, code="unsafe_external_url")


def _require_complete_positions(positions: list[int], *, path: str) -> None:
    if sorted(positions) != list(range(len(positions))):
        raise TreeValidationError(path=path, code="invalid_order")


def _validate_parent_links(
    items: tuple[NavigationItem, ...],
    by_id: dict[UUID, NavigationItem],
) -> None:
    for index, item in enumerate(items):
        _validate_href(item.link_kind, item.href, item.target, f"items.{index}.href")
        if item.parent_id is None:
            continue
        parent = by_id.get(item.parent_id)
        if parent is None:
            raise TreeValidationError(path=f"items.{index}.parent_id", code="orphan")
        if parent.id == item.id:
            raise TreeValidationError(path=f"items.{index}.parent_id", code="self_parent")
        if parent.parent_id is not None:
            raise TreeValidationError(path=f"items.{index}.parent_id", code="maximum_depth")


def _validate_child_groups(
    items: tuple[NavigationItem, ...],
    roots: list[NavigationItem],
) -> None:
    for parent in roots:
        children = [item for item in items if item.parent_id == parent.id]
        if len(children) > MAXIMUM_CHILD_ITEMS:
            raise TreeValidationError(path="items", code="too_many_children")
        _require_complete_positions(
            [item.position for item in children],
            path="items.position",
        )


def validate_navigation(items: tuple[NavigationItem, ...]) -> None:
    """Reject cycles, depth greater than two, invalid parents, links, and gaps."""
    if len(items) > MAXIMUM_ROOT_ITEMS * (MAXIMUM_CHILD_ITEMS + 1):
        raise TreeValidationError(path="items", code="too_many_items")
    by_id = {item.id: item for item in items}
    if len(by_id) != len(items):
        raise TreeValidationError(path="items", code="duplicate_id")
    roots = [item for item in items if item.parent_id is None]
    if len(roots) > MAXIMUM_ROOT_ITEMS:
        raise TreeValidationError(path="items", code="too_many_roots")
    _require_complete_positions([item.position for item in roots], path="items.position")
    _validate_parent_links(items, by_id)
    _validate_child_groups(items, roots)
    if any(
        item.parent_id is not None and by_id[item.parent_id].parent_id == item.id for item in items
    ):
        raise TreeValidationError(path="items.parent_id", code="cycle")


def validate_footer(columns: tuple[FooterColumn, ...]) -> None:
    """Reject duplicate IDs, empty visible columns, unsafe links, and order gaps."""
    if len(columns) > MAXIMUM_FOOTER_COLUMNS:
        raise TreeValidationError(path="columns", code="too_many_columns")
    if len({column.id for column in columns}) != len(columns):
        raise TreeValidationError(path="columns", code="duplicate_id")
    _require_complete_positions([column.position for column in columns], path="columns.position")
    item_ids: set[UUID] = set()
    for column_index, column in enumerate(columns):
        if len(column.items) > MAXIMUM_FOOTER_ITEMS:
            raise TreeValidationError(path=f"columns.{column_index}.items", code="too_many_items")
        if column.visible and not column.items:
            raise TreeValidationError(path=f"columns.{column_index}.items", code="empty_column")
        _require_complete_positions(
            [item.position for item in column.items],
            path=f"columns.{column_index}.items.position",
        )
        for item_index, item in enumerate(column.items):
            if item.id in item_ids:
                raise TreeValidationError(path="columns.items", code="duplicate_id")
            item_ids.add(item.id)
            _validate_href(
                item.link_kind,
                item.href,
                item.target,
                f"columns.{column_index}.items.{item_index}.href",
            )


def public_navigation(tree: NavigationTree) -> NavigationTree:
    """Remove hidden nodes and children of hidden parents."""
    visible_roots = {item.id for item in tree.items if item.visible and item.parent_id is None}
    return NavigationTree(
        id=tree.id,
        items=tuple(
            item
            for item in tree.items
            if item.visible and (item.parent_id is None or item.parent_id in visible_roots)
        ),
        version=tree.version,
    )


def public_footer(tree: FooterTree) -> FooterTree:
    """Remove hidden columns and links from the public projection."""
    return FooterTree(
        id=tree.id,
        copyright_text=tree.copyright_text,
        columns=tuple(
            FooterColumn(
                id=column.id,
                title=column.title,
                visible=True,
                position=column.position,
                items=tuple(item for item in column.items if item.visible),
                version=column.version,
            )
            for column in tree.columns
            if column.visible and any(item.visible for item in column.items)
        ),
        version=tree.version,
    )
