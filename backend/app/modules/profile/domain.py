"""Persistence-neutral profile values and explicit public projection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class ContactPreference(StrEnum):
    """Public contact channels selected by the administrator."""

    NONE = "none"
    EMAIL = "email"
    SOCIAL = "social"
    EMAIL_AND_SOCIAL = "email_and_social"


class PublicProfileField(StrEnum):
    """Every profile value requires an explicit publication decision."""

    FULL_NAME = "full_name"
    PROFESSIONAL_TITLE = "professional_title"
    SHORT_BIOGRAPHY = "short_biography"
    FULL_BIOGRAPHY = "full_biography"
    LOCATION = "location"
    AVAILABILITY = "availability"
    EMAIL = "email"
    SOCIAL_LINKS = "social_links"
    GITHUB_URL = "github_url"
    LINKEDIN_URL = "linkedin_url"
    PERSONAL_VALUES = "personal_values"
    WORK_PREFERENCES = "work_preferences"
    RESUME_URL = "resume_url"
    CONTACT_PREFERENCE = "contact_preference"


@dataclass(frozen=True, slots=True)
class SocialLink:
    """A labelled HTTPS social profile."""

    label: str
    url: str


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    """Complete administrator profile state."""

    id: UUID
    full_name: str | None
    professional_title: str | None
    short_biography: str | None
    full_biography: str | None
    profile_image_id: UUID | None
    location: str | None
    availability: str | None
    email: str | None
    social_links: tuple[SocialLink, ...]
    github_url: str | None
    linkedin_url: str | None
    personal_values: tuple[str, ...]
    work_preferences: tuple[str, ...]
    resume_url: str | None
    contact_preference: ContactPreference
    public_fields: frozenset[PublicProfileField]
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class ProfileValues:
    """Validated replacement values for the singleton profile."""

    full_name: str | None
    professional_title: str | None
    short_biography: str | None
    full_biography: str | None
    profile_image_id: UUID | None
    location: str | None
    availability: str | None
    email: str | None
    social_links: tuple[SocialLink, ...]
    github_url: str | None
    linkedin_url: str | None
    personal_values: tuple[str, ...]
    work_preferences: tuple[str, ...]
    resume_url: str | None
    contact_preference: ContactPreference
    public_fields: frozenset[PublicProfileField]


@dataclass(frozen=True, slots=True)
class PublicProfile:
    """Allow-list projection; unapproved properties remain absent at transport."""

    full_name: str | None = None
    professional_title: str | None = None
    short_biography: str | None = None
    full_biography: str | None = None
    profile_image_id: UUID | None = None
    location: str | None = None
    availability: str | None = None
    email: str | None = None
    social_links: tuple[SocialLink, ...] | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    personal_values: tuple[str, ...] | None = None
    work_preferences: tuple[str, ...] | None = None
    resume_url: str | None = None
    contact_preference: ContactPreference | None = None


def public_profile(snapshot: ProfileSnapshot) -> PublicProfile:
    """Build a public allow-list without serializing the administrator shape."""
    allowed = snapshot.public_fields
    return PublicProfile(
        full_name=snapshot.full_name if PublicProfileField.FULL_NAME in allowed else None,
        professional_title=(
            snapshot.professional_title
            if PublicProfileField.PROFESSIONAL_TITLE in allowed
            else None
        ),
        short_biography=(
            snapshot.short_biography if PublicProfileField.SHORT_BIOGRAPHY in allowed else None
        ),
        full_biography=(
            snapshot.full_biography if PublicProfileField.FULL_BIOGRAPHY in allowed else None
        ),
        profile_image_id=snapshot.profile_image_id,
        location=snapshot.location if PublicProfileField.LOCATION in allowed else None,
        availability=(
            snapshot.availability if PublicProfileField.AVAILABILITY in allowed else None
        ),
        email=snapshot.email if PublicProfileField.EMAIL in allowed else None,
        social_links=(
            snapshot.social_links if PublicProfileField.SOCIAL_LINKS in allowed else None
        ),
        github_url=(snapshot.github_url if PublicProfileField.GITHUB_URL in allowed else None),
        linkedin_url=(
            snapshot.linkedin_url if PublicProfileField.LINKEDIN_URL in allowed else None
        ),
        personal_values=(
            snapshot.personal_values if PublicProfileField.PERSONAL_VALUES in allowed else None
        ),
        work_preferences=(
            snapshot.work_preferences if PublicProfileField.WORK_PREFERENCES in allowed else None
        ),
        resume_url=snapshot.resume_url if PublicProfileField.RESUME_URL in allowed else None,
        contact_preference=(
            snapshot.contact_preference
            if PublicProfileField.CONTACT_PREFERENCE in allowed
            else None
        ),
    )
