"""Deny-by-default application authorization policies."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.common.domain.actors import ActorContext, ActorType

_CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9:_-]{0,127}$")


class AuthorizationDeniedError(Exception):
    """Raised without resource-existence detail when a use case is not allowed."""


@dataclass(frozen=True, slots=True)
class AccessPolicy:
    """Explicit resource/action policy evaluated inside an application use case."""

    resource: str
    action: str
    allowed_actor_types: frozenset[ActorType]
    required_token_scopes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Reject empty, malformed, or contradictory policy declarations."""
        if (
            _CAPABILITY_PATTERN.fullmatch(self.resource) is None
            or _CAPABILITY_PATTERN.fullmatch(self.action) is None
        ):
            msg = "resource and action must use bounded capability names"
            raise ValueError(msg)
        if not self.allowed_actor_types:
            msg = "an access policy must allow at least one actor type"
            raise ValueError(msg)
        if any(
            _CAPABILITY_PATTERN.fullmatch(scope) is None for scope in self.required_token_scopes
        ):
            msg = "token scopes must use bounded capability names"
            raise ValueError(msg)
        if self.required_token_scopes and ActorType.API_TOKEN not in self.allowed_actor_types:
            msg = "token scopes require the API-token actor type"
            raise ValueError(msg)

    def allows(self, actor: ActorContext) -> bool:
        """Return a deterministic decision without consulting persistence."""
        if actor.actor_type not in self.allowed_actor_types:
            return False
        if actor.actor_type is ActorType.API_TOKEN:
            return self.required_token_scopes.issubset(actor.scopes)
        return True


def require_authorized(actor: ActorContext, policy: AccessPolicy) -> None:
    """Enforce one use-case policy without disclosing resource existence."""
    if not policy.allows(actor):
        raise AuthorizationDeniedError
