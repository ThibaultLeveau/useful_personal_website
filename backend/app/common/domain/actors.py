"""Transport-neutral actor identities for application authorization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class ActorType(StrEnum):
    """Supported authentication audiences at the application boundary."""

    PUBLIC = "public"
    ADMINISTRATOR_SESSION = "administrator_session"
    API_TOKEN = "api_token"  # noqa: S105 - actor kind, not a credential.  # nosec B105


@dataclass(frozen=True, slots=True)
class ActorContext:
    """Minimal authenticated identity passed to use cases, never an ORM object."""

    actor_type: ActorType
    actor_id: UUID | None
    scopes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Reject structurally ambiguous actor identities."""
        if self.actor_type is ActorType.PUBLIC:
            if self.actor_id is not None or self.scopes:
                msg = "a public actor cannot carry an identifier or scopes"
                raise ValueError(msg)
            return
        if self.actor_id is None:
            msg = "an authenticated actor requires an opaque identifier"
            raise ValueError(msg)
        if self.actor_type is ActorType.ADMINISTRATOR_SESSION and self.scopes:
            msg = "administrator sessions do not use token scopes"
            raise ValueError(msg)

    @classmethod
    def public(cls) -> ActorContext:
        """Create the unauthenticated public actor."""
        return cls(actor_type=ActorType.PUBLIC, actor_id=None)

    @classmethod
    def administrator(cls, administrator_id: UUID) -> ActorContext:
        """Create a fully authenticated administrator-session actor."""
        return cls(
            actor_type=ActorType.ADMINISTRATOR_SESSION,
            actor_id=administrator_id,
        )

    @classmethod
    def token(cls, token_id: UUID, scopes: frozenset[str]) -> ActorContext:
        """Create a token-shaped actor with its already-validated scopes."""
        return cls(actor_type=ActorType.API_TOKEN, actor_id=token_id, scopes=scopes)

    @property
    def storage_identity(self) -> bytes:
        """Return a stable, non-secret identity input suitable for one-way digesting."""
        identifier = str(self.actor_id) if self.actor_id is not None else "anonymous"
        return f"{self.actor_type.value}:{identifier}".encode()
