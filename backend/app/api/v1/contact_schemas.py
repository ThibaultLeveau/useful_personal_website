"""Public and private contact API contracts."""
# ruff: noqa: D101

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.api.v1.schemas import ApiModel


class ContactFormContextData(ApiModel):
    policy_version: str
    source: str
    issued_at: int
    proof: str


class ContactSubmitRequest(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    subject: str = Field(min_length=1, max_length=180)
    message: str = Field(min_length=1, max_length=5000)
    consent: bool
    policy_version: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=40)
    issued_at: int
    proof: str = Field(min_length=64, max_length=64)
    website: str = Field(default="", max_length=200)


class ContactAcceptedData(ApiModel):
    status: Literal["accepted"] = "accepted"


class ContactSummaryData(ApiModel):
    id: UUID
    name: str
    email: str
    subject: str
    state: Literal["unread", "read", "archived"]
    created_at: datetime
    version: int


class ContactDetailData(ContactSummaryData):
    message: str
    consented_at: datetime
    policy_version: str
    source: str
    read_at: datetime | None
    archived_at: datetime | None
    updated_at: datetime


class ContactTransitionRequest(ApiModel):
    state: Literal["read", "archived"]
