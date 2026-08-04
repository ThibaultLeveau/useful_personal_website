"""M8 exact-catalog, schema, serializer, reference, and malicious-input proofs."""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.modules.pages.registry import (
    BLOCK_REGISTRY,
    REGISTRY_MANIFEST,
    BlockType,
    ReferenceKind,
    RegistryError,
    canonical_config,
    canonical_config_bytes,
    config_checksum,
    deserialize_config,
    extract_references,
    upgrade_config,
)

SKILL_ID = "0198a13d-8000-7000-8000-000000000002"
EXPERIENCE_ID = "0198a13d-8000-7000-8000-000000000003"
PROJECT_ID = "0198a13d-8000-7000-8000-000000000004"
POST_ID = "0198a13d-8000-7000-8000-000000000005"
MEDIA_ID = "0198a13d-8000-7000-8000-000000000006"
PAGE_ID = "0198a13d-8000-7000-8000-000000000007"

FIXTURES: dict[BlockType, dict[str, Any]] = {
    BlockType.HERO: {
        "eyebrow": "Independent engineer",
        "heading": "Systems that earn trust",
        "body": "I design clear, resilient products.",
        "actions": [{"label": "See projects", "destination": "/projects"}],
        "include_profile_evidence": True,
    },
    BlockType.PROFILE_SUMMARY: {},
    BlockType.CALL_TO_ACTION: {
        "heading": "Build something useful",
        "body": "Start with a concrete problem.",
        "actions": [{"label": "Read the work", "destination": "/projects"}],
    },
    BlockType.STATISTICS: {"items": [{"value": "12", "label": "Products shipped"}]},
    BlockType.SKILLS_GRID: {"skill_ids": [SKILL_ID], "maximum_items": 12},
    BlockType.FEATURED_SKILLS: {"skill_ids": [SKILL_ID], "maximum_items": 6},
    BlockType.EXPERIENCE_SUMMARY: {"experience_ids": [EXPERIENCE_ID], "maximum_items": 4},
    BlockType.EXPERIENCE_LIST: {"experience_ids": [EXPERIENCE_ID], "maximum_items": 8},
    BlockType.PROJECT_GRID: {"project_ids": [PROJECT_ID], "maximum_items": 12},
    BlockType.FEATURED_PROJECTS: {"project_ids": [PROJECT_ID], "maximum_items": 6},
    BlockType.LATEST_POSTS: {"post_ids": [POST_ID], "maximum_items": 3},
    BlockType.RICH_TEXT: {"source": "## Deliberate work\n\nSafe **CommonMark** only."},
    BlockType.IMAGE: {"media_id": MEDIA_ID, "alt": "Staged architectural diagram"},
    BlockType.IMAGE_WITH_TEXT: {
        "media_id": MEDIA_ID,
        "alt": "Staged product view",
        "heading": "Evidence in context",
        "body": "A bounded supporting explanation.",
    },
    BlockType.LINKS_COLLECTION: {
        "links": [{"label": "Source", "destination": "https://example.test/source"}]
    },
    BlockType.CONTACT_CALLOUT: {
        "heading": "Continue the conversation",
        "body": "Choose a safe public destination.",
        "actions": [{"label": "About", "destination": "/about"}],
    },
    BlockType.TESTIMONIAL: {
        "quote": "The implementation made difficult decisions visible.",
        "attribution": "Project collaborator",
    },
    BlockType.DIVIDER: {"style": "subtle"},
    BlockType.SPACER: {"size": "large", "narrow_size": "small"},
}


def test_registry_has_exact_spec_catalog_and_unique_renderer_parity() -> None:
    """No missing, placeholder, aliased, or duplicate kind can reach generation."""
    assert len(BlockType) == len(BLOCK_REGISTRY) == len(REGISTRY_MANIFEST) == 19
    assert set(FIXTURES) == set(BlockType) == set(BLOCK_REGISTRY)
    assert {item["renderer_key"] for item in REGISTRY_MANIFEST} == {
        block_type.value for block_type in BlockType
    }


@pytest.mark.parametrize("block_type", list(BlockType))
def test_every_fixture_round_trips_canonically(block_type: BlockType) -> None:
    """Every exact kind/version has a deterministic strict schema fixture."""
    parsed = deserialize_config(block_type, 1, FIXTURES[block_type])
    canonical = canonical_config(parsed)
    reparsed = deserialize_config(block_type, 1, canonical)
    assert canonical_config(reparsed) == canonical
    assert canonical_config_bytes(reparsed) == canonical_config_bytes(parsed)
    assert len(config_checksum(parsed)) == 64
    assert upgrade_config(block_type, 1, canonical) == (1, canonical)


def test_reference_extraction_is_ordered_typed_and_duplicate_safe() -> None:
    """Clients cannot manufacture normalized rows independently of config."""
    parsed = deserialize_config(
        BlockType.SKILLS_GRID,
        1,
        {"skill_ids": [SKILL_ID, "0198a13d-8000-7000-8000-000000000099"]},
    )
    references = extract_references(BlockType.SKILLS_GRID, parsed)
    assert [item.kind for item in references] == [ReferenceKind.SKILL, ReferenceKind.SKILL]
    assert [item.position for item in references] == [0, 1]
    assert all(not item.required for item in references)

    duplicate = deserialize_config(BlockType.SKILLS_GRID, 1, {"skill_ids": [SKILL_ID, SKILL_ID]})
    with pytest.raises(RegistryError) as captured:
        extract_references(BlockType.SKILLS_GRID, duplicate)
    assert captured.value.code == "duplicate_reference"

    action = deserialize_config(
        BlockType.CALL_TO_ACTION,
        1,
        {
            "heading": "Continue",
            "body": "Open the custom page.",
            "actions": [{"label": "Details", "page_id": PAGE_ID}],
        },
    )
    assert extract_references(BlockType.CALL_TO_ACTION, action)[0].kind is ReferenceKind.PAGE


@pytest.mark.parametrize(
    ("block_type", "payload"),
    [
        (BlockType.HERO, {**FIXTURES[BlockType.HERO], "renderer": "attacker"}),
        (BlockType.DIVIDER, {"style": "line", "class": "fixed inset-0"}),
        (
            BlockType.LINKS_COLLECTION,
            {"links": [{"label": "Bad", "destination": "javascript:alert(1)"}]},
        ),
        (BlockType.RICH_TEXT, {"source": "<script>alert(1)</script>"}),
        (BlockType.STATISTICS, {"items": [{"value": "1", "label": "A", "query": "SELECT 1"}]}),
        (BlockType.SPACER, {"__proto__": {"polluted": True}, "size": "small"}),
    ],
)
def test_malicious_or_undeclared_config_fails_closed(
    block_type: BlockType, payload: dict[str, object]
) -> None:
    """HTML, code, CSS, query, unsafe URL, and prototype-shaped input cannot persist."""
    with pytest.raises(RegistryError):
        deserialize_config(block_type, 1, payload)


def test_unknown_version_depth_size_unicode_and_nonfinite_numbers_fail_closed() -> None:
    """Bounded validation rejects resource-exhaustion and ambiguous JSON shapes."""
    with pytest.raises(RegistryError) as version:
        deserialize_config(BlockType.DIVIDER, 2, {"style": "line"})
    assert version.value.code == "unsupported_schema_version"

    deep: dict[str, object] = {"value": "leaf"}
    for _ in range(10):
        deep = {"nested": deep}
    for payload in (
        deep,
        {"style": float("nan")},
        {"style": "line\u202e"},
        {"style": "x" * 4_001},
    ):
        with pytest.raises(RegistryError):
            deserialize_config(BlockType.DIVIDER, 1, payload)


def test_canonical_form_is_portable_json_without_python_objects() -> None:
    """Canonical output contains only standard JSON primitives."""
    value = canonical_config(deserialize_config(BlockType.PROFILE_SUMMARY, 1, {}))
    decoded = json.loads(
        canonical_config_bytes(deserialize_config(BlockType.PROFILE_SUMMARY, 1, value))
    )
    assert decoded == {
        "about_destination": "/about",
        "show_biography": True,
        "show_location": True,
    }
