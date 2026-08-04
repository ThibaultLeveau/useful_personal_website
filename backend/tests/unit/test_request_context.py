"""Tests for bounded request ID acceptance and secure generation."""

from __future__ import annotations

from app.common.request_context import select_request_id


def test_valid_edge_request_id_is_preserved() -> None:
    """A syntactically safe edge request ID should remain stable."""
    candidate = "edge-request-id-000000000001"

    assert select_request_id(candidate) == candidate


def test_invalid_request_ids_are_replaced() -> None:
    """Short, oversized, or unsafe IDs should be replaced with 128-bit IDs."""
    invalid_ids = (None, "short", "contains spaces and ?query", "x" * 129)

    replacements = {select_request_id(candidate) for candidate in invalid_ids}

    assert len(replacements) == len(invalid_ids)
    assert all(len(replacement) == 32 for replacement in replacements)
    assert all(replacement.isalnum() for replacement in replacements)
