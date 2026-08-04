"""Focused M6 project transport and OpenAPI privacy-contract tests."""

from __future__ import annotations

from datetime import date
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.api.v1.admin_projects import _map_error, _values
from app.api.v1.project_schemas import ProjectInput, PublicProjectData
from app.api.v1.public_projects import _data
from app.main import create_app
from app.modules.projects.domain import (
    ProjectStatus,
    ProjectValidationError,
    PublicProject,
    PublicProjectExperienceReference,
    PublicProjectReference,
    PublicProjectSkillReference,
)
from app.modules.projects.service import ProjectRelationError

PROJECT_ID = UUID("0198a12c-7000-7000-8000-000000000001")


def _input(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "name": "API Platform",
        "short_description": "A secure API-first platform.",
        "full_description": "## Overview\n\nControlled content.",
        "problem": "Delivery was risky.",
        "solution": "Introduced typed contracts.",
        "impact": "Reduced lead time.",
        "owner_role": "Technical lead",
        "architecture": "Bounded services.",
        "technologies": ["Python", "PostgreSQL"],
        "status": "active",
        "start_date": "2025-01-01",
    }
    values.update(overrides)
    return values


def test_project_input_rejects_mass_assignment_and_preserves_media_staging() -> None:
    """Transport rejects unknown state and carries only explicit staged media fields inward."""
    with pytest.raises(ValidationError):
        ProjectInput.model_validate(_input(version=99))
    payload = ProjectInput.model_validate(
        _input(cover_media_id="0198a12c-7000-7000-8000-000000000002")
    )
    values = _values(payload)
    assert values.cover_media_id is not None


def test_transport_maps_field_and_graph_errors_without_rejected_content() -> None:
    """Stable validation responses expose a path/code but never rejected values."""
    field = _map_error(ProjectValidationError(path="canonical_url", code="unsafe_url"))
    relation = _map_error(ProjectRelationError("related_project_cycle"))
    assert field.code == "VALIDATION_FAILED"
    field_items = field.details["fields"]
    relation_items = relation.details["fields"]
    assert isinstance(field_items, list)
    assert isinstance(field_items[0], dict)
    assert isinstance(relation_items, list)
    assert isinstance(relation_items[0], dict)
    assert field_items[0]["path"] == "body.canonical_url"
    assert relation_items[0]["code"] == "related_project_cycle"


def test_public_projection_exposes_only_media_ids_and_omits_internal_fields() -> None:
    """Public JSON carries safe logical IDs but no storage or revision details."""
    cover_id = UUID("0198a12c-7000-7000-8000-000000000002")
    screenshot_id = UUID("0198a12c-7000-7000-8000-000000000005")
    item = PublicProject(
        id=PROJECT_ID,
        slug="api-platform",
        name="API Platform",
        short_description="A secure API-first platform.",
        full_description="Overview.",
        problem="Problem.",
        solution="Solution.",
        impact="Impact.",
        owner_role="Technical lead",
        architecture="Architecture.",
        technologies=("Python",),
        status=ProjectStatus.ACTIVE,
        start_date=date(2025, 1, 1),
        end_date=None,
        repository_url=None,
        demo_url=None,
        featured=True,
        seo_title="API Platform",
        seo_description="A secure API-first platform.",
        canonical_url=None,
        cover_media_id=cover_id,
        screenshot_media_ids=(screenshot_id,),
        skills=(PublicProjectSkillReference(name="Python", slug="python"),),
        experiences=(
            PublicProjectExperienceReference(
                id=UUID("0198a12c-7000-7000-8000-000000000003"),
                company_name="Example Studio",
                role_title="Staff Engineer",
            ),
        ),
        related_projects=(
            PublicProjectReference(
                id=UUID("0198a12c-7000-7000-8000-000000000004"),
                slug="related",
                name="Related",
            ),
        ),
    )
    document = _data(item).model_dump(mode="json")
    assert document["cover_media_id"] == str(cover_id)
    assert document["screenshot_media_ids"] == [str(screenshot_id)]
    assert "gallery_available" not in document
    assert "published_revision_id" not in document


def test_openapi_exposes_closed_project_filters_and_unique_operations() -> None:
    """Generated contract inputs reflect the allow-listed query surface."""
    document = create_app().openapi()
    public_parameters = {
        value["name"] for value in document["paths"]["/api/v1/public/projects"]["get"]["parameters"]
    }
    admin_parameters = {
        value["name"] for value in document["paths"]["/api/v1/admin/projects"]["get"]["parameters"]
    }
    assert public_parameters == {
        "experience_id",
        "featured",
        "page",
        "page_size",
        "search",
        "skill",
        "sort",
        "status",
        "technology",
    }
    assert {"lifecycle", "skill_id", "experience_id", "featured"} <= admin_parameters
    operations = [
        operation["operationId"]
        for path in document["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operations) == len(set(operations))


def test_public_schema_cannot_accept_internal_fields() -> None:
    """Even direct schema construction rejects revision leakage through extras."""
    with pytest.raises(ValidationError):
        PublicProjectData.model_validate(
            {
                **_data(
                    PublicProject(
                        id=PROJECT_ID,
                        slug="api-platform",
                        name="API Platform",
                        short_description="Summary",
                        full_description="Overview",
                        problem="Problem",
                        solution="Solution",
                        impact="Impact",
                        owner_role="Lead",
                        architecture="Architecture",
                        technologies=("Python",),
                        status=ProjectStatus.ACTIVE,
                        start_date=date(2025, 1, 1),
                        end_date=None,
                        repository_url=None,
                        demo_url=None,
                        featured=False,
                        seo_title="API Platform",
                        seo_description="Summary",
                        canonical_url=None,
                        cover_media_id=None,
                        screenshot_media_ids=(),
                        skills=(),
                        experiences=(),
                        related_projects=(),
                    )
                ).model_dump(mode="json"),
                "draft_revision_id": str(PROJECT_ID),
            }
        )
