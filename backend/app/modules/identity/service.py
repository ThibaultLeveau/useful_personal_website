"""Identity application services and transaction boundaries."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from app.modules.audit.domain import ActorType, AuditEntry, AuditOutcome
from app.modules.identity.domain import (
    BootstrapResult,
    NewAdministrator,
    NewAdminSession,
    SessionIssue,
    SessionView,
    utc_now,
    uuid7,
)
from app.modules.identity.security import (
    PasswordManager,
    PasswordPolicyError,
    create_csrf_token,
    create_session_secret,
    digest_session_secret,
    digest_user_agent,
    keyed_pseudonym,
    verify_csrf_token,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from uuid import UUID

    from app.modules.identity.ports import (
        AdministratorState,
        AdminSessionState,
        IdentityUnitOfWorkFactory,
        RateLimitDecision,
    )


SESSION_IDLE_MINUTES = 30
SESSION_ABSOLUTE_HOURS = 12
MAXIMUM_EMAIL_LENGTH = 320
MAXIMUM_DISPLAY_NAME_LENGTH = 160


class BootstrapAlreadyCompletedError(RuntimeError):
    """Bootstrap refused because an active administrator already exists."""


class AuthenticationFailedError(RuntimeError):
    """Credentials are invalid without revealing which field failed."""


class AuthenticationRequiredError(RuntimeError):
    """The opaque session is absent, invalid, expired, or revoked."""


class PasswordChangeRequiredError(RuntimeError):
    """The initial-password session cannot perform an ordinary admin action."""


class CsrfValidationError(RuntimeError):
    """The signed double-submit CSRF value is invalid."""


@dataclass(frozen=True, slots=True)
class RateLimitedError(RuntimeError):
    """Authentication is temporarily blocked for a pseudonymous subject."""

    retry_after_seconds: int


@dataclass(frozen=True, slots=True)
class IdentityServiceConfiguration:
    """Security keys and deterministic seams for the identity service."""

    csrf_signing_key: bytes
    privacy_hmac_key: bytes
    password_manager: PasswordManager
    hash_concurrency: int = 2
    clock: Callable[[], datetime] = utc_now
    uuid_factory: Callable[[], UUID] = uuid7


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Explicit login input detached from the transport framework."""

    email: str
    password: str
    client_ip: str
    user_agent: str | None
    request_id: str


@dataclass(frozen=True, slots=True)
class ChangePasswordCommand:
    """Explicit password-change input detached from the transport framework."""

    secret: str
    current_password: str
    new_password: str
    csrf_cookie: str | None
    csrf_header: str | None
    request_id: str
    client_ip: str
    user_agent: str | None


@dataclass(frozen=True, slots=True)
class AuditFact:
    """Controlled data accepted by the minimal audit factory."""

    event_type: str
    outcome: AuditOutcome
    request_id: str
    now: datetime
    administrator_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    ip_pseudonym: bytes | None = None


def normalize_email(email: str) -> str:
    """Normalize the R1 login identifier with bounded conservative syntax."""
    normalized = email.strip().casefold()
    local, separator, domain = normalized.rpartition("@")
    if (
        separator != "@"
        or not local
        or not domain
        or "." not in domain
        or len(normalized) > MAXIMUM_EMAIL_LENGTH
        or any(character.isspace() for character in normalized)
    ):
        msg = "Email address is invalid."
        raise ValueError(msg)
    return normalized


class BootstrapService:
    """Explicit takeover-safe initial-administrator command service."""

    def __init__(
        self,
        uow_factory: IdentityUnitOfWorkFactory,
        *,
        password_manager: PasswordManager | None = None,
        clock: Callable[[], datetime] = utc_now,
        uuid_factory: Callable[[], UUID] = uuid7,
    ) -> None:
        """Store deterministic seams without opening a database connection."""
        self._uow_factory = uow_factory
        self._password_manager = password_manager or PasswordManager.create()
        self._clock = clock
        self._uuid_factory = uuid_factory

    async def bootstrap(self, *, email: str, display_name: str, password: str) -> BootstrapResult:
        """Create exactly one initial administrator or refuse without mutation."""
        email_normalized = normalize_email(email)
        clean_display_name = display_name.strip()
        if not clean_display_name or len(clean_display_name) > MAXIMUM_DISPLAY_NAME_LENGTH:
            msg = "Display name must contain between 1 and 160 characters."
            raise ValueError(msg)
        password_hash = await asyncio.to_thread(self._password_manager.hash, password)
        now = self._clock()
        administrator_id = self._uuid_factory()

        async with self._uow_factory() as uow:
            identity = uow.identity
            audit = uow.audit
            await identity.acquire_bootstrap_lock()
            if await identity.administrator_count() != 0:
                raise BootstrapAlreadyCompletedError
            identity.add_administrator(
                NewAdministrator(
                    id=administrator_id,
                    email=email.strip(),
                    email_normalized=email_normalized,
                    display_name=clean_display_name,
                    password_hash=password_hash,
                    must_change_password=True,
                    is_active=True,
                    password_changed_at=None,
                    created_at=now,
                    updated_at=now,
                    version=1,
                )
            )
            audit.append(
                self._audit_entry(
                    event_type="admin.bootstrap_succeeded",
                    administrator_id=administrator_id,
                    request_id="bootstrap-cli",
                    now=now,
                )
            )
            await uow.commit()
        return BootstrapResult(administrator_id=administrator_id)

    def _audit_entry(
        self,
        *,
        event_type: str,
        administrator_id: UUID,
        request_id: str,
        now: datetime,
    ) -> AuditEntry:
        return AuditEntry(
            id=self._uuid_factory(),
            event_type=event_type,
            actor_type=ActorType.SYSTEM,
            actor_id=None,
            actor_label_snapshot="system",
            resource_type="administrator",
            resource_id=administrator_id,
            request_id=request_id,
            occurred_at=now,
            outcome=AuditOutcome.SUCCESS,
            ip_pseudonym=None,
            metadata={"source": "bootstrap_cli"},
            schema_version=1,
        )


class IdentityService:
    """Login, session, CSRF, password, and logout application service."""

    def __init__(
        self,
        uow_factory: IdentityUnitOfWorkFactory,
        configuration: IdentityServiceConfiguration,
    ) -> None:
        """Store security keys and deterministic seams for request services."""
        self._uow_factory = uow_factory
        self._csrf_signing_key = configuration.csrf_signing_key
        self._privacy_hmac_key = configuration.privacy_hmac_key
        self._password_manager = configuration.password_manager
        if configuration.hash_concurrency < 1:
            msg = "hash_concurrency must be positive"
            raise ValueError(msg)
        self._hash_slots = asyncio.Semaphore(configuration.hash_concurrency)
        self._clock = configuration.clock
        self._uuid_factory = configuration.uuid_factory

    async def login(self, command: LoginCommand) -> SessionIssue:
        """Authenticate without holding a database connection during Argon2 work."""
        try:
            email_normalized = normalize_email(command.email)
        except ValueError:
            email_normalized = "invalid@invalid.invalid"
        subject = keyed_pseudonym(
            self._privacy_hmac_key,
            email_normalized,
            command.client_ip,
        )
        now = self._clock()

        decision, administrator = await self._login_preflight(
            email_normalized,
            subject,
            now,
        )

        if not decision.allowed:
            async with self._uow_factory() as denied_uow:
                denied_uow.audit.append(
                    self._audit(
                        AuditFact(
                            event_type="admin.login_rate_limited",
                            outcome=AuditOutcome.DENIED,
                            request_id=command.request_id,
                            now=now,
                            ip_pseudonym=keyed_pseudonym(
                                self._privacy_hmac_key,
                                command.client_ip,
                            ),
                        )
                    )
                )
                await denied_uow.commit()
            raise RateLimitedError(decision.retry_after_seconds)

        password_hash = administrator.password_hash if administrator is not None else None
        verified = await self._verify_password(password_hash, command.password)
        replacement_hash: str | None = None
        if (
            verified
            and password_hash is not None
            and self._password_manager.needs_rehash(password_hash)
        ):
            replacement_hash = await self._hash_password(command.password)

        if not verified or administrator is None:
            async with self._uow_factory() as failure_uow:
                rate_limit = failure_uow.rate_limit
                failure_decision = await rate_limit.record_login_failure(subject, now)
                failure_uow.audit.append(
                    self._audit(
                        AuditFact(
                            event_type="admin.login_failed",
                            outcome=AuditOutcome.FAILURE,
                            request_id=command.request_id,
                            now=now,
                            ip_pseudonym=keyed_pseudonym(
                                self._privacy_hmac_key,
                                command.client_ip,
                            ),
                        )
                    )
                )
                await failure_uow.commit()
            if not failure_decision.allowed:
                raise RateLimitedError(failure_decision.retry_after_seconds)
            raise AuthenticationFailedError

        async with self._uow_factory() as write_uow:
            identity = write_uow.identity
            rate_limit = write_uow.rate_limit
            audit = write_uow.audit
            concurrent_decision = await rate_limit.check_login(subject, now)
            locked_administrator = await identity.administrator_by_id(
                administrator.id,
                for_update=True,
            )
            if not concurrent_decision.allowed:
                write_uow.audit.append(
                    self._audit(
                        AuditFact(
                            event_type="admin.login_rate_limited",
                            outcome=AuditOutcome.DENIED,
                            request_id=command.request_id,
                            now=now,
                            ip_pseudonym=keyed_pseudonym(
                                self._privacy_hmac_key,
                                command.client_ip,
                            ),
                        )
                    )
                )
                await write_uow.commit()
                raise RateLimitedError(concurrent_decision.retry_after_seconds)
            if locked_administrator is None or locked_administrator.password_hash != password_hash:
                write_uow.audit.append(
                    self._audit(
                        AuditFact(
                            event_type="admin.login_failed",
                            outcome=AuditOutcome.FAILURE,
                            request_id=command.request_id,
                            now=now,
                            ip_pseudonym=keyed_pseudonym(
                                self._privacy_hmac_key,
                                command.client_ip,
                            ),
                        )
                    )
                )
                await write_uow.commit()
                raise AuthenticationFailedError
            if replacement_hash is not None:
                locked_administrator.password_hash = replacement_hash
                locked_administrator.updated_at = now
                locked_administrator.version += 1
            await rate_limit.clear_login_failures(subject)
            issue = self._new_session(
                administrator=locked_administrator,
                now=now,
                user_agent=command.user_agent,
                client_ip=command.client_ip,
            )
            identity.add_session(issue[0])
            audit.append(
                self._audit(
                    AuditFact(
                        event_type="admin.login_succeeded",
                        outcome=AuditOutcome.SUCCESS,
                        request_id=command.request_id,
                        now=now,
                        administrator_id=locked_administrator.id,
                        resource_id=issue[0].id,
                        resource_type="admin_session",
                        ip_pseudonym=keyed_pseudonym(
                            self._privacy_hmac_key,
                            command.client_ip,
                        ),
                    )
                )
            )
            await write_uow.commit()
            return issue[1]

    async def inspect_session(self, secret: str) -> SessionView:
        """Return a safe session projection without mutating on GET."""
        now = self._clock()
        async with self._uow_factory() as uow:
            pair = await uow.identity.session_with_administrator(digest_session_secret(secret))
            return self._validated_view(pair, now)

    async def logout(
        self,
        *,
        secret: str,
        csrf_cookie: str | None,
        csrf_header: str | None,
        request_id: str,
    ) -> None:
        """Revoke the current session transactionally with audit."""
        now = self._clock()
        async with self._uow_factory() as uow:
            identity = uow.identity
            pair = await identity.session_with_administrator(
                digest_session_secret(secret),
                for_update=True,
            )
            if pair is None:
                raise AuthenticationRequiredError
            view = self._validated_view(pair, now)
            self.validate_csrf(view.session_id, csrf_cookie, csrf_header)
            pair[0].revoked_at = now
            pair[0].revocation_reason = "logout"
            uow.audit.append(
                self._audit(
                    AuditFact(
                        event_type="admin.logout",
                        outcome=AuditOutcome.SUCCESS,
                        request_id=request_id,
                        now=now,
                        administrator_id=view.administrator_id,
                        resource_type="admin_session",
                        resource_id=view.session_id,
                    )
                )
            )
            await uow.commit()

    async def change_password(self, command: ChangePasswordCommand) -> SessionIssue:
        """Authenticate outside transactions, then re-lock and rotate atomically."""
        now = self._clock()
        secret_digest = digest_session_secret(command.secret)
        async with self._uow_factory() as read_uow:
            pair = await read_uow.identity.session_with_administrator(secret_digest)
            if pair is None:
                raise AuthenticationRequiredError
            view = self._validated_view(pair, now)
            password_hash = pair[1].password_hash

        self.validate_csrf(view.session_id, command.csrf_cookie, command.csrf_header)
        verified = await self._verify_password(password_hash, command.current_password)
        if not verified:
            async with self._uow_factory() as denied_uow:
                denied_uow.audit.append(
                    self._audit(
                        AuditFact(
                            event_type="admin.password_change_failed",
                            outcome=AuditOutcome.FAILURE,
                            request_id=command.request_id,
                            now=now,
                            administrator_id=view.administrator_id,
                            resource_type="administrator",
                            resource_id=view.administrator_id,
                        )
                    )
                )
                await denied_uow.commit()
            raise AuthenticationFailedError

        if command.new_password == command.current_password:
            msg = "New password must differ from the current password."
            raise PasswordPolicyError(msg)
        new_hash = await self._hash_password(command.new_password)
        async with self._uow_factory() as write_uow:
            identity = write_uow.identity
            locked_pair = await identity.session_with_administrator(
                secret_digest,
                for_update=True,
            )
            if locked_pair is None:
                raise AuthenticationRequiredError
            locked_view = self._validated_view(locked_pair, now)
            self.validate_csrf(
                locked_view.session_id,
                command.csrf_cookie,
                command.csrf_header,
            )
            current_session, administrator = locked_pair
            if administrator.password_hash != password_hash:
                raise AuthenticationFailedError
            current_session.revoked_at = now
            current_session.revocation_reason = "password_changed"
            await identity.revoke_other_sessions(
                administrator_id=administrator.id,
                current_session_id=current_session.id,
                revoked_at=now,
                reason="password_changed",
            )
            administrator.password_hash = new_hash
            administrator.must_change_password = False
            administrator.password_changed_at = now
            administrator.updated_at = now
            administrator.version += 1
            issue = self._new_session(
                administrator=administrator,
                now=now,
                user_agent=command.user_agent,
                client_ip=command.client_ip,
                rotated_from_id=current_session.id,
            )
            identity.add_session(issue[0])
            write_uow.audit.append(
                self._audit(
                    AuditFact(
                        event_type="admin.password_changed",
                        outcome=AuditOutcome.SUCCESS,
                        request_id=command.request_id,
                        now=now,
                        administrator_id=administrator.id,
                        resource_type="administrator",
                        resource_id=administrator.id,
                    )
                )
            )
            await write_uow.commit()
            return issue[1]

    async def refresh_session(
        self,
        *,
        secret: str,
        csrf_cookie: str | None,
        csrf_header: str | None,
    ) -> SessionView:
        """Slide idle expiry on explicit CSRF-protected activity, capped absolutely."""
        now = self._clock()
        async with self._uow_factory() as uow:
            pair = await uow.identity.session_with_administrator(
                digest_session_secret(secret),
                for_update=True,
            )
            if pair is None:
                raise AuthenticationRequiredError
            view = self._validated_view(pair, now)
            self.validate_csrf(view.session_id, csrf_cookie, csrf_header)
            session, administrator = pair
            session.last_seen_at = now
            session.idle_expires_at = min(
                now + timedelta(minutes=SESSION_IDLE_MINUTES),
                session.absolute_expires_at,
            )
            refreshed = SessionView(
                administrator_id=administrator.id,
                display_name=administrator.display_name,
                must_change_password=administrator.must_change_password,
                idle_expires_at=session.idle_expires_at,
                absolute_expires_at=session.absolute_expires_at,
                session_id=session.id,
            )
            await uow.commit()
            return refreshed

    def csrf_token(self, session_id: UUID) -> str:
        """Issue a new signed CSRF token for a validated session."""
        return create_csrf_token(self._csrf_signing_key, str(session_id))

    def cookie_max_age_seconds(self, view: SessionView) -> int:
        """Cap browser cookie lifetime at the server-side absolute expiry."""
        remaining = int((view.absolute_expires_at - self._clock()).total_seconds())
        return max(1, min(remaining, SESSION_ABSOLUTE_HOURS * 60 * 60))

    def validate_csrf(
        self,
        session_id: UUID,
        cookie_token: str | None,
        header_token: str | None,
    ) -> None:
        """Reject missing, mismatched, or invalid session-bound CSRF values."""
        if not verify_csrf_token(
            self._csrf_signing_key,
            str(session_id),
            cookie_token,
            header_token,
        ):
            raise CsrfValidationError

    @staticmethod
    def require_full_access(view: SessionView) -> None:
        """Deny ordinary administration until the initial password is replaced."""
        if view.must_change_password:
            raise PasswordChangeRequiredError

    def _new_session(
        self,
        *,
        administrator: AdministratorState,
        now: datetime,
        user_agent: str | None,
        client_ip: str,
        rotated_from_id: UUID | None = None,
    ) -> tuple[NewAdminSession, SessionIssue]:
        session_id = self._uuid_factory()
        secret = create_session_secret()
        idle_expires_at = now + timedelta(minutes=SESSION_IDLE_MINUTES)
        absolute_expires_at = now + timedelta(hours=SESSION_ABSOLUTE_HOURS)
        record = NewAdminSession(
            id=session_id,
            administrator_id=administrator.id,
            token_digest=digest_session_secret(secret),
            created_at=now,
            last_seen_at=now,
            idle_expires_at=idle_expires_at,
            absolute_expires_at=absolute_expires_at,
            revoked_at=None,
            revocation_reason=None,
            user_agent_digest=digest_user_agent(user_agent),
            ip_pseudonym=keyed_pseudonym(self._privacy_hmac_key, client_ip),
            rotated_from_id=rotated_from_id,
        )
        view = SessionView(
            administrator_id=administrator.id,
            display_name=administrator.display_name,
            must_change_password=administrator.must_change_password,
            idle_expires_at=idle_expires_at,
            absolute_expires_at=absolute_expires_at,
            session_id=session_id,
        )
        return record, SessionIssue(secret=secret, view=view)

    async def _verify_password(self, password_hash: str | None, password: str) -> bool:
        """Bound process-wide Argon2 verification concurrency for this app instance."""
        async with self._hash_slots:
            return await asyncio.to_thread(
                self._password_manager.verify,
                password_hash,
                password,
            )

    async def _hash_password(self, password: str) -> str:
        """Bound process-wide Argon2 hashing concurrency for this app instance."""
        async with self._hash_slots:
            return await asyncio.to_thread(self._password_manager.hash, password)

    async def _login_preflight(
        self,
        email_normalized: str,
        subject: bytes,
        now: datetime,
    ) -> tuple[RateLimitDecision, AdministratorState | None]:
        """Read rate/admin state in a short transaction before Argon2 admission."""
        async with self._uow_factory() as read_uow:
            decision = await read_uow.rate_limit.check_login(subject, now)
            administrator = (
                None
                if not decision.allowed
                else await read_uow.identity.administrator_by_email(email_normalized)
            )
        return decision, administrator

    @staticmethod
    def _validated_view(
        pair: tuple[AdminSessionState, AdministratorState] | None,
        now: datetime,
    ) -> SessionView:
        if pair is None:
            raise AuthenticationRequiredError
        session, administrator = pair
        if (
            session.revoked_at is not None
            or session.idle_expires_at <= now
            or session.absolute_expires_at <= now
        ):
            raise AuthenticationRequiredError
        return SessionView(
            administrator_id=administrator.id,
            display_name=administrator.display_name,
            must_change_password=administrator.must_change_password,
            idle_expires_at=session.idle_expires_at,
            absolute_expires_at=session.absolute_expires_at,
            session_id=session.id,
        )

    def _audit(self, fact: AuditFact) -> AuditEntry:
        actor_type = ActorType.ADMINISTRATOR if fact.administrator_id else ActorType.ANONYMOUS
        return AuditEntry(
            id=self._uuid_factory(),
            event_type=fact.event_type,
            actor_type=actor_type,
            actor_id=fact.administrator_id,
            actor_label_snapshot=("administrator" if fact.administrator_id else "anonymous"),
            resource_type=fact.resource_type,
            resource_id=fact.resource_id,
            request_id=fact.request_id,
            occurred_at=fact.now,
            outcome=fact.outcome,
            ip_pseudonym=fact.ip_pseudonym,
            metadata={},
            schema_version=1,
        )


__all__ = [
    "AuthenticationFailedError",
    "AuthenticationRequiredError",
    "BootstrapAlreadyCompletedError",
    "BootstrapService",
    "ChangePasswordCommand",
    "CsrfValidationError",
    "IdentityService",
    "IdentityServiceConfiguration",
    "LoginCommand",
    "PasswordChangeRequiredError",
    "PasswordPolicyError",
    "RateLimitedError",
    "normalize_email",
]
