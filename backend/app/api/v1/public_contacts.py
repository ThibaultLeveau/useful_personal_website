"""Unauthenticated safe contact-form endpoints."""
# ruff: noqa: D103, EM101, FAST001

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Header, Request, Response

from app.api.v1.contact_schemas import (
    ContactAcceptedData,
    ContactFormContextData,
    ContactSubmitRequest,
)
from app.api.v1.conventions import set_private_no_store, success
from app.api.v1.schemas import ErrorEnvelope, SuccessEnvelope
from app.common.errors import ApiError
from app.common.request_context import get_request_id
from app.modules.contacts.domain import ContactValidationError
from app.modules.contacts.service import (
    ContactRateLimitedError,
    ContactRejectedError,
    ContactService,
)

router = APIRouter(prefix="/public/contacts", tags=["Contact"])


def _service(request: Request) -> ContactService:
    service = getattr(request.app.state, "contact_service", None)
    if not isinstance(service, ContactService):
        raise ApiError.from_code("DEPENDENCY_UNAVAILABLE")
    return service


@router.get("/form-context", response_model=SuccessEnvelope[ContactFormContextData])
async def form_context(
    request: Request, response: Response
) -> SuccessEnvelope[ContactFormContextData]:
    context = _service(request).form_context()
    set_private_no_store(response)
    return success(
        request,
        ContactFormContextData(
            policy_version=context.policy_version,
            source=context.source,
            issued_at=context.issued_at,
            proof=context.proof,
        ),
    )


@router.post(
    "",
    status_code=HTTPStatus.ACCEPTED,
    response_model=SuccessEnvelope[ContactAcceptedData],
    responses={
        400: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        429: {"model": ErrorEnvelope},
    },
)
async def submit_contact(
    request: Request,
    response: Response,
    body: ContactSubmitRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> SuccessEnvelope[ContactAcceptedData]:
    client_ip = request.client.host if request.client is not None else "unknown"
    try:
        await _service(request).submit(
            name=body.name,
            email=str(body.email),
            subject=body.subject,
            message=body.message,
            consent=body.consent,
            policy_version=body.policy_version,
            source=body.source,
            issued_at=body.issued_at,
            proof=body.proof,
            honeypot=body.website,
            idempotency_key=idempotency_key,
            client_ip=client_ip,
            request_id=get_request_id(request),
        )
    except ContactRateLimitedError as error:
        response.headers["Retry-After"] = str(error.retry_after)
        raise ApiError.from_code("RATE_LIMITED") from error
    except ContactRejectedError as error:
        raise ApiError.from_code("VALIDATION_FAILED", details={"fields": []}) from error
    except ContactValidationError as error:
        raise ApiError.from_code(
            "VALIDATION_FAILED",
            details={
                "fields": [{"path": error.path, "code": error.code, "message": "Value is invalid."}]
            },
        ) from error
    set_private_no_store(response)
    return success(request, ContactAcceptedData())
