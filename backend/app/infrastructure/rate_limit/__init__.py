"""PostgreSQL-backed rate-limit adapter."""

from app.infrastructure.rate_limit.persistence import RateLimitRepository

__all__ = ["RateLimitRepository"]
