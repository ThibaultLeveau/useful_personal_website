"""Password, session-secret, CSRF, and privacy pseudonym primitives."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from importlib.resources import files

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type

ARGON2_MEMORY_KIB = 65_536
ARGON2_PARALLELISM = 1
ARGON2_TIME_COST = 3
MINIMUM_PASSWORD_LENGTH = 12
MAXIMUM_PASSWORD_LENGTH = 1_024
SESSION_SECRET_BYTES = 32
_SESSION_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
_INVALID_SESSION_DIGEST = hashlib.sha256(b"invalid-session-secret").digest()


def _normalized_password(value: str) -> str:
    return "".join(value.casefold().split())


def _load_common_passwords() -> frozenset[str]:
    content = (
        files("app.modules.identity").joinpath("common_passwords.txt").read_text(encoding="utf-8")
    )
    return frozenset(
        _normalized_password(line)
        for line in content.splitlines()
        if line and not line.startswith("#")
    )


_COMMON_PASSWORDS = _load_common_passwords()


class PasswordPolicyError(ValueError):
    """A new password does not meet the public password policy."""


@dataclass(frozen=True, slots=True)
class PasswordManager:
    """Argon2id policy with one reusable non-account dummy hash."""

    hasher: PasswordHasher
    dummy_hash: str

    @classmethod
    def create(cls) -> PasswordManager:
        """Create the frozen M1 Argon2id policy."""
        hasher = PasswordHasher(
            hash_len=32,
            memory_cost=ARGON2_MEMORY_KIB,
            parallelism=ARGON2_PARALLELISM,
            salt_len=16,
            time_cost=ARGON2_TIME_COST,
            type=Type.ID,
        )
        return cls(hasher=hasher, dummy_hash=hasher.hash(secrets.token_urlsafe(48)))

    def validate_new_password(self, password: str) -> None:
        """Reject short, unbounded, and known-common baseline passwords."""
        if len(password) < MINIMUM_PASSWORD_LENGTH:
            msg = f"Password must contain at least {MINIMUM_PASSWORD_LENGTH} characters."
            raise PasswordPolicyError(msg)
        if len(password) > MAXIMUM_PASSWORD_LENGTH:
            msg = f"Password must contain at most {MAXIMUM_PASSWORD_LENGTH} characters."
            raise PasswordPolicyError(msg)
        normalized = _normalized_password(password)
        if normalized in _COMMON_PASSWORDS:
            msg = "Password is present in the common-password blocklist."
            raise PasswordPolicyError(msg)

    def hash(self, password: str) -> str:
        """Validate and hash a new password with Argon2id."""
        self.validate_new_password(password)
        return self.hasher.hash(password)

    def verify(self, password_hash: str | None, password: str) -> bool:
        """Verify a real hash or the dummy hash with indistinguishable handling."""
        selected_hash = password_hash or self.dummy_hash
        try:
            return self.hasher.verify(selected_hash, password) and password_hash is not None
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """Return whether a stored hash predates the active policy."""
        return self.hasher.check_needs_rehash(password_hash)


def create_session_secret() -> str:
    """Create a URL-safe 256-bit opaque session secret."""
    return _encode(secrets.token_bytes(SESSION_SECRET_BYTES))


def digest_session_secret(secret: str) -> bytes:
    """Digest an exact 256-bit token or a fixed nonmatching malformed sentinel."""
    if not _SESSION_SECRET_PATTERN.fullmatch(secret):
        return _INVALID_SESSION_DIGEST
    try:
        decoded = _decode(secret)
    except (ValueError, TypeError):
        return _INVALID_SESSION_DIGEST
    if len(decoded) != SESSION_SECRET_BYTES:
        return _INVALID_SESSION_DIGEST
    return hashlib.sha256(secret.encode("ascii")).digest()


def digest_user_agent(user_agent: str | None) -> bytes | None:
    """Bound user-agent correlation without retaining the raw header."""
    if not user_agent:
        return None
    return hashlib.sha256(user_agent[:1_024].encode()).digest()


def keyed_pseudonym(key: bytes, *parts: str) -> bytes:
    """Create a stable keyed pseudonym without storing raw identifiers."""
    message = "\x00".join(parts).encode()
    return hmac.digest(key, message, "sha256")


def create_csrf_token(signing_key: bytes, session_id: str) -> str:
    """Create a signed double-submit value bound to one server session."""
    nonce = _encode(secrets.token_bytes(SESSION_SECRET_BYTES))
    signature = hmac.digest(signing_key, f"{nonce}.{session_id}".encode(), "sha256")
    return f"{nonce}.{_encode(signature)}"


def verify_csrf_token(
    signing_key: bytes,
    session_id: str,
    cookie_token: str | None,
    header_token: str | None,
) -> bool:
    """Require exact double-submit equality and a valid session-bound signature."""
    if cookie_token is None or header_token is None:
        return False
    if not hmac.compare_digest(cookie_token, header_token):
        return False
    try:
        nonce, provided_signature = cookie_token.split(".", maxsplit=1)
        expected = hmac.digest(signing_key, f"{nonce}.{session_id}".encode(), "sha256")
        return hmac.compare_digest(_decode(provided_signature), expected)
    except (ValueError, TypeError):
        return False


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
