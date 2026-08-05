"""API access token domain and cryptographic contract tests."""

# ruff: noqa: D103
import hmac
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.api_access.domain import (
    ApiTokenScope,
    ApiTokenValidationError,
    normalize_token_name,
    validate_expiry,
)
from app.modules.api_access.security import digest_api_token, issue_api_token, parse_api_token


def test_issued_token_has_exact_format_and_digest_only_verification() -> None:
    pepper = b"unit-pepper-with-at-least-thirty-two-bytes"
    issued = issue_api_token(pepper)
    parsed = parse_api_token(issued.plaintext)
    assert parsed is not None
    public_id, secret = parsed
    assert public_id == issued.public_id
    assert len(issued.plaintext) == 74
    assert len(issued.digest) == 32
    assert hmac.compare_digest(issued.digest, digest_api_token(pepper, public_id, secret))


def test_malformed_token_never_parses() -> None:
    assert parse_api_token("pp_live_short.secret") is None
    assert parse_api_token("Bearer pp_live_invalid") is None


def test_name_and_expiry_are_bounded() -> None:
    now = datetime(2026, 8, 4, tzinfo=UTC)
    assert normalize_token_name("  CI   publisher ") == "CI publisher"
    validate_expiry(now + timedelta(days=365), now=now, confirm_no_expiry=False)
    with pytest.raises(ApiTokenValidationError):
        validate_expiry(None, now=now, confirm_no_expiry=False)
    with pytest.raises(ApiTokenValidationError):
        validate_expiry(now + timedelta(days=366), now=now, confirm_no_expiry=False)


def test_normative_scope_catalog_is_exact() -> None:
    assert {item.value for item in ApiTokenScope} == {
        "content:read",
        "content:write",
        "media:read",
        "media:write",
        "contacts:read",
        "admin:read",
    }
