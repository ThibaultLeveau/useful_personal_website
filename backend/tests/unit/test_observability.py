"""Tests for structured logging and sensitive-field redaction."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from app.common.observability import REDACTED, configure_logging, get_logger
from app.config import LogLevel

if TYPE_CHECKING:
    import pytest


def test_structured_logger_redacts_nested_sensitive_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Sensitive values must be removed before the JSON renderer sees them."""
    configure_logging(LogLevel.INFO)
    logger = get_logger()

    logger.info(
        "security.redaction_test",
        authorization="Bearer private-token",
        nested={"email": "person@example.test", "safe_id": "resource-123"},
        password="private-password",
    )

    event = json.loads(capsys.readouterr().out.strip())
    assert event["event"] == "security.redaction_test"
    assert event["authorization"] == REDACTED
    assert event["password"] == REDACTED
    assert event["nested"] == {"email": REDACTED, "safe_id": "resource-123"}
    assert "private-token" not in json.dumps(event)
    assert "person@example.test" not in json.dumps(event)
