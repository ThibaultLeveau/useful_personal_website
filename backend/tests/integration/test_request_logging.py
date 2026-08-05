"""Tests for correlated, structured, and non-reflective request logs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from app.config import Environment, Settings
from app.main import create_app

if TYPE_CHECKING:
    import pytest


async def test_request_log_uses_route_template_and_omits_query_secret(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Request logging must never copy the raw URL or query values."""
    request_id = "edge-request-id-000000000001"
    application = create_app(settings=Settings(environment=Environment.TEST))
    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/health/live",
            headers={"X-Request-ID": request_id},
            params={"token": "private-query-token"},
        )

    log_lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    events = [json.loads(line) for line in log_lines]
    request_event = next(event for event in events if event.get("event") == "request.completed")
    serialized = json.dumps(request_event)
    assert response.status_code == 200
    assert request_event["request_id"] == request_id
    assert request_event["route"] == "/api/v1/health/live"
    assert request_event["status"] == 200
    assert "private-query-token" not in serialized
    assert "?token" not in serialized
