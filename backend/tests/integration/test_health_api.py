"""In-process API tests for the baseline health contract."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.auth import require_full_admin_session
from app.common.errors import ApiError
from app.common.health import ReadinessCategory, ReadinessResult
from app.config import Environment, Settings
from app.main import create_app
from app.modules.identity.domain import SessionView


class ReadyProbe:
    """Successful injected readiness probe."""

    def __init__(self) -> None:
        """Initialize the dependency-call counter."""
        self.calls = 0

    async def check(self) -> ReadinessResult:
        """Return readiness while tracking dependency calls."""
        self.calls += 1
        return ReadinessResult(ready=True)


class UnavailableProbe:
    """Controlled dependency failure for the aggregate admin view."""

    def __init__(self, category: ReadinessCategory) -> None:
        """Select the safe unavailable category returned by the probe."""
        self.category = category
        self.calls = 0

    async def check(self) -> ReadinessResult:
        """Return one safe unavailable category."""
        self.calls += 1
        return ReadinessResult(ready=False, category=self.category)


class ExplodingProbe:
    """Dependency probe that simulates a timeout or unavailable database."""

    def __init__(self) -> None:
        """Initialize the dependency-call counter."""
        self.calls = 0

    async def check(self) -> ReadinessResult:
        """Raise a sensitive adapter exception for safe-mapping coverage."""
        self.calls += 1
        msg = "timeout at postgresql://runtime:private@internal-db/site"
        raise TimeoutError(msg)


async def _authenticated_admin() -> SessionView:
    now = datetime(2026, 8, 3, 8, 0, tzinfo=UTC)
    return SessionView(
        administrator_id=UUID("0198abc0-0000-7000-8000-000000000001"),
        display_name="Site Owner",
        must_change_password=False,
        idle_expires_at=now + timedelta(minutes=30),
        absolute_expires_at=now + timedelta(hours=12),
        session_id=UUID("0198abc0-0000-7000-8000-000000000002"),
    )


async def _anonymous_admin() -> SessionView:
    """Reject the protected dependency with the stable anonymous contract."""
    error_code = "AUTHENTICATION_REQUIRED"
    raise ApiError.from_code(error_code)


def _test_settings() -> Settings:
    return Settings(environment=Environment.TEST)


async def test_liveness_uses_success_envelope_and_never_calls_probe() -> None:
    """Liveness must remain process-only and correlated by request ID."""
    probe = ReadyProbe()
    request_id = "edge-request-id-000000000001"
    application = create_app(settings=_test_settings(), readiness_probe=probe)
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/health/live",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["X-Request-ID"] == request_id
    assert response.json() == {
        "data": {"status": "ok"},
        "meta": {"request_id": request_id},
    }
    assert probe.calls == 0


@pytest.mark.parametrize(
    "probe",
    [
        ReadyProbe(),
        UnavailableProbe(ReadinessCategory.DATABASE),
        UnavailableProbe(ReadinessCategory.MIGRATION),
        ExplodingProbe(),
    ],
    ids=["database-current", "database-outage", "revision-mismatch", "database-timeout"],
)
async def test_liveness_is_identical_for_every_dependency_state(
    probe: ReadyProbe | UnavailableProbe | ExplodingProbe,
) -> None:
    """Liveness must never invoke database, timeout, or revision probes."""
    application = create_app(settings=_test_settings(), readiness_probe=probe)
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.json()["data"] == {"status": "ok"}
    assert response.json()["meta"]["request_id"] == response.headers["X-Request-ID"]
    assert probe.calls == 0


async def test_readiness_uses_injected_probe_and_success_envelope() -> None:
    """A successful dependency probe should produce the stable ready contract."""
    probe = ReadyProbe()
    application = create_app(settings=_test_settings(), readiness_probe=probe)
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health/ready")

    body = response.json()
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert body["data"] == {"status": "ready"}
    assert body["meta"]["request_id"] == response.headers["X-Request-ID"]
    assert probe.calls == 1


async def test_default_readiness_fails_closed_with_safe_category() -> None:
    """The app must not claim database readiness before M0-T05 supplies a probe."""
    application = create_app(settings=_test_settings())
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health/ready")

    body = response.json()
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "private, no-store"
    assert body == {
        "error": {
            "code": "DEPENDENCY_UNAVAILABLE",
            "message": "A required dependency is unavailable.",
            "details": {"status": "not_ready", "dependency": "database"},
            "request_id": response.headers["X-Request-ID"],
        }
    }


@pytest.mark.parametrize(
    ("probe", "dependency"),
    [
        (UnavailableProbe(ReadinessCategory.DATABASE), "database"),
        (UnavailableProbe(ReadinessCategory.MIGRATION), "migration"),
        (ExplodingProbe(), "database"),
    ],
    ids=["database-outage", "revision-mismatch", "database-timeout"],
)
async def test_readiness_fails_closed_with_safe_dependency_category(
    probe: UnavailableProbe | ExplodingProbe,
    dependency: str,
) -> None:
    """Dependency failures produce only the stable not-ready contract."""
    request_id = "health-readiness-request-0001"
    application = create_app(settings=_test_settings(), readiness_probe=probe)
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/health/ready",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["X-Request-ID"] == request_id
    assert response.json() == {
        "error": {
            "code": "DEPENDENCY_UNAVAILABLE",
            "message": "A required dependency is unavailable.",
            "details": {"status": "not_ready", "dependency": dependency},
            "request_id": request_id,
        }
    }
    assert "postgresql" not in response.text
    assert "private" not in response.text
    assert probe.calls == 1


async def test_admin_health_is_authenticated_private_and_safe() -> None:
    """The privileged view exposes only bounded build and aggregate status fields."""
    application = create_app(
        settings=Settings(
            environment=Environment.TEST,
            build_version="1.2.3",
            build_commit="abcdef123456",
        ),
        readiness_probe=ReadyProbe(),
    )
    application.dependency_overrides[require_full_admin_session] = _authenticated_admin
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/admin/health")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Pragma"] == "no-cache"
    body = response.json()
    assert body["data"] | {"checked_at": "ignored"} == {
        "status": "operational",
        "application_status": "operational",
        "database_status": "operational",
        "migration_status": "current",
        "build_version": "1.2.3",
        "build_commit": "abcdef123456",
        "checked_at": "ignored",
    }
    assert datetime.fromisoformat(body["data"]["checked_at"]).tzinfo is not None
    assert "test" not in response.text
    assert "postgresql" not in response.text


async def test_admin_health_reports_safe_degraded_categories() -> None:
    """A migration mismatch distinguishes database reachability without raw revision data."""
    application = create_app(
        settings=_test_settings(),
        readiness_probe=UnavailableProbe(ReadinessCategory.MIGRATION),
    )
    application.dependency_overrides[require_full_admin_session] = _authenticated_admin
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/admin/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "degraded"
    assert response.json()["data"]["database_status"] == "operational"
    assert response.json()["data"]["migration_status"] == "unavailable"


async def test_admin_health_denies_anonymous_access_without_cache_or_disclosure() -> None:
    """The administrator aggregate is never available to an anonymous caller."""
    application = create_app(settings=_test_settings(), readiness_probe=ReadyProbe())
    application.dependency_overrides[require_full_admin_session] = _anonymous_admin
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/admin/health")

    assert response.status_code == 401
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.headers["Pragma"] == "no-cache"
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    for forbidden in ("postgresql", "database_url", "password", "traceback"):
        assert forbidden not in response.text.lower()


def test_openapi_exposes_same_origin_server_and_stable_operation_ids() -> None:
    """The F2 health seam must remain same-origin and generator-safe."""
    schema = create_app(settings=_test_settings()).openapi()
    paths = schema["paths"]

    assert schema["servers"] == [{"url": "/", "description": "Same-origin API"}]
    assert paths["/api/v1/health/live"]["get"]["operationId"] == "health_live"
    assert paths["/api/v1/health/ready"]["get"]["operationId"] == "health_ready"
    assert (
        paths["/api/v1/health/live"]["get"]["responses"]["200"]["headers"]["Cache-Control"][
            "schema"
        ]["example"]
        == "no-store"
    )
    admin_health = paths["/api/v1/admin/health"]["get"]
    assert admin_health["operationId"] == "admin_health_get"
    assert admin_health["security"] == [{"AdminSessionCookie": []}]
    assert set(admin_health["responses"]) == {"200", "401", "403", "500", "503"}
    assert (
        admin_health["responses"]["200"]["headers"]["Cache-Control"]["schema"]["example"]
        == "private, no-store"
    )
    assert schema["openapi"].startswith("3.")
