"""M3 profile, settings, navigation, and public-boundary unit contracts."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.api.v1.public_site_configuration import (
    _public_footer_data,
    _public_navigation_data,
    _public_profile_data,
)
from app.api.v1.site_configuration_schemas import (
    ProfileUpdateRequest,
    SocialLinkInput,
    WebsiteSettingsUpdateRequest,
)
from app.modules.navigation.domain import (
    FooterColumn,
    FooterItem,
    FooterItemKind,
    FooterTree,
    LinkKind,
    LinkTarget,
    NavigationItem,
    NavigationTree,
    TreeValidationError,
    public_footer,
    public_navigation,
    validate_footer,
    validate_navigation,
)
from app.modules.profile.domain import (
    ContactPreference,
    ProfileSnapshot,
    PublicProfileField,
    SocialLink,
    public_profile,
)
from app.modules.settings.domain import AnalyticsProvider

if TYPE_CHECKING:
    from collections.abc import Callable

NOW = datetime(2026, 8, 3, tzinfo=UTC)
MENU_ID = UUID("00000000-0000-7000-8000-000000000301")
ROOT_ID = UUID("00000000-0000-7000-8000-000000000302")
CHILD_ID = UUID("00000000-0000-7000-8000-000000000303")
OTHER_ID = UUID("00000000-0000-7000-8000-000000000304")
FOOTER_ID = UUID("00000000-0000-7000-8000-000000000305")
COLUMN_ID = UUID("00000000-0000-7000-8000-000000000306")


def _profile(*, public_fields: frozenset[PublicProfileField]) -> ProfileSnapshot:
    return ProfileSnapshot(
        id=ROOT_ID,
        full_name="Public Name",
        professional_title="Private title",
        short_biography="Private short biography",
        full_biography="Private full biography",
        profile_image_id=None,
        location="Private location",
        availability="Private availability",
        email="private@example.test",
        social_links=(SocialLink(label="Example", url="https://example.test/profile"),),
        github_url="https://github.com/example",
        linkedin_url="https://www.linkedin.com/in/example",
        personal_values=("Privacy",),
        work_preferences=("Remote",),
        resume_url="https://example.test/resume.pdf",
        contact_preference=ContactPreference.EMAIL,
        public_fields=public_fields,
        created_at=NOW,
        updated_at=NOW,
        version=1,
    )


def _item(
    identifier: UUID,
    *,
    parent_id: UUID | None = None,
    position: int = 0,
    href: str = "/",
    visible: bool = True,
) -> NavigationItem:
    return NavigationItem(
        id=identifier,
        parent_id=parent_id,
        label="Destination",
        link_kind=LinkKind.INTERNAL,
        href=href,
        target=LinkTarget.SAME_WINDOW,
        visible=visible,
        position=position,
    )


def _footer_item(
    identifier: UUID,
    *,
    position: int = 0,
    href: str = "/about",
    visible: bool = True,
) -> FooterItem:
    return FooterItem(
        id=identifier,
        label="Footer destination",
        link_kind=LinkKind.INTERNAL,
        item_kind=FooterItemKind.LINK,
        href=href,
        target=LinkTarget.SAME_WINDOW,
        visible=visible,
        position=position,
    )


def test_profile_projection_requires_explicit_field_approval_and_omits_private_values() -> None:
    """A single approved field must not carry adjacent admin values into JSON."""
    projection = public_profile(_profile(public_fields=frozenset({PublicProfileField.FULL_NAME})))
    payload = _public_profile_data(projection).model_dump(exclude_none=True, mode="json")

    assert payload == {"configured": True, "full_name": "Public Name"}
    serialized = str(payload)
    assert "Private" not in serialized
    assert "private@example.test" not in serialized


def test_unconfigured_profile_has_only_an_explicit_empty_state() -> None:
    """With no publication decisions, no stored value is serializable."""
    payload = _public_profile_data(public_profile(_profile(public_fields=frozenset()))).model_dump(
        exclude_none=True, mode="json"
    )

    assert payload == {"configured": False}


@pytest.mark.parametrize(
    "extra_field",
    [
        "database_url",
        "private_key",
        "analytics_secret",
        "arbitrary_script",
        "storage_key",
    ],
)
def test_settings_reject_secret_capable_mass_assignment(extra_field: str) -> None:
    """Unknown secret-shaped inputs never become ordinary website settings."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WebsiteSettingsUpdateRequest.model_validate({extra_field: "must-not-be-accepted"})


@pytest.mark.parametrize(
    ("provider", "identifier"),
    [
        (AnalyticsProvider.NONE, "G-ABCDEF"),
        (AnalyticsProvider.PLAUSIBLE, "not a domain"),
        (AnalyticsProvider.GOOGLE_ANALYTICS, "UA-secret-shaped"),
    ],
)
def test_settings_reject_invalid_analytics_pairs(
    provider: AnalyticsProvider,
    identifier: str,
) -> None:
    """Only allow-listed provider-specific public identifiers are accepted."""
    with pytest.raises(ValidationError):
        WebsiteSettingsUpdateRequest(
            analytics_provider=provider,
            analytics_public_id=identifier,
        )


def test_settings_normalize_colors_and_validate_locale_timezone() -> None:
    """Portable locale/timezone values and canonical color tokens cross the API."""
    settings = WebsiteSettingsUpdateRequest(
        default_locale="fr-FR",
        timezone="Europe/Paris",
        primary_color="#a1b2c3",
    )
    assert settings.primary_color == "#A1B2C3"

    with pytest.raises(ValidationError):
        WebsiteSettingsUpdateRequest(default_locale="not_a_locale")
    with pytest.raises(ValidationError):
        WebsiteSettingsUpdateRequest(timezone="Mars/Olympus")


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,unsafe",
        "//example.test/path",
        "http://example.test/path",
        "https://user:password@example.test/path",
        "https://example.test/path#fragment",
        " https://example.test/path",
        "https://example.test/path\\escape",
        "https://example.test/path\nother",
    ],
)
def test_social_links_reject_unsafe_or_noncanonical_urls(url: str) -> None:
    """Public social links use canonical credential-free HTTPS only."""
    with pytest.raises(ValidationError):
        SocialLinkInput(label="Example", url=url)


def test_navigation_accepts_registered_two_level_tree_and_external_new_window() -> None:
    """The valid boundary includes registered routes and safe HTTPS targets."""
    items = (
        _item(ROOT_ID),
        _item(CHILD_ID, parent_id=ROOT_ID, href="/about"),
        replace(
            _item(OTHER_ID, position=1),
            href="https://example.test/work",
            link_kind=LinkKind.EXTERNAL,
            target=LinkTarget.NEW_WINDOW,
        ),
    )
    validate_navigation(items)


@pytest.mark.parametrize(
    "items",
    [
        (_item(ROOT_ID), _item(ROOT_ID, position=1)),
        (_item(ROOT_ID, parent_id=ROOT_ID),),
        (_item(ROOT_ID, parent_id=OTHER_ID),),
        (_item(ROOT_ID, position=1),),
        (_item(ROOT_ID, href="/not-registered"),),
        (replace(_item(ROOT_ID), target=LinkTarget.NEW_WINDOW),),
        (
            replace(
                _item(ROOT_ID),
                href="javascript:alert(1)",
                link_kind=LinkKind.EXTERNAL,
            ),
        ),
        (
            _item(ROOT_ID, parent_id=CHILD_ID),
            _item(CHILD_ID, parent_id=ROOT_ID),
        ),
    ],
)
def test_navigation_rejects_duplicate_parent_order_route_link_and_cycle_faults(
    items: tuple[NavigationItem, ...],
) -> None:
    """Every malformed tree fails before persistence can partially replace it."""
    with pytest.raises(TreeValidationError):
        validate_navigation(items)


def test_public_navigation_drops_hidden_roots_children_and_edit_state() -> None:
    """A hidden parent removes its subtree and public JSON has no edit metadata."""
    tree = NavigationTree(
        id=MENU_ID,
        items=(
            _item(ROOT_ID, visible=False),
            _item(CHILD_ID, parent_id=ROOT_ID),
            _item(OTHER_ID, position=1, href="/about"),
        ),
        version=7,
    )
    payload = _public_navigation_data(public_navigation(tree)).model_dump(mode="json")

    assert len(payload["items"]) == 1
    assert payload["items"][0]["key"] == str(OTHER_ID)
    assert "visible" not in str(payload)
    assert "version" not in str(payload)


def test_footer_validates_visibility_order_and_projects_public_shape() -> None:
    """Hidden footer content and editor-only fields never reach public JSON."""
    visible = FooterColumn(
        id=COLUMN_ID,
        title="Explore",
        visible=True,
        position=0,
        items=(
            _footer_item(ROOT_ID),
            _footer_item(CHILD_ID, position=1, visible=False),
        ),
    )
    hidden = FooterColumn(
        id=OTHER_ID,
        title="Hidden",
        visible=False,
        position=1,
        items=(_footer_item(OTHER_ID),),
    )
    validate_footer((visible, hidden))
    projected = public_footer(
        FooterTree(
            id=FOOTER_ID,
            copyright_text="Fictional copyright",
            columns=(visible, hidden),
            version=3,
        )
    )
    payload = _public_footer_data(projected).model_dump(mode="json")

    assert payload["columns"] == [
        {
            "title": "Explore",
            "items": [
                {
                    "label": "Footer destination",
                    "item_kind": "link",
                    "href": "/about",
                    "target": "same_window",
                }
            ],
        }
    ]
    assert "visible" not in str(payload)
    assert "version" not in str(payload)


@pytest.mark.parametrize(
    "columns_factory",
    [
        lambda: (
            FooterColumn(
                id=COLUMN_ID,
                title="Empty",
                visible=True,
                position=0,
                items=(),
            ),
        ),
        lambda: (
            FooterColumn(
                id=COLUMN_ID,
                title="Gap",
                visible=True,
                position=1,
                items=(_footer_item(ROOT_ID),),
            ),
        ),
    ],
)
def test_footer_rejects_empty_visible_columns_and_order_gaps(
    columns_factory: Callable[[], tuple[FooterColumn, ...]],
) -> None:
    """Invalid complete footer inputs fail deterministically."""
    with pytest.raises(TreeValidationError):
        validate_footer(columns_factory())


def test_profile_update_rejects_unlisted_fields_and_duplicate_public_values() -> None:
    """Profile mutations reject mass assignment and ambiguous ordered values."""
    with pytest.raises(ValidationError):
        ProfileUpdateRequest.model_validate({"password": "not-a-profile-field"})
    with pytest.raises(ValidationError):
        ProfileUpdateRequest(personal_values=["Privacy", "Privacy"])
