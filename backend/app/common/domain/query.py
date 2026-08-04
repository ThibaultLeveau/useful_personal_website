"""Allow-listed filter and deterministic sort parsing for collection use cases."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.common.domain.pagination import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, PageRequest

if TYPE_CHECKING:
    from collections.abc import Sequence

_FIELD_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True, slots=True)
class QueryIssue:
    """Safe validation fact that never reflects an untrusted query value."""

    path: str
    code: str


class QueryValidationError(Exception):
    """Raised with bounded safe issues when a collection query is not accepted."""

    def __init__(self, issues: tuple[QueryIssue, ...]) -> None:
        """Retain at least one safe validation issue."""
        if not issues:
            msg = "query validation requires at least one issue"
            raise ValueError(msg)
        super().__init__("the collection query is invalid")
        self.issues = issues


@dataclass(frozen=True, slots=True)
class SortTerm:
    """One catalog key and direction; never a SQL identifier fragment."""

    field: str
    descending: bool = False


@dataclass(frozen=True, slots=True)
class QueryCatalog:
    """Endpoint-owned filter/sort keys and deterministic default ordering."""

    allowed_filters: frozenset[str]
    allowed_sorts: frozenset[str]
    default_sort: tuple[SortTerm, ...]

    def __post_init__(self) -> None:
        """Require safe names and the universal opaque-ID tie breaker."""
        all_fields = self.allowed_filters | self.allowed_sorts
        if any(_FIELD_PATTERN.fullmatch(field) is None for field in all_fields):
            msg = "query catalog keys must be safe snake_case names"
            raise ValueError(msg)
        if "id" not in self.allowed_sorts:
            msg = "every sort catalog must allow the deterministic id tie breaker"
            raise ValueError(msg)
        default_fields = [term.field for term in self.default_sort]
        if (
            not default_fields
            or len(default_fields) != len(set(default_fields))
            or any(field not in self.allowed_sorts for field in default_fields)
        ):
            msg = "default sort terms must be unique allowed fields"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class CollectionQuery:
    """Validated page, filter values, and deterministic catalog sort terms."""

    page: PageRequest
    filters: dict[str, str]
    sort: tuple[SortTerm, ...]


def _parse_positive_integer(
    values: list[str],
    *,
    path: str,
    default: int,
    issues: list[QueryIssue],
) -> int:
    if not values:
        return default
    value = values[0]
    if not value.isascii() or not value.isdecimal():
        issues.append(QueryIssue(path=path, code="integer"))
        return default
    parsed = int(value)
    if parsed < 1:
        issues.append(QueryIssue(path=path, code="range"))
        return default
    return parsed


def _parse_sort(
    raw_value: str | None,
    *,
    catalog: QueryCatalog,
    issues: list[QueryIssue],
) -> tuple[SortTerm, ...]:
    if raw_value is None:
        terms = list(catalog.default_sort)
    else:
        pieces = raw_value.split(",")
        terms = []
        for piece in pieces:
            descending = piece.startswith("-")
            field = piece[1:] if descending else piece
            if not field or _FIELD_PATTERN.fullmatch(field) is None:
                issues.append(QueryIssue(path="query.sort", code="invalid_sort"))
                continue
            if field not in catalog.allowed_sorts:
                issues.append(QueryIssue(path="query.sort", code="unsupported_sort"))
                continue
            terms.append(SortTerm(field=field, descending=descending))
        fields = [term.field for term in terms]
        if len(fields) != len(set(fields)):
            issues.append(QueryIssue(path="query.sort", code="duplicate_sort"))
    if all(term.field != "id" for term in terms):
        terms.append(SortTerm(field="id"))
    return tuple(terms)


def parse_collection_query(
    pairs: Sequence[tuple[str, str]],
    *,
    catalog: QueryCatalog,
) -> CollectionQuery:
    """Parse exact endpoint parameters and reject every unknown or duplicate key."""
    grouped: dict[str, list[str]] = {}
    for key, value in pairs:
        grouped.setdefault(key, []).append(value)

    issues: list[QueryIssue] = []
    accepted_keys = {"page", "page_size", "sort"} | set(catalog.allowed_filters)
    issues.extend(
        [
            QueryIssue(path="query", code="unsupported_field")
            for key in grouped
            if key not in accepted_keys
        ]
    )
    for key, count in Counter(key for key, _value in pairs).items():
        if count > 1:
            issues.append(QueryIssue(path=f"query.{key}", code="duplicate_field"))

    page_number = _parse_positive_integer(
        grouped.get("page", []),
        path="query.page",
        default=DEFAULT_PAGE,
        issues=issues,
    )
    page_size = _parse_positive_integer(
        grouped.get("page_size", []),
        path="query.page_size",
        default=DEFAULT_PAGE_SIZE,
        issues=issues,
    )
    try:
        page = PageRequest(page=page_number, page_size=page_size)
    except ValueError:
        issues.append(QueryIssue(path="query.page_size", code="range"))
        page = PageRequest()

    sort_values = grouped.get("sort", [])
    sort = _parse_sort(sort_values[0] if sort_values else None, catalog=catalog, issues=issues)
    filters = {
        key: values[0]
        for key, values in grouped.items()
        if key in catalog.allowed_filters and values
    }
    if issues:
        raise QueryValidationError(tuple(issues))
    return CollectionQuery(page=page, filters=filters, sort=sort)
