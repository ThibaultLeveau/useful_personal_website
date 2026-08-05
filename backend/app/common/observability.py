"""Structured logging configuration and recursive sensitive-field redaction."""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

import structlog

if TYPE_CHECKING:
    from structlog.typing import EventDict, FilteringBoundLogger, WrappedLogger

    from app.config import LogLevel

REDACTED = "[REDACTED]"
_SENSITIVE_KEY_FRAGMENTS = (
    "authorization",
    "body",
    "cookie",
    "csrf",
    "email",
    "message",
    "password",
    "secret",
    "token",
)


def _is_sensitive_key(key: str) -> bool:
    return any(fragment in key.casefold() for fragment in _SENSITIVE_KEY_FRAGMENTS)


def _redact_value(value: object, *, key: str | None = None) -> object:
    if key is not None and _is_sensitive_key(key):
        return REDACTED
    if isinstance(value, Mapping):
        return {
            str(child_key): _redact_value(child_value, key=str(child_key))
            for child_key, child_value in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_redact_value(item) for item in value]
    return value


def redact_sensitive_fields(
    _logger: WrappedLogger,
    _method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Redact sensitive fields recursively before JSON serialization."""
    return {key: _redact_value(value, key=key) for key, value in event_dict.items()}


def configure_logging(log_level: LogLevel) -> None:
    """Configure deterministic JSON logs on stdout with safe library levels."""
    numeric_level = getattr(logging, log_level.value)
    logging.basicConfig(
        force=True,
        format="%(message)s",
        level=numeric_level,
        stream=sys.stdout,
    )
    for logger_name in ("httpcore", "httpx", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    logging.getLogger("app").disabled = False

    structlog.configure(
        cache_logger_on_first_use=False,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            redact_sensitive_fields,
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
    )


def get_logger() -> FilteringBoundLogger:
    """Return the typed application logger."""
    return cast("FilteringBoundLogger", structlog.get_logger("app"))
