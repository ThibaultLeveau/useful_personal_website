"""Typed deployment configuration and secure environment validation."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path  # noqa: TC003 - Pydantic resolves field types at runtime.
from typing import Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MINIMUM_SECRET_BYTES = 32
_DISALLOWED_SECRET_MARKERS = (
    "changeme",
    "default",
    "example",
    "password",
    "replace-me",
    "secret",
)
_DISALLOWED_DATABASE_USERS = frozenset({"admin", "postgres", "root", "user"})


class Environment(StrEnum):
    """Supported application runtime environments."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Allow-listed application log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MediaStorageKind(StrEnum):
    """Closed private media storage adapters."""

    LOCAL = "local"
    S3_COMPATIBLE = "s3_compatible"


class MediaStorageAuthSource(StrEnum):
    """Credential discovery modes that keep secrets outside settings."""

    WORKLOAD_IDENTITY = "workload_identity"
    ENVIRONMENT = "environment"


class MediaStorageEncryption(StrEnum):
    """Provider-side encryption modes accepted by the S3 adapter."""

    AES256 = "AES256"
    KMS = "aws:kms"


class Settings(BaseSettings):
    """Application settings loaded from the `APP_` environment namespace."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="APP_",
        env_ignore_empty=True,
        extra="ignore",
        frozen=True,
    )

    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    build_version: str = Field(default="0.0.0", pattern=r"^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$")
    build_commit: str = Field(default="unknown", pattern=r"^(?:unknown|[0-9a-f]{7,64})$")
    trusted_origins: tuple[str, ...] = ()
    database_url: SecretStr | None = None
    audit_retention_database_url: SecretStr | None = None
    audit_retention_days: int = Field(default=400, ge=7, le=3650)
    csrf_signing_key: SecretStr | None = None
    token_digest_pepper: SecretStr | None = None
    token_digest_key_version: str = Field(default="development-v1", min_length=1, max_length=40)
    privacy_hmac_key: SecretStr | None = None
    media_storage_kind: MediaStorageKind | None = None
    media_local_root: Path | None = None
    media_local_production_acknowledged: bool = False
    media_s3_endpoint_url: str | None = None
    media_s3_region: str | None = None
    media_s3_bucket: str | None = None
    media_s3_managed_prefix: str | None = None
    media_s3_auth_source: MediaStorageAuthSource | None = None
    media_s3_encryption: MediaStorageEncryption | None = None
    media_s3_kms_key_id: str | None = None
    media_s3_connect_timeout_seconds: float | None = None
    media_s3_read_timeout_seconds: float | None = None
    contact_policy_version: str = Field(
        default="development-policy-v1", min_length=1, max_length=80
    )
    contact_source: str = Field(default="contact_page", pattern=r"^[a-z][a-z0-9_]{0,39}$")
    contact_minimum_completion_seconds: int = Field(default=2, ge=1, le=60)
    contact_proof_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    contact_pseudonym_key_version: str = Field(
        default="development-v1", min_length=1, max_length=40
    )
    contact_retention_days: int = Field(default=365, ge=30, le=3650)

    @model_validator(mode="after")
    def validate_secure_environment(self) -> Self:
        """Reject insecure production configuration instead of falling back."""
        self._validate_media_configuration()
        if self.environment is not Environment.PRODUCTION:
            return self

        if self.debug:
            msg = "debug mode is forbidden in production"
            raise ValueError(msg)

        self._validate_database_url()
        if (
            self.audit_retention_database_url is not None
            and self.database_url is not None
            and self.audit_retention_database_url.get_secret_value()
            == self.database_url.get_secret_value()
        ):
            msg = "audit retention must use a credential distinct from the runtime database URL"
            raise ValueError(msg)
        self._validate_secret("csrf_signing_key", self.csrf_signing_key)
        self._validate_secret("token_digest_pepper", self.token_digest_pepper)
        self._validate_secret("privacy_hmac_key", self.privacy_hmac_key)
        self._validate_trusted_origins()
        if self.contact_policy_version.startswith(
            "development-"
        ) or self.contact_pseudonym_key_version.startswith("development-"):
            msg = "production contact policy and pseudonym-key versions must be explicitly approved"
            raise ValueError(msg)
        if self.token_digest_key_version.startswith("development-"):
            msg = "production token digest key version must be explicitly configured"
            raise ValueError(msg)
        return self

    def _validate_media_configuration(self) -> None:
        if self.media_storage_kind is None:
            if self.environment is Environment.PRODUCTION:
                msg = "media_storage_kind is required in production"
                raise ValueError(msg)
            return
        if self.media_storage_kind is MediaStorageKind.LOCAL:
            if self.media_local_root is None or not self.media_local_root.is_absolute():
                msg = "media_local_root must be an explicit absolute path"
                raise ValueError(msg)
            if (
                self.environment is Environment.PRODUCTION
                and not self.media_local_production_acknowledged
            ):
                msg = "production local media storage must be explicitly acknowledged"
                raise ValueError(msg)
            return
        required = {
            "media_s3_endpoint_url": self.media_s3_endpoint_url,
            "media_s3_region": self.media_s3_region,
            "media_s3_bucket": self.media_s3_bucket,
            "media_s3_managed_prefix": self.media_s3_managed_prefix,
            "media_s3_auth_source": self.media_s3_auth_source,
            "media_s3_encryption": self.media_s3_encryption,
            "media_s3_connect_timeout_seconds": self.media_s3_connect_timeout_seconds,
            "media_s3_read_timeout_seconds": self.media_s3_read_timeout_seconds,
        }
        missing = next((name for name, value in required.items() if value is None), None)
        if missing is not None:
            msg = f"{missing} is required for S3-compatible media storage"
            raise ValueError(msg)
        endpoint = urlsplit(self.media_s3_endpoint_url or "")
        if endpoint.scheme != "https" or not endpoint.hostname:
            msg = "media_s3_endpoint_url must use HTTPS"
            raise ValueError(msg)
        if (self.media_s3_encryption is MediaStorageEncryption.KMS) != bool(
            self.media_s3_kms_key_id
        ):
            msg = "media_s3_kms_key_id must match the selected encryption mode"
            raise ValueError(msg)
        if (self.media_s3_connect_timeout_seconds or 0) <= 0 or (
            self.media_s3_read_timeout_seconds or 0
        ) <= 0:
            msg = "media storage timeouts must be positive"
            raise ValueError(msg)

    def _validate_database_url(self) -> None:
        database_url = self.database_url
        if database_url is None:
            msg = "database_url is required in production"
            raise ValueError(msg)

        parsed = urlsplit(database_url.get_secret_value())
        if parsed.scheme != "postgresql+asyncpg" or not parsed.hostname:
            msg = "database_url must use postgresql+asyncpg with a hostname"
            raise ValueError(msg)
        if not parsed.username or not parsed.password or parsed.path in {"", "/"}:
            msg = "database_url must include non-default credentials and a database name"
            raise ValueError(msg)
        if parsed.username.casefold() in _DISALLOWED_DATABASE_USERS:
            msg = "database_url must not use a default privileged username"
            raise ValueError(msg)
        password = parsed.password.casefold()
        if any(marker in password for marker in _DISALLOWED_SECRET_MARKERS):
            msg = "database_url must not contain a predictable password"
            raise ValueError(msg)

    @staticmethod
    def _validate_secret(name: str, secret: SecretStr | None) -> None:
        if secret is None:
            msg = f"{name} is required in production"
            raise ValueError(msg)
        raw_secret = secret.get_secret_value()
        if len(raw_secret.encode()) < MINIMUM_SECRET_BYTES:
            msg = f"{name} must contain at least {MINIMUM_SECRET_BYTES} bytes"
            raise ValueError(msg)
        normalized = raw_secret.casefold()
        if any(marker in normalized for marker in _DISALLOWED_SECRET_MARKERS):
            msg = f"{name} must not contain a predictable marker"
            raise ValueError(msg)

    def _validate_trusted_origins(self) -> None:
        if not self.trusted_origins:
            msg = "at least one trusted_origin is required in production"
            raise ValueError(msg)
        if len(set(self.trusted_origins)) != len(self.trusted_origins):
            msg = "trusted_origins must not contain duplicates"
            raise ValueError(msg)

        for origin in self.trusted_origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                msg = "production trusted_origins must be exact HTTPS origins"
                raise ValueError(msg)
