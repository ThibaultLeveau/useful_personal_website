"""Relational persistence for profile, settings, navigation, and footer."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves runtime annotations.
from uuid import UUID  # noqa: TC003 - SQLAlchemy resolves runtime annotations.

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SiteConfigurationBase(DeclarativeBase):
    """SQLAlchemy registry for the M3 site-configuration slice."""


class ProfileRecord(SiteConfigurationBase):
    """The single administrator-owned profile and explicit publication policy."""

    __tablename__ = "profile"
    __table_args__ = (
        CheckConstraint("singleton_key = 1", name="profile_singleton_key"),
        CheckConstraint("version > 0", name="profile_positive_version"),
        UniqueConstraint("singleton_key", name="uq_profile_singleton"),
        ForeignKeyConstraint(
            ["profile_image_id"],
            ["media_asset.id"],
            name="fk_profile_image_media_asset",
            ondelete="RESTRICT",
            use_alter=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    singleton_key: Mapped[int] = mapped_column(SmallInteger, default=1)
    full_name: Mapped[str | None] = mapped_column(String(160))
    professional_title: Mapped[str | None] = mapped_column(String(160))
    short_biography: Mapped[str | None] = mapped_column(Text)
    full_biography: Mapped[str | None] = mapped_column(Text)
    profile_image_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    location: Mapped[str | None] = mapped_column(String(160))
    availability: Mapped[str | None] = mapped_column(String(240))
    email: Mapped[str | None] = mapped_column(String(320))
    social_links: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    github_url: Mapped[str | None] = mapped_column(String(2048))
    linkedin_url: Mapped[str | None] = mapped_column(String(2048))
    personal_values: Mapped[list[str]] = mapped_column(JSONB, default=list)
    work_preferences: Mapped[list[str]] = mapped_column(JSONB, default=list)
    resume_url: Mapped[str | None] = mapped_column(String(2048))
    contact_preference: Mapped[str] = mapped_column(String(24), default="none")
    public_fields: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class WebsiteSettingsRecord(SiteConfigurationBase):
    """The single non-secret website configuration record."""

    __tablename__ = "website_settings"
    __table_args__ = (
        CheckConstraint("singleton_key = 1", name="website_settings_singleton_key"),
        CheckConstraint("version > 0", name="website_settings_positive_version"),
        UniqueConstraint("singleton_key", name="uq_website_settings_singleton"),
        ForeignKeyConstraint(
            ["logo_media_id"],
            ["media_asset.id"],
            name="fk_website_settings_logo_media_asset",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["favicon_media_id"],
            ["media_asset.id"],
            name="fk_website_settings_favicon_media_asset",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["social_image_media_id"],
            ["media_asset.id"],
            name="fk_website_settings_social_image_media_asset",
            ondelete="RESTRICT",
            use_alter=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    singleton_key: Mapped[int] = mapped_column(SmallInteger, default=1)
    website_name: Mapped[str | None] = mapped_column(String(120))
    default_title: Mapped[str | None] = mapped_column(String(160))
    default_description: Mapped[str | None] = mapped_column(String(320))
    logo_media_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    favicon_media_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    social_image_media_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    default_locale: Mapped[str] = mapped_column(String(35), default="en")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    theme_policy: Mapped[str] = mapped_column(String(16), default="system")
    primary_color: Mapped[str | None] = mapped_column(String(7))
    accent_color: Mapped[str | None] = mapped_column(String(7))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    social_links: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    seo_title_suffix: Mapped[str | None] = mapped_column(String(80))
    seo_description: Mapped[str | None] = mapped_column(String(320))
    analytics_provider: Mapped[str] = mapped_column(String(32), default="none")
    analytics_public_id: Mapped[str | None] = mapped_column(String(80))
    public_availability: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class NavigationMenuRecord(SiteConfigurationBase):
    """The primary navigation aggregate root."""

    __tablename__ = "navigation_menu"
    __table_args__ = (
        CheckConstraint("singleton_key = 1", name="navigation_menu_singleton_key"),
        CheckConstraint("version > 0", name="navigation_menu_positive_version"),
        UniqueConstraint("singleton_key", name="uq_navigation_menu_singleton"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    singleton_key: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class NavigationItemRecord(SiteConfigurationBase):
    """One ordered, at-most-two-level navigation destination."""

    __tablename__ = "navigation_item"
    __table_args__ = (
        CheckConstraint("parent_id IS NULL OR parent_id <> id", name="navigation_item_not_self"),
        CheckConstraint("position >= 0", name="navigation_item_nonnegative_position"),
        CheckConstraint("version > 0", name="navigation_item_positive_version"),
        CheckConstraint(
            "link_kind IN ('internal', 'external')",
            name="navigation_item_link_kind_catalog",
        ),
        CheckConstraint(
            "target IN ('same_window', 'new_window')",
            name="navigation_item_target_catalog",
        ),
        UniqueConstraint(
            "menu_id",
            "parent_id",
            "position",
            name="uq_navigation_item_child_position",
        ),
        Index(
            "uq_navigation_item_root_position",
            "menu_id",
            "position",
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
        Index("ix_navigation_item_menu_parent", "menu_id", "parent_id", "position", "id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    menu_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("navigation_menu.id", ondelete="CASCADE"),
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("navigation_item.id", ondelete="CASCADE"),
    )
    label: Mapped[str] = mapped_column(String(80))
    link_kind: Mapped[str] = mapped_column(String(16))
    href: Mapped[str] = mapped_column(String(2048))
    target: Mapped[str] = mapped_column(String(16))
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class FooterRecord(SiteConfigurationBase):
    """The singleton footer aggregate root."""

    __tablename__ = "footer"
    __table_args__ = (
        CheckConstraint("singleton_key = 1", name="footer_singleton_key"),
        CheckConstraint("version > 0", name="footer_positive_version"),
        UniqueConstraint("singleton_key", name="uq_footer_singleton"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    singleton_key: Mapped[int] = mapped_column(SmallInteger, default=1)
    copyright_text: Mapped[str | None] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class FooterColumnRecord(SiteConfigurationBase):
    """One deterministic footer column."""

    __tablename__ = "footer_column"
    __table_args__ = (
        CheckConstraint("position >= 0", name="footer_column_nonnegative_position"),
        CheckConstraint("version > 0", name="footer_column_positive_version"),
        UniqueConstraint("footer_id", "position", name="uq_footer_column_position"),
        Index("ix_footer_column_footer_position", "footer_id", "position", "id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    footer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("footer.id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(80))
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)


class FooterItemRecord(SiteConfigurationBase):
    """One ordered normal, social, or legal footer destination."""

    __tablename__ = "footer_item"
    __table_args__ = (
        CheckConstraint("position >= 0", name="footer_item_nonnegative_position"),
        CheckConstraint("version > 0", name="footer_item_positive_version"),
        CheckConstraint(
            "link_kind IN ('internal', 'external')",
            name="footer_item_link_kind_catalog",
        ),
        CheckConstraint(
            "target IN ('same_window', 'new_window')",
            name="footer_item_target_catalog",
        ),
        CheckConstraint(
            "item_kind IN ('link', 'social', 'legal')",
            name="footer_item_kind_catalog",
        ),
        UniqueConstraint("column_id", "position", name="uq_footer_item_position"),
        Index("ix_footer_item_column_position", "column_id", "position", "id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    column_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("footer_column.id", ondelete="CASCADE"),
    )
    label: Mapped[str] = mapped_column(String(80))
    link_kind: Mapped[str] = mapped_column(String(16))
    item_kind: Mapped[str] = mapped_column(String(16))
    href: Mapped[str] = mapped_column(String(2048))
    target: Mapped[str] = mapped_column(String(16))
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
