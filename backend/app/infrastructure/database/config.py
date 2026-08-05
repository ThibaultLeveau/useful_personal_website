"""Validated PostgreSQL engine configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from pydantic import SecretStr


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Secret-safe async PostgreSQL connection and pool settings."""

    url: SecretStr
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout_seconds: float = 10.0
    pool_recycle_seconds: int = 1800

    def __post_init__(self) -> None:
        """Reject non-PostgreSQL URLs and invalid pool bounds."""
        parsed = urlsplit(self.url.get_secret_value())
        if parsed.scheme != "postgresql+asyncpg" or not parsed.hostname:
            msg = "database URL must use postgresql+asyncpg with a hostname"
            raise ValueError(msg)
        if parsed.path in {"", "/"}:
            msg = "database URL must name a database"
            raise ValueError(msg)
        if self.pool_size < 1:
            msg = "pool_size must be positive"
            raise ValueError(msg)
        if self.max_overflow < 0:
            msg = "max_overflow must not be negative"
            raise ValueError(msg)
        if self.pool_timeout_seconds <= 0 or self.pool_recycle_seconds <= 0:
            msg = "pool timeout and recycle values must be positive"
            raise ValueError(msg)
