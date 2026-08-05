"""Secure public contact submission and private administrator lifecycle."""
# ruff: noqa: D101, D102, D107, EM101, PLR0913, TC003

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from app.common.application.idempotency import (
    IdempotencyDecisionType,
    IdempotencyOutcome,
    IdempotencyRequest,
)
from app.common.domain.actors import ActorContext
from app.modules.audit.domain import ActorType as AuditActorType
from app.modules.audit.domain import AuditEntry, AuditOutcome
from app.modules.contacts.domain import ContactState, ContactSubmission, ContactValidationError
from app.modules.identity.domain import uuid7

if TYPE_CHECKING:
    from app.modules.contacts.ports import ContactUnitOfWorkFactory

EMAIL = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,189}\.[^\s@]{2,63}$")
ROUTE = "/api/v1/public/contacts"


class ContactNotFoundError(Exception):
    pass


class ContactConflictError(Exception):
    pass


class ContactRateLimitedError(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after


class ContactRejectedError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ContactConfiguration:
    policy_version: str
    source: str
    minimum_completion_seconds: int
    proof_ttl_seconds: int
    hmac_key: bytes
    pseudonym_key_version: str


@dataclass(frozen=True, slots=True)
class ContactFormContext:
    policy_version: str
    source: str
    issued_at: int
    proof: str


class ContactService:
    def __init__(self, uow_factory: ContactUnitOfWorkFactory, config: ContactConfiguration) -> None:
        self._uow_factory, self._config = uow_factory, config

    def form_context(self, *, now: datetime | None = None) -> ContactFormContext:
        issued = int((now or datetime.now(UTC)).timestamp())
        material = f"contact-proof:v1:{self._config.source}:{issued}".encode()
        proof = hmac.new(self._config.hmac_key, material, hashlib.sha256).hexdigest()
        return ContactFormContext(self._config.policy_version, self._config.source, issued, proof)

    def _valid_proof(self, issued_at: int, proof: str, now: datetime) -> bool:
        age = int(now.timestamp()) - issued_at
        if age < self._config.minimum_completion_seconds or age > self._config.proof_ttl_seconds:
            return False
        expected = self.form_context(now=datetime.fromtimestamp(issued_at, UTC)).proof
        return hmac.compare_digest(expected, proof)

    async def submit(
        self,
        *,
        name: str,
        email: str,
        subject: str,
        message: str,
        consent: bool,
        policy_version: str,
        source: str,
        issued_at: int,
        proof: str,
        honeypot: str,
        idempotency_key: str,
        client_ip: str,
        request_id: str,
    ) -> None:
        now = datetime.now(UTC)
        values = {
            "name": name.strip(),
            "email": email.strip().casefold(),
            "subject": subject.strip(),
            "message": message.strip(),
        }
        bounds = {"name": (1, 120), "email": (3, 254), "subject": (1, 180), "message": (1, 5000)}
        for key, (low, high) in bounds.items():
            if not low <= len(values[key]) <= high:
                raise ContactValidationError(key, "invalid_length")
        if not EMAIL.fullmatch(values["email"]):
            raise ContactValidationError("email", "invalid_format")
        if not consent:
            raise ContactValidationError("consent", "required")
        if policy_version != self._config.policy_version:
            raise ContactValidationError("policy_version", "stale")
        if (
            source != self._config.source
            or honeypot
            or not self._valid_proof(issued_at, proof, now)
        ):
            raise ContactRejectedError
        digest = hmac.new(
            self._config.hmac_key,
            f"contact-ip:{self._config.pseudonym_key_version}:{client_ip}".encode(),
            hashlib.sha256,
        ).digest()
        payload = json.dumps(
            {**values, "consent": True, "policy_version": policy_version, "source": source},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        async with self._uow_factory() as uow:
            allowed, retry = await uow.rate_limits.admit_contact(digest, now)
            if not allowed:
                raise ContactRateLimitedError(retry)
            decision = await uow.idempotency.acquire(
                IdempotencyRequest.create(
                    actor=ActorContext.public(),
                    route=ROUTE,
                    key=idempotency_key,
                    canonical_payload=payload,
                    requested_at=now,
                )
            )
            if decision.decision is IdempotencyDecisionType.REPLAY:
                return
            if (
                decision.decision is not IdempotencyDecisionType.ACQUIRED
                or decision.record_id is None
            ):
                raise ContactRejectedError
            item = ContactSubmission(
                id=uuid7(),
                **values,
                consented_at=now,
                policy_version=policy_version,
                source=self._config.source,
                state=ContactState.UNREAD,
                read_at=None,
                archived_at=None,
                created_at=now,
                updated_at=now,
                version=1,
            )
            await uow.contacts.add(item)
            await uow.idempotency.complete(
                decision.record_id,
                IdempotencyOutcome(
                    response_status=202,
                    result_code="contact.accepted",
                    resource_type="contact_submission",
                    resource_id=item.id,
                    resource_version=1,
                ),
                completed_at=now,
            )
            uow.audit.append(
                AuditEntry(
                    id=uuid7(),
                    event_type="contact.submitted",
                    actor_type=AuditActorType.ANONYMOUS,
                    actor_id=None,
                    actor_label_snapshot=None,
                    resource_type="contact_submission",
                    resource_id=item.id,
                    request_id=request_id,
                    occurred_at=now,
                    outcome=AuditOutcome.SUCCESS,
                    ip_pseudonym=digest,
                    metadata={"policy_version": policy_version, "source": self._config.source},
                    schema_version=1,
                )
            )
            await uow.commit()

    async def list(
        self,
        *,
        state: ContactState | None,
        created_from: datetime | None,
        created_to: datetime | None,
        offset: int,
        limit: int,
        oldest_first: bool,
    ) -> tuple[tuple[ContactSubmission, ...], int]:
        async with self._uow_factory() as uow:
            return await uow.contacts.list(
                state=state,
                created_from=created_from,
                created_to=created_to,
                offset=offset,
                limit=limit,
                oldest_first=oldest_first,
            )

    async def get(self, contact_id: UUID) -> ContactSubmission:
        async with self._uow_factory() as uow:
            item = await uow.contacts.get(contact_id)
        if item is None:
            raise ContactNotFoundError
        return item

    async def transition(
        self,
        contact_id: UUID,
        target: ContactState,
        *,
        expected_version: int,
        actor_id: UUID,
        request_id: str,
    ) -> ContactSubmission:
        async with self._uow_factory() as uow:
            item = await uow.contacts.get(contact_id, for_update=True)
            if item is None:
                raise ContactNotFoundError
            if item.version != expected_version:
                raise ContactConflictError
            now = await uow.contacts.database_now()
            changed = item.transition(target, now=now)
            try:
                await uow.contacts.update(changed, expected_version=expected_version)
            except LookupError as error:
                raise ContactConflictError from error
            uow.audit.append(
                AuditEntry(
                    id=uuid7(),
                    event_type=f"contact.{target.value}",
                    actor_type=AuditActorType.ADMINISTRATOR,
                    actor_id=actor_id,
                    actor_label_snapshot=None,
                    resource_type="contact_submission",
                    resource_id=item.id,
                    request_id=request_id,
                    occurred_at=now,
                    outcome=AuditOutcome.SUCCESS,
                    ip_pseudonym=None,
                    metadata={"prior_state": item.state.value},
                    schema_version=1,
                )
            )
            await uow.commit()
            return changed

    async def delete(
        self, contact_id: UUID, *, expected_version: int, actor_id: UUID, request_id: str
    ) -> None:
        async with self._uow_factory() as uow:
            item = await uow.contacts.get(contact_id, for_update=True)
            if item is None:
                raise ContactNotFoundError
            try:
                await uow.contacts.delete(contact_id, expected_version=expected_version)
            except LookupError as error:
                raise ContactConflictError from error
            now = await uow.contacts.database_now()
            uow.audit.append(
                AuditEntry(
                    id=uuid7(),
                    event_type="contact.deleted",
                    actor_type=AuditActorType.ADMINISTRATOR,
                    actor_id=actor_id,
                    actor_label_snapshot=None,
                    resource_type="contact_submission",
                    resource_id=contact_id,
                    request_id=request_id,
                    occurred_at=now,
                    outcome=AuditOutcome.SUCCESS,
                    ip_pseudonym=None,
                    metadata={"prior_state": item.state.value},
                    schema_version=1,
                )
            )
            await uow.commit()

    async def purge(
        self, *, retention_days: int, batch_size: int, apply: bool
    ) -> tuple[datetime, int]:
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        if not apply:
            async with self._uow_factory() as uow:
                _, count = await uow.contacts.list(
                    state=None,
                    created_from=None,
                    created_to=cutoff,
                    offset=0,
                    limit=1,
                    oldest_first=True,
                )
                return cutoff, count
        total = 0
        while True:
            async with self._uow_factory() as uow:
                count = await uow.contacts.purge(before=cutoff, limit=batch_size)
                await uow.commit()
            total += count
            if count < batch_size:
                return cutoff, total
