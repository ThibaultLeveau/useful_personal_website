"""Tests for typed settings and production-safe validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import SecretStr, ValidationError

from app.config import (
    Environment,
    LogLevel,
    MediaStorageAuthSource,
    MediaStorageEncryption,
    MediaStorageKind,
    Settings,
)

if TYPE_CHECKING:
    from pathlib import Path

_SECURE_VALUE = "5f7c2be6798d421a8702d6581ed9bfa3"


def _production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.PRODUCTION,
        "database_url": SecretStr(
            "postgresql+asyncpg://portfolio_app:92vX7qLm4cNa6rTu@db/portfolio"
        ),
        "csrf_signing_key": SecretStr(_SECURE_VALUE),
        "token_digest_pepper": SecretStr(f"a{_SECURE_VALUE}"),
        "privacy_hmac_key": SecretStr(f"b{_SECURE_VALUE}"),
        "trusted_origins": ("https://portfolio.example",),
        "media_storage_kind": MediaStorageKind.S3_COMPATIBLE,
        "media_s3_endpoint_url": "https://objects.example.test",
        "media_s3_region": "eu-test-1",
        "media_s3_bucket": "private-portfolio-media",
        "media_s3_managed_prefix": "portfolio/media/",
        "media_s3_auth_source": MediaStorageAuthSource.WORKLOAD_IDENTITY,
        "media_s3_encryption": MediaStorageEncryption.AES256,
        "media_s3_connect_timeout_seconds": 2.0,
        "media_s3_read_timeout_seconds": 5.0,
        "contact_policy_version": "privacy-2026-08-approved",
        "contact_pseudonym_key_version": "contact-ip-2026-08",
        "token_digest_key_version": "api-token-2026-08",
    }
    values.update(overrides)
    return Settings.model_validate(values)


def test_development_defaults_are_non_debug_and_cors_disabled() -> None:
    """Development defaults must not silently enable debug or CORS."""
    settings = Settings()

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.debug is False
    assert settings.log_level is LogLevel.INFO
    assert settings.build_version == "0.0.0"
    assert settings.build_commit == "unknown"
    assert settings.trusted_origins == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("build_version", "unsafe version with spaces"),
        ("build_commit", "https://internal.example/repository"),
        ("build_commit", "ABCDEF1"),
    ],
)
def test_build_metadata_rejects_values_that_are_not_safe_to_disclose(
    field: str,
    value: str,
) -> None:
    """Admin health may expose only bounded, allow-listed build identifiers."""
    with pytest.raises(ValidationError):
        Settings.model_validate({field: value})


def test_valid_production_settings_are_accepted_and_secret_repr_is_masked() -> None:
    """Complete non-default production configuration should validate safely."""
    settings = _production_settings()

    rendered = repr(settings)
    assert settings.environment is Environment.PRODUCTION
    assert _SECURE_VALUE not in rendered
    assert "92vX7qLm4cNa6rTu" not in rendered


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"debug": True}, "debug mode is forbidden"),
        ({"database_url": None}, "database_url is required"),
        (
            {"database_url": SecretStr("postgresql+asyncpg://postgres:password@db/portfolio")},
            "default privileged username",
        ),
        ({"csrf_signing_key": SecretStr("short")}, "at least 32 bytes"),
        ({"trusted_origins": ()}, "at least one trusted_origin"),
        ({"trusted_origins": ("http://portfolio.example",)}, "exact HTTPS origins"),
        ({"trusted_origins": ("https://*.example",)}, "exact HTTPS origins"),
        ({"trusted_origins": ("https://portfolio.example/path",)}, "exact HTTPS origins"),
        ({"media_storage_kind": None}, "media_storage_kind is required"),
        ({"media_storage_kind": MediaStorageKind.LOCAL}, "forbidden in production"),
    ],
)
def test_production_rejects_insecure_configuration(
    overrides: dict[str, object],
    message: str,
) -> None:
    """Production must fail clearly instead of using insecure fallbacks."""
    with pytest.raises(ValidationError, match=message):
        _production_settings(**overrides)


def test_environment_namespace_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the documented APP namespace should populate settings."""
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("APP_DEBUG", "false")

    settings = Settings()

    assert settings.environment is Environment.TEST
    assert settings.debug is False


def test_empty_optional_storage_environment_values_are_ignored(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Compose may forward blank unselected S3 fields beside the local adapter."""
    monkeypatch.setenv("APP_MEDIA_STORAGE_KIND", "local")
    monkeypatch.setenv("APP_MEDIA_LOCAL_ROOT", str(tmp_path.resolve()))
    monkeypatch.setenv("APP_MEDIA_S3_AUTH_SOURCE", "")
    monkeypatch.setenv("APP_MEDIA_S3_ENCRYPTION", "")
    monkeypatch.setenv("APP_MEDIA_S3_CONNECT_TIMEOUT_SECONDS", "")
    monkeypatch.setenv("APP_MEDIA_S3_READ_TIMEOUT_SECONDS", "")

    settings = Settings()

    assert settings.media_storage_kind is MediaStorageKind.LOCAL
    assert settings.media_s3_auth_source is None
    assert settings.media_s3_connect_timeout_seconds is None
