"""Explicit authentication request and response contracts."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves this type at runtime.
from typing import Literal
from uuid import UUID  # noqa: TC003 - Pydantic resolves this type at runtime.

from pydantic import Field

from app.api.v1.schemas import ApiModel


class LoginRequest(ApiModel):
    """Non-enumerating administrator login input."""

    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1_024)


class ChangePasswordRequest(ApiModel):
    """Current and replacement password input."""

    current_password: str = Field(min_length=1, max_length=1_024)
    new_password: str = Field(min_length=1, max_length=1_024)


class SessionData(ApiModel):
    """Safe browser session state; no opaque secret or email is returned."""

    administrator_id: UUID
    display_name: str
    must_change_password: bool
    idle_expires_at: datetime
    absolute_expires_at: datetime


class AuthActionData(ApiModel):
    """Stable result for a completed authentication action."""

    status: Literal["logged_out"]
