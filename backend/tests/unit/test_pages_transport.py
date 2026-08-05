"""M8 page transport and OpenAPI discriminated-union proofs."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.api.v1.page_schemas import (
    AddBlockRequest,
    PageCreateRequest,
    PageUpdateRequest,
)
from app.main import create_app
from app.modules.pages.registry import BlockType


def test_openapi_has_exact_nineteen_kind_discriminator_and_unique_operations() -> None:
    """Generated clients receive one exact closed block union with no alias escape."""
    schema = create_app().openapi()
    add_block = schema["components"]["schemas"]["AddBlockRequest"]
    block_schema = add_block["properties"]["block"]
    mapping = block_schema["discriminator"]["mapping"]
    assert block_schema["discriminator"]["propertyName"] == "block_type"
    assert set(mapping) == {item.value for item in BlockType}
    assert len(block_schema["oneOf"]) == 19

    operation_ids = [
        operation["operationId"]
        for path in schema["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete"}
    ]
    assert len(operation_ids) == len(set(operation_ids))
    assert {
        "admin_page_create",
        "admin_page_block_add",
        "admin_page_blocks_reorder",
        "admin_page_preview",
        "admin_page_export",
        "admin_page_publish",
        "public_page_home_get",
        "public_pages_list",
        "public_page_custom_get",
    }.issubset(operation_ids)


def test_page_and_block_requests_reject_server_owned_or_arbitrary_fields() -> None:
    """Pointers, raw renderer/CSS/query fields, and undeclared config cannot mass assign."""
    with pytest.raises(ValidationError):
        PageCreateRequest.model_validate(
            {
                "route_kind": "custom",
                "slug": "work",
                "title": "Work",
                "description": "Selected evidence.",
                "published_revision_id": str(UUID(int=1)),
            }
        )
    with pytest.raises(ValidationError):
        AddBlockRequest.model_validate(
            {
                "block": {
                    "block_type": "divider",
                    "config": {"style": "line", "css": "position:fixed"},
                }
            }
        )
    with pytest.raises(ValidationError):
        AddBlockRequest.model_validate(
            {
                "block": {
                    "block_type": "attacker_renderer",
                    "config": {},
                }
            }
        )


def test_every_kind_requires_its_exact_type_specific_config() -> None:
    """The discriminator cannot be paired with another kind's config shape."""
    accepted = AddBlockRequest.model_validate(
        {
            "block": {
                "block_type": "hero",
                "config": {"heading": "Useful work", "body": "Evidence over claims."},
            }
        }
    )
    assert accepted.block.block_type is BlockType.HERO
    with pytest.raises(ValidationError):
        AddBlockRequest.model_validate(
            {
                "block": {
                    "block_type": "hero",
                    "config": {"style": "line"},
                }
            }
        )


def test_home_and_custom_shapes_remain_domain_validated() -> None:
    """Transport accepts only declared fields while domain owns route semantics."""
    home = PageCreateRequest.model_validate(
        {
            "route_kind": "home",
            "title": "Home",
            "description": "A useful personal website.",
        }
    )
    assert home.slug is None
    update = PageUpdateRequest.model_validate(
        {
            "route_kind": "custom",
            "slug": "selected-work",
            "title": "Selected work",
            "description": "A focused collection.",
            "visible": False,
        }
    )
    assert update.visible is False
