"""Unit contracts for password, session, CSRF, and identity values."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from importlib.resources import files
from uuid import UUID

import pytest

from app.modules.identity.domain import SessionView, uuid7
from app.modules.identity.security import (
    ARGON2_MEMORY_KIB,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    PasswordManager,
    PasswordPolicyError,
    create_csrf_token,
    create_session_secret,
    digest_session_secret,
    digest_user_agent,
    keyed_pseudonym,
    verify_csrf_token,
)
from app.modules.identity.service import (
    AuthenticationRequiredError,
    IdentityService,
    PasswordChangeRequiredError,
    normalize_email,
)


@pytest.fixture(scope="module")
def password_manager() -> PasswordManager:
    """Create the expensive Argon2 policy once for focused unit tests."""
    return PasswordManager.create()


def test_argon2id_policy_hashes_and_verifies_without_plaintext(
    password_manager: PasswordManager,
) -> None:
    """The frozen policy must use the approved Argon2id cost floor."""
    password = "Correct horse battery staple! 2026"
    password_hash = password_manager.hash(password)

    assert password_hash.startswith("$argon2id$v=19$")
    assert f"m={ARGON2_MEMORY_KIB},t={ARGON2_TIME_COST},p={ARGON2_PARALLELISM}" in password_hash
    assert password not in password_hash
    assert password_manager.verify(password_hash, password) is True
    assert password_manager.verify(password_hash, "wrong password") is False
    assert password_manager.needs_rehash(password_hash) is False


@pytest.mark.parametrize(
    "password",
    [
        "  PaSs WoRd PaSs WoRd  ",
        "QWERTY QWERTY",
        "Welcome Welcome",
        "ADMIN admin ADMIN",
    ],
)
def test_versioned_offline_common_passwords_reject_normalized_variants(
    password_manager: PasswordManager,
    password: str,
) -> None:
    """Case/whitespace variants of catalog passwords remain blocked offline."""
    with pytest.raises(PasswordPolicyError, match="common-password blocklist"):
        password_manager.hash(password)


def test_common_password_catalog_has_immutable_reviewed_provenance() -> None:
    """The bundled offline subset is tied to one immutable upstream snapshot."""
    content = (
        files("app.modules.identity").joinpath("common_passwords.txt").read_text(encoding="utf-8")
    )
    assert "2d5dc7504a40962c53f932a6d9d5ece4b213dfc6" in content
    assert "780ebec6f93bd80aff2121c2644cf9e198ac1e361379ca73f28528fbcf044443" in content
    entries = [line for line in content.splitlines() if line and not line.startswith("#")]
    assert len(entries) == 115
    canonical_payload = ("\n".join(entries) + "\n").encode()
    assert hashlib.sha256(canonical_payload).hexdigest() == (
        "a591b9683f6b8a3d45e28c32bc112355fbcf893d998d76a8a013dc6e102aedf9"
    )


@pytest.mark.parametrize("password", ["password123", "qwerty123", "welcome123"])
def test_short_common_passwords_are_rejected(
    password_manager: PasswordManager,
    password: str,
) -> None:
    """Short common values remain invalid regardless of rejection ordering."""
    with pytest.raises(PasswordPolicyError):
        password_manager.hash(password)


def test_password_policy_accepts_password_manager_length(
    password_manager: PasswordManager,
) -> None:
    """Long generated credentials are accepted without truncation."""
    password = "N7!" + ("generated-password-segment-" * 4)
    password_hash = password_manager.hash(password)

    assert password_manager.verify(password_hash, password) is True


def test_password_policy_rejects_unbounded_values_and_invalid_stored_hashes(
    password_manager: PasswordManager,
) -> None:
    """Unbounded input and corrupted persistence values fail closed."""
    with pytest.raises(PasswordPolicyError, match="at most"):
        password_manager.hash("x" * 1_025)
    assert password_manager.verify("not-an-argon2-hash", "irrelevant") is False


def test_session_secret_is_256_bits_and_malformed_values_are_safe() -> None:
    """Only exact URL-safe secrets can map to stored session digests."""
    secret = create_session_secret()
    valid_digest = digest_session_secret(secret)

    assert len(secret) == 43
    assert len(valid_digest) == 32
    assert digest_session_secret("é") != valid_digest
    assert digest_session_secret("!" * 43) != valid_digest
    assert digest_session_secret("a" * 10_000) != valid_digest


def test_csrf_requires_exact_match_and_session_binding() -> None:
    """Signed double-submit tokens cannot cross sessions or mismatch headers."""
    signing_key = b"csrf-key-with-at-least-thirty-two-bytes"
    token = create_csrf_token(signing_key, "session-one")

    assert verify_csrf_token(signing_key, "session-one", token, token) is True
    assert verify_csrf_token(signing_key, "session-two", token, token) is False
    assert verify_csrf_token(signing_key, "session-one", token, f"{token}x") is False
    assert verify_csrf_token(signing_key, "session-one", None, token) is False


def test_keyed_pseudonyms_do_not_retain_raw_identifiers() -> None:
    """Rate/audit subjects are keyed fixed-length digests."""
    pseudonym = keyed_pseudonym(
        b"privacy-key-with-at-least-thirty-two", "Admin@Example.test", "127.0.0.1"
    )

    assert len(pseudonym) == 32
    assert b"Admin" not in pseudonym
    assert b"127.0.0.1" not in pseudonym


def test_optional_user_agent_and_malformed_csrf_fail_closed() -> None:
    """Absent correlation input stays absent and malformed signatures never raise."""
    assert digest_user_agent(None) is None
    assert digest_user_agent("") is None
    assert len(digest_user_agent("browser") or b"") == 32
    assert verify_csrf_token(b"k" * 32, "session", "malformed", "malformed") is False


def test_uuid_factory_emits_uuid7() -> None:
    """Security persistence identifiers use the application UUIDv7 seam."""
    identifier = uuid7()

    assert isinstance(identifier, UUID)
    assert identifier.version == 7
    assert identifier.variant == "specified in RFC 4122"


def test_email_normalization_is_conservative() -> None:
    """Login identifiers normalize case/edges but reject malformed syntax."""
    assert normalize_email("  Admin@Example.TEST ") == "admin@example.test"
    with pytest.raises(ValueError, match="invalid"):
        normalize_email("not-an-email")


def test_forced_change_dependency_denies_ordinary_admin_access() -> None:
    """Initial-password sessions are denied by the reusable server policy."""
    view = SessionView(
        administrator_id=uuid7(),
        display_name="Administrator",
        must_change_password=True,
        idle_expires_at=datetime.now(UTC),
        absolute_expires_at=datetime.now(UTC),
        session_id=uuid7(),
    )

    with pytest.raises(PasswordChangeRequiredError):
        IdentityService.require_full_access(view)


def test_authentication_error_types_do_not_embed_secret_values() -> None:
    """Safe authentication failures have no payload-bearing message."""
    assert str(AuthenticationRequiredError()) == ""
