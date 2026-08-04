"""Token generation, parsing, and purpose-separated HMAC digesting."""
# ruff: noqa: D101, D103

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass

TOKEN_PATTERN = re.compile(
    r"^pp_live_(?P<public>[A-Za-z0-9_-]{22})\.(?P<secret>[A-Za-z0-9_-]{43})$"
)
DUMMY_SECRET = b"\0" * 32


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


@dataclass(frozen=True, slots=True)
class IssuedApiToken:
    public_id: str
    plaintext: str
    display_suffix: str
    digest: bytes


def issue_api_token(pepper: bytes) -> IssuedApiToken:
    public_id = _encode(secrets.token_bytes(16))
    secret = _encode(secrets.token_bytes(32))
    plaintext = f"pp_live_{public_id}.{secret}"
    return IssuedApiToken(
        public_id, plaintext, secret[-6:], digest_api_token(pepper, public_id, secret)
    )


def parse_api_token(value: str) -> tuple[str, str] | None:
    match = TOKEN_PATTERN.fullmatch(value)
    return None if match is None else (match.group("public"), match.group("secret"))


def digest_api_token(pepper: bytes, public_id: str, secret: str) -> bytes:
    return hmac.new(
        pepper, b"api-token:v1\0" + public_id.encode() + b"\0" + secret.encode(), hashlib.sha256
    ).digest()


def dummy_digest(pepper: bytes) -> bytes:
    return hmac.new(pepper, b"api-token:v1\0unknown\0" + DUMMY_SECRET, hashlib.sha256).digest()
