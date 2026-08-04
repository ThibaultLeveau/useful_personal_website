"""Closed administrator transport error catalogs and query primitive tests."""

# mypy: disable-error-code="attr-defined"
# ruff: noqa: D103, SLF001

from __future__ import annotations

from enum import StrEnum
from types import SimpleNamespace

import pytest

from app.api.v1 import (
    admin_api_tokens,
    admin_blog,
    admin_contacts,
    admin_experiences,
    admin_media,
    admin_pages,
    admin_projects,
    admin_site_configuration,
    admin_skills,
    integration_resources,
)
from app.common.application.idempotency import IdempotencyDecision, IdempotencyDecisionType
from app.common.domain.query import QueryValidationError
from app.common.errors import ApiError


class _Choice(StrEnum):
    FIRST = "first"


def _decision() -> IdempotencyDecision:
    return IdempotencyDecision(IdempotencyDecisionType.IN_PROGRESS)


@pytest.mark.parametrize(
    ("module", "error"),
    [
        (admin_skills, admin_skills.SkillValidationError(path="name", code="invalid")),
        (admin_skills, admin_skills.SkillsSlugConflictError("slug")),
        (admin_skills, admin_skills.RelationProviderUnavailableError()),
        (admin_skills, admin_skills.SkillsNotFoundError("skill")),
        (admin_skills, admin_skills.CategoryInUseError()),
        (admin_skills, admin_skills.SkillsIdempotencyRejectedError(_decision())),
        (
            admin_experiences,
            admin_experiences.ExperienceValidationError(path="title", code="invalid"),
        ),
        (admin_experiences, admin_experiences.SkillsNotFoundError("skill")),
        (admin_experiences, admin_experiences.ExperienceNotFoundError()),
        (
            admin_experiences,
            admin_experiences.ExperienceIdempotencyRejectedError(_decision()),
        ),
        (admin_experiences, admin_experiences.ExperiencePublicationError("draft_invalid")),
        (admin_experiences, admin_experiences.FrozenRevisionError()),
        (admin_experiences, admin_experiences.PointerIntegrityError()),
        (admin_experiences, ValueError("timestamp")),
        (admin_projects, admin_projects.MediaStateError()),
        (admin_projects, admin_projects.ProjectValidationError(path="title", code="invalid")),
        (admin_projects, admin_projects.SkillsNotFoundError("skill")),
        (admin_projects, admin_projects.ExperienceNotFoundError()),
        (admin_projects, admin_projects.ProjectRelationError("self_reference")),
        (admin_projects, admin_projects.ProjectSlugConflictError()),
        (admin_projects, admin_projects.ProjectNotFoundError()),
        (admin_projects, admin_projects.ProjectIdempotencyRejectedError(_decision())),
        (admin_projects, admin_projects.ProjectPublicationError("draft_invalid")),
        (admin_projects, admin_projects.FrozenProjectRevisionError()),
        (admin_projects, admin_projects.ProjectPointerIntegrityError()),
        (admin_projects, ValueError("timestamp")),
        (admin_blog, admin_blog.MediaStateError()),
        (admin_blog, admin_blog.BlogValidationError(path="title", code="invalid")),
        (admin_blog, admin_blog.BlogRelationError("unknown_relation")),
        (admin_blog, admin_blog.BlogSlugConflictError()),
        (admin_blog, admin_blog.BlogNotFoundError()),
        (admin_blog, admin_blog.BlogIdempotencyRejectedError(_decision())),
        (admin_blog, admin_blog.BlogPublicationError("draft_invalid")),
        (admin_blog, admin_blog.BlogTaxonomyUsageError(3)),
        (admin_blog, admin_blog.FrozenPostRevisionError()),
        (admin_blog, admin_blog.PostPointerIntegrityError()),
        (admin_blog, admin_blog.BlogIntegrityError()),
        (admin_blog, ValueError("timestamp")),
        (admin_pages, admin_pages.PageValidationError(path="slug", code="invalid")),
        (admin_pages, admin_pages.RegistryError(path="config", code="invalid")),
        (admin_pages, admin_pages.PageReferenceError(path="reference", code="missing")),
        (admin_pages, admin_pages.PageRouteConflictError()),
        (admin_pages, admin_pages.MediaStateError()),
        (admin_pages, admin_pages.PageNotFoundError()),
        (admin_pages, admin_pages.PagePublicationError("draft_invalid")),
        (admin_pages, admin_pages.PageIdempotencyRejectedError(_decision())),
        (admin_pages, admin_pages.FrozenPageRevisionError()),
        (admin_pages, admin_pages.PagePersistenceError()),
    ],
)
def test_closed_transport_errors_map_to_safe_api_errors(module: object, error: Exception) -> None:
    mapped = module._map_error(error)
    assert isinstance(mapped, ApiError)
    assert mapped.code in {
        "VALIDATION_FAILED",
        "NOT_FOUND",
        "RESOURCE_CONFLICT",
        "RESOURCE_VERSION_CONFLICT",
        "IDEMPOTENCY_IN_PROGRESS",
    }


@pytest.mark.parametrize(
    "parser",
    [
        admin_skills._parse_bool,
        admin_experiences._parse_bool,
        admin_projects._boolean,
        admin_blog._boolean,
    ],
)
def test_boolean_query_parsers_are_closed(parser: object) -> None:
    assert parser(None, path="query.visible") is None  # type: ignore[operator]
    assert parser("true", path="query.visible") is True  # type: ignore[operator]
    assert parser("false", path="query.visible") is False  # type: ignore[operator]
    with pytest.raises(QueryValidationError):
        parser("TRUE", path="query.visible")  # type: ignore[operator]


@pytest.mark.parametrize(
    "parser", [admin_experiences._parse_enum, admin_projects._enum, admin_blog._enum]
)
def test_enum_query_parsers_are_closed(parser: object) -> None:
    assert parser(None, _Choice, path="query.kind") is None  # type: ignore[operator]
    assert parser("first", _Choice, path="query.kind") is _Choice.FIRST  # type: ignore[operator]
    with pytest.raises(QueryValidationError):
        parser("other", _Choice, path="query.kind")  # type: ignore[operator]


@pytest.mark.parametrize(
    "error",
    [
        admin_media.MediaNotFoundError(),
        admin_media.MediaConflictError(),
        admin_media.MediaIdempotencyRejectedError(IdempotencyDecisionType.PAYLOAD_CONFLICT),
        admin_media.MediaIdempotencyRejectedError(IdempotencyDecisionType.IN_PROGRESS),
        admin_media.MediaValidationError(path="file", code="invalid"),
        admin_media.MediaUploadError("invalid_size"),
        admin_media.MediaUploadError("unsupported_format"),
        admin_media.MediaUploadError("processing_failed"),
    ],
)
def test_media_transport_errors_are_non_reflective(error: Exception) -> None:
    assert isinstance(admin_media._map_error(error), ApiError)


@pytest.mark.parametrize(
    "error",
    [
        admin_contacts.ContactNotFoundError(),
        admin_contacts.ContactConflictError(),
        admin_contacts.ContactValidationError("state", "invalid"),
        RuntimeError("synthetic"),
    ],
)
def test_contact_transport_errors_are_closed(error: Exception) -> None:
    assert isinstance(admin_contacts._map(error), ApiError)


@pytest.mark.parametrize(
    "error",
    [
        admin_api_tokens.ApiTokenNotFoundError(),
        admin_api_tokens.ApiTokenConflictError(),
        admin_api_tokens.ApiTokenValidationError("scopes", "required"),
        RuntimeError("synthetic"),
    ],
)
def test_api_token_transport_errors_are_closed(error: Exception) -> None:
    assert isinstance(admin_api_tokens._map(error), ApiError)


def test_transport_helpers_require_preconditions_and_composed_dependencies() -> None:
    with pytest.raises(ApiError):
        admin_api_tokens._version(None)
    with pytest.raises(ApiError):
        admin_contacts._missing_etag()

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    dependency_helpers = (
        admin_api_tokens._service,
        admin_contacts._service,
        admin_media._service,
        admin_pages._service,
        admin_projects._service,
        admin_skills._service,
        admin_site_configuration._profile_service,
        admin_site_configuration._settings_service,
        admin_site_configuration._navigation_service,
        integration_resources._projects,
        integration_resources._contacts,
    )
    for helper in dependency_helpers:
        with pytest.raises(ApiError) as raised:
            helper(request)  # type: ignore[arg-type]
        assert raised.value.code == "DEPENDENCY_UNAVAILABLE"
