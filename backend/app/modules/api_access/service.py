"""Administrator token lifecycle and scoped bearer authentication."""

# ruff: noqa: D101, D102, D107, EM101, PLR0913, TC003
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.common.domain.actors import ActorContext
from app.modules.api_access.domain import (
    ApiTokenMetadata,
    ApiTokenScope,
    ApiTokenStatus,
    ApiTokenValidationError,
    normalize_token_name,
    validate_expiry,
)
from app.modules.api_access.security import (
    digest_api_token,
    dummy_digest,
    issue_api_token,
    parse_api_token,
)
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from app.modules.api_access.ports import ApiTokenUnitOfWork, ApiTokenUnitOfWorkFactory


class ApiTokenNotFoundError(Exception):
    pass


class ApiTokenConflictError(Exception):
    pass


class ApiTokenAuthenticationError(Exception):
    pass


class ApiTokenRateLimitedError(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after


@dataclass(frozen=True, slots=True)
class ApiTokenConfiguration:
    pepper: bytes
    key_version: str
    maximum_active_tokens: int = 50


@dataclass(frozen=True, slots=True)
class CreatedApiToken:
    metadata: ApiTokenMetadata
    plaintext: str


class ApiTokenService:
    def __init__(
        self, uow_factory: ApiTokenUnitOfWorkFactory, config: ApiTokenConfiguration
    ) -> None:
        self._uow_factory = uow_factory
        self._config = config

    @staticmethod
    def _audit(
        uow: ApiTokenUnitOfWork,
        *,
        event: str,
        actor_type: AuditActorType,
        actor_id: UUID | None,
        resource_id: UUID | None,
        request_id: str,
        now: datetime,
        metadata: dict[str, str | int | bool | None],
    ) -> None:
        uow.audit.append(
            AuditEntry(
                id=uuid7(),
                event_type=event,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_label_snapshot=None,
                resource_type="api_token",
                resource_id=resource_id,
                request_id=request_id,
                occurred_at=now,
                outcome=AuditOutcome.SUCCESS,
                ip_pseudonym=None,
                metadata=metadata,
                schema_version=1,
            )
        )

    async def create(
        self,
        *,
        owner_id: UUID,
        name: str,
        scopes: frozenset[ApiTokenScope],
        expires_at: datetime | None,
        confirm_no_expiry: bool,
        request_id: str,
        rotated_from_id: UUID | None = None,
    ) -> CreatedApiToken:
        normalized = normalize_token_name(name)
        if not scopes:
            raise ApiTokenValidationError("scopes", "required")
        async with self._uow_factory() as uow:
            now = await uow.tokens.database_now()
            validate_expiry(expires_at, now=now, confirm_no_expiry=confirm_no_expiry)
            if (
                await uow.tokens.active_count(owner_id, now=now)
                >= self._config.maximum_active_tokens
            ):
                raise ApiTokenConflictError
            if await uow.tokens.name_exists(owner_id, normalized, exclude_id=rotated_from_id):
                raise ApiTokenValidationError("name", "not_unique")
            issued = issue_api_token(self._config.pepper)
            metadata = ApiTokenMetadata(
                id=uuid7(),
                public_id=issued.public_id,
                name=normalized,
                display_suffix=issued.display_suffix,
                scopes=scopes,
                created_at=now,
                expires_at=expires_at,
                last_used_at=None,
                revoked_at=None,
                revocation_reason=None,
                rotated_from_id=rotated_from_id,
                version=1,
            )
            await uow.tokens.add(
                metadata=metadata,
                secret_digest=issued.digest,
                key_version=self._config.key_version,
                owner_id=owner_id,
                display_suffix=issued.display_suffix,
            )
            self._audit(
                uow,
                event="api_token.created",
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=owner_id,
                resource_id=metadata.id,
                request_id=request_id,
                now=now,
                metadata={
                    "scope_count": len(scopes),
                    "has_expiry": expires_at is not None,
                    "rotated": rotated_from_id is not None,
                },
            )
            await uow.commit()
            return CreatedApiToken(metadata, issued.plaintext)

    async def list(
        self, *, owner_id: UUID, offset: int, limit: int, status: str | None
    ) -> tuple[tuple[ApiTokenMetadata, ...], int, datetime]:
        async with self._uow_factory() as uow:
            now = await uow.tokens.database_now()
            items, total = await uow.tokens.list(
                owner_id=owner_id, offset=offset, limit=limit, status=status
            )
            return items, total, now

    async def get(self, token_id: UUID) -> tuple[ApiTokenMetadata, datetime]:
        async with self._uow_factory() as uow:
            item = await uow.tokens.get_metadata(token_id)
            now = await uow.tokens.database_now()
        if item is None:
            raise ApiTokenNotFoundError
        return item, now

    async def revoke(
        self,
        token_id: UUID,
        *,
        owner_id: UUID,
        expected_version: int,
        request_id: str,
        reason: str = "administrator_revoked",
    ) -> ApiTokenMetadata:
        async with self._uow_factory() as uow:
            item = await uow.tokens.get_metadata(token_id, for_update=True)
            if item is None:
                raise ApiTokenNotFoundError
            if item.version != expected_version or item.revoked_at is not None:
                raise ApiTokenConflictError
            now = await uow.tokens.database_now()
            try:
                await uow.tokens.revoke(
                    token_id, expected_version=expected_version, now=now, reason=reason
                )
            except LookupError as error:
                raise ApiTokenConflictError from error
            self._audit(
                uow,
                event="api_token.revoked",
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=owner_id,
                resource_id=token_id,
                request_id=request_id,
                now=now,
                metadata={"reason": reason},
            )
            await uow.commit()
        updated, _ = await self.get(token_id)
        return updated

    async def rotate(
        self,
        token_id: UUID,
        *,
        owner_id: UUID,
        expected_version: int,
        expires_at: datetime | None,
        confirm_no_expiry: bool,
        request_id: str,
    ) -> CreatedApiToken:
        async with self._uow_factory() as uow:
            old = await uow.tokens.get_metadata(token_id, for_update=True)
            if old is None:
                raise ApiTokenNotFoundError
            now = await uow.tokens.database_now()
            if old.version != expected_version or old.status_at(now) is not ApiTokenStatus.ACTIVE:
                raise ApiTokenConflictError
            validate_expiry(expires_at, now=now, confirm_no_expiry=confirm_no_expiry)
            issued = issue_api_token(self._config.pepper)
            replacement = ApiTokenMetadata(
                id=uuid7(),
                public_id=issued.public_id,
                name=old.name,
                display_suffix=issued.display_suffix,
                scopes=old.scopes,
                created_at=now,
                expires_at=expires_at,
                last_used_at=None,
                revoked_at=None,
                revocation_reason=None,
                rotated_from_id=old.id,
                version=1,
            )
            try:
                await uow.tokens.revoke(
                    old.id, expected_version=expected_version, now=now, reason="rotated"
                )
            except LookupError as error:
                raise ApiTokenConflictError from error
            await uow.tokens.add(
                metadata=replacement,
                secret_digest=issued.digest,
                key_version=self._config.key_version,
                owner_id=owner_id,
                display_suffix=issued.display_suffix,
            )
            self._audit(
                uow,
                event="api_token.rotated",
                actor_type=AuditActorType.ADMINISTRATOR,
                actor_id=owner_id,
                resource_id=replacement.id,
                request_id=request_id,
                now=now,
                metadata={"predecessor_id": str(old.id), "scope_count": len(old.scopes)},
            )
            await uow.commit()
            return CreatedApiToken(replacement, issued.plaintext)

    async def authenticate(
        self, bearer: str, *, required_scopes: frozenset[ApiTokenScope], request_id: str
    ) -> ActorContext:
        parsed = parse_api_token(bearer)
        public_id, secret = parsed if parsed is not None else ("_" * 22, "")
        async with self._uow_factory() as uow:
            found = await uow.tokens.find_auth(public_id) if parsed is not None else None
            expected = found[1] if found is not None else dummy_digest(self._config.pepper)
            provided = digest_api_token(self._config.pepper, public_id, secret)
            valid_digest = hmac.compare_digest(expected, provided)
            now = await uow.tokens.database_now()
            rate_subject = hmac.new(
                self._config.pepper,
                b"api-token-rate:v1\0" + public_id.encode(),
                hashlib.sha256,
            ).digest()
            allowed, retry = await uow.rate_limits.admit_api_token(
                rate_subject,
                now,
                valid=found is not None and valid_digest,
            )
            if not allowed:
                await uow.commit()
                raise ApiTokenRateLimitedError(retry)
            if found is None or not valid_digest:
                await uow.commit()
                raise ApiTokenAuthenticationError
            item, _digest, key_version = found
            if (
                key_version != self._config.key_version
                or item.status_at(now) is not ApiTokenStatus.ACTIVE
                or not required_scopes.issubset(item.scopes)
            ):
                await uow.commit()
                raise ApiTokenAuthenticationError
            await uow.tokens.touch_used(item.id, now=now)
            self._audit(
                uow,
                event="api_token.used",
                actor_type=AuditActorType.SYSTEM,
                actor_id=None,
                resource_id=item.id,
                request_id=request_id,
                now=now,
                metadata={"required_scope_count": len(required_scopes)},
            )
            await uow.commit()
            return ActorContext.token(item.id, frozenset(scope.value for scope in item.scopes))
