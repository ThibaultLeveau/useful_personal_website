"""In-process tests for safe centralized API error handling."""

from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

import pytest
from fastapi import Query
from httpx import ASGITransport, AsyncClient
from pydantic import Field

from app.api.v1.schemas import ApiModel
from app.common.errors import ApiError
from app.config import Environment, Settings
from app.main import create_app


class ProbePayload(ApiModel):
    """Strict body used to exercise safe validation-path serialization."""

    name: str = Field(min_length=1, max_length=20)


def _client() -> AsyncClient:
    application = create_app(settings=Settings(environment=Environment.TEST))

    @application.get("/api/v1/_test/explicit-error", include_in_schema=False)
    async def explicit_error() -> None:
        raise ApiError(
            status_code=HTTPStatus.CONFLICT,
            code="RESOURCE_VERSION_CONFLICT",
            message="The resource changed since it was loaded.",
            details={"fields": []},
        )

    @application.get("/api/v1/_test/validation", include_in_schema=False)
    async def validation(value: Annotated[int, Query(gt=0)]) -> dict[str, int]:
        return {"value": value}

    @application.get("/api/v1/_test/unexpected", include_in_schema=False)
    async def unexpected() -> None:
        msg = "database failed at postgresql://app:private-password@internal-db/portfolio"
        raise RuntimeError(msg)

    @application.post("/api/v1/_test/body-validation", include_in_schema=False)
    async def body_validation(payload: ProbePayload) -> ProbePayload:
        return payload

    catalog = {
        "bad": "BAD_REQUEST",
        "authentication": "AUTHENTICATION_REQUIRED",
        "authorization": "AUTHORIZATION_DENIED",
        "not-found": "NOT_FOUND",
        "conflict": "RESOURCE_VERSION_CONFLICT",
        "validation": "VALIDATION_FAILED",
        "precondition": "PRECONDITION_REQUIRED",
        "rate": "RATE_LIMITED",
        "unavailable": "DEPENDENCY_UNAVAILABLE",
    }

    @application.get("/api/v1/_test/catalog/{name}", include_in_schema=False)
    async def catalog_error(name: str) -> None:
        code = catalog[name]
        if code == "RATE_LIMITED":
            raise ApiError.from_code(
                code,
                details={"retry_after_seconds": 17},
                retry_after_seconds=17,
            )
        raise ApiError.from_code(code)

    return AsyncClient(
        transport=ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://testserver",
    )


async def test_explicit_api_error_preserves_safe_contract() -> None:
    """Known application errors should preserve stable code/message/details."""
    async with _client() as client:
        response = await client.get("/api/v1/_test/explicit-error")

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "RESOURCE_VERSION_CONFLICT",
        "message": "The resource changed since it was loaded.",
        "details": {"fields": []},
        "request_id": response.headers["X-Request-ID"],
    }


async def test_validation_error_does_not_reflect_untrusted_input() -> None:
    """Validation details should contain only path, code, and generic message."""
    malicious = "private-token<script>alert(1)</script>"
    async with _client() as client:
        response = await client.get("/api/v1/_test/validation", params={"value": malicious})

    serialized = response.text
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert response.json()["error"]["details"]["fields"][0]["path"] == "query.value"
    assert malicious not in serialized
    assert "<script>" not in serialized


async def test_validation_location_does_not_reflect_an_adversarial_field_name() -> None:
    """An extra JSON key may not become a reflected path or diagnostic value."""
    malicious_field = "private-token;DROP TABLE audit_entry"
    async with _client() as client:
        response = await client.post(
            "/api/v1/_test/body-validation",
            json={"name": "valid", malicious_field: "secret"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["details"]["fields"][0]["path"] == "body.*"
    assert malicious_field not in response.text
    assert "secret" not in response.text


async def test_unexpected_error_is_safe_and_correlated() -> None:
    """Unhandled failures must not expose exception, stack, DSN, or credentials."""
    async with _client() as client:
        response = await client.get("/api/v1/_test/unexpected")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "details": {},
            "request_id": response.headers["X-Request-ID"],
        }
    }
    assert "private-password" not in response.text
    assert "postgresql" not in response.text
    assert "RuntimeError" not in response.text


async def test_framework_404_uses_stable_error_envelope() -> None:
    """Unmatched routes should not escape FastAPI's default detail contract."""
    async with _client() as client:
        response = await client.get("/api/v1/not-present")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "NOT_FOUND",
        "message": "The requested resource was not found.",
        "details": {},
        "request_id": response.headers["X-Request-ID"],
    }


@pytest.mark.parametrize(
    ("name", "status", "code"),
    [
        ("bad", 400, "BAD_REQUEST"),
        ("authentication", 401, "AUTHENTICATION_REQUIRED"),
        ("authorization", 403, "AUTHORIZATION_DENIED"),
        ("not-found", 404, "NOT_FOUND"),
        ("conflict", 409, "RESOURCE_VERSION_CONFLICT"),
        ("validation", 422, "VALIDATION_FAILED"),
        ("precondition", 428, "PRECONDITION_REQUIRED"),
        ("rate", 429, "RATE_LIMITED"),
        ("unavailable", 503, "DEPENDENCY_UNAVAILABLE"),
    ],
)
async def test_registered_status_matrix_is_correlated_and_never_cacheable(
    name: str,
    status: int,
    code: str,
) -> None:
    """Representative application errors preserve one stable status/code contract."""
    request_id = "edge-contract-request-000001"
    async with _client() as client:
        response = await client.get(
            f"/api/v1/_test/catalog/{name}",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == status
    assert response.headers["X-Request-ID"] == request_id
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["request_id"] == request_id
    assert isinstance(response.json()["error"]["details"], dict)
    if status == 429:
        assert response.headers["Retry-After"] == "17"
