from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from deskpilot_core.errors import DeskPilotError, ErrorCode, problem_document, unexpected_problem


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", "missing"))


async def deskpilot_error_handler(request: Request, exc: DeskPilotError) -> JSONResponse:
    payload = problem_document(exc, _correlation_id(request))
    headers = {"Cache-Control": "no-store", "X-Correlation-ID": payload["correlation_id"]}
    if exc.retry_after_seconds:
        headers["Retry-After"] = str(exc.retry_after_seconds)
    return JSONResponse(payload, status_code=exc.status, media_type="application/problem+json", headers=headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    del exc
    error = DeskPilotError(ErrorCode.VALIDATION_FAILED, "Check the documented request fields and try again.")
    payload = problem_document(error, _correlation_id(request))
    return JSONResponse(
        payload, status_code=error.status, media_type="application/problem+json",
        headers={"Cache-Control": "no-store", "X-Correlation-ID": payload["correlation_id"]},
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del exc
    payload = unexpected_problem(_correlation_id(request))
    return JSONResponse(
        payload, status_code=500, media_type="application/problem+json",
        headers={"Cache-Control": "no-store", "X-Correlation-ID": payload["correlation_id"]},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DeskPilotError, deskpilot_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_error_handler)

