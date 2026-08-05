"""Page-number pagination value objects with exact total metadata."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAXIMUM_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Validated page-number request independent of any persistence technology."""

    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        """Enforce positive bounded pagination without bool-as-int ambiguity."""
        if isinstance(self.page, bool) or self.page < 1:
            msg = "page must be a positive integer"
            raise ValueError(msg)
        if (
            isinstance(self.page_size, bool)
            or self.page_size < 1
            or self.page_size > MAXIMUM_PAGE_SIZE
        ):
            msg = f"page_size must be between 1 and {MAXIMUM_PAGE_SIZE}"
            raise ValueError(msg)

    @property
    def offset(self) -> int:
        """Return the bounded SQL offset implied by this request."""
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class PageMetadata:
    """Exact collection traversal facts returned with a list response."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_previous: bool
    has_next: bool


@dataclass(frozen=True, slots=True)
class Page[ItemT]:
    """Immutable page items paired with exact traversal metadata."""

    items: tuple[ItemT, ...]
    metadata: PageMetadata


def page_metadata(request: PageRequest, *, total_items: int) -> PageMetadata:
    """Build deterministic metadata, including empty and beyond-last pages."""
    if isinstance(total_items, bool) or total_items < 0:
        msg = "total_items must be a non-negative integer"
        raise ValueError(msg)
    total_pages = (total_items + request.page_size - 1) // request.page_size
    return PageMetadata(
        page=request.page,
        page_size=request.page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_previous=request.page > 1,
        has_next=request.page < total_pages,
    )
