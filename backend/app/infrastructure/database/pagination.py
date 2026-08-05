"""Bound-parameter SQLAlchemy page execution for already allow-listed queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.common.domain.pagination import Page, PageRequest, page_metadata

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_page[ItemT](
    session: AsyncSession,
    *,
    ordered_statement: Select[tuple[ItemT]],
    count_statement: Select[tuple[int]],
    request: PageRequest,
) -> Page[ItemT]:
    """Execute a caller-mapped ordered statement without accepting SQL field names."""
    total_items = (await session.execute(count_statement)).scalar_one()
    result = await session.execute(
        ordered_statement.offset(request.offset).limit(request.page_size)
    )
    return Page(
        items=tuple(result.scalars()),
        metadata=page_metadata(request, total_items=total_items),
    )
