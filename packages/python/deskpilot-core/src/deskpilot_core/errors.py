from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping


class ErrorCode(StrEnum):
    VALIDATION_FAILED = "validation_failed"
    AUTHENTICATION_REQUIRED = "authentication_required"
    ACCESS_DENIED = "access_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"
    CONFLICT = "conflict"
    RATE_LIMITED = "rate_limited"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    INTERNAL_ERROR = "internal_error"


_STATUS_BY_CODE = {
    ErrorCode.VALIDATION_FAILED: 422,
    ErrorCode.AUTHENTICATION_REQUIRED: 401,
    ErrorCode.ACCESS_DENIED: 403,
    ErrorCode.RESOURCE_NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.DEPENDENCY_UNAVAILABLE: 503,
    ErrorCode.DEADLINE_EXCEEDED: 504,
    ErrorCode.INTERNAL_ERROR: 500,
}
_PUBLIC_TITLES = {
    ErrorCode.VALIDATION_FAILED: "Request validation failed",
    ErrorCode.AUTHENTICATION_REQUIRED: "Authentication is required",
    ErrorCode.ACCESS_DENIED: "The operation is not permitted",
    ErrorCode.RESOURCE_NOT_FOUND: "The requested resource was not found",
    ErrorCode.CONFLICT: "The request conflicts with current state",
    ErrorCode.RATE_LIMITED: "Too many requests",
    ErrorCode.DEPENDENCY_UNAVAILABLE: "A required service is temporarily unavailable",
    ErrorCode.DEADLINE_EXCEEDED: "The operation timed out",
    ErrorCode.INTERNAL_ERROR: "The request could not be completed",
}
_SAFE_DETAIL = re.compile(r"^[A-Za-z0-9 ,.:'()/_-]{1,240}$")


@dataclass(frozen=True, slots=True)
class DeskPilotError(Exception):
    code: ErrorCode
    safe_detail: str | None = None
    retry_after_seconds: int | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.safe_detail is not None and not _SAFE_DETAIL.fullmatch(self.safe_detail):
            raise ValueError("safe error detail contains prohibited characters")
        if self.retry_after_seconds is not None and not 1 <= self.retry_after_seconds <= 3600:
            raise ValueError("retry_after_seconds must be between 1 and 3600")

    @property
    def status(self) -> int:
        return _STATUS_BY_CODE[self.code]

    def __str__(self) -> str:
        return self.code.value


def problem_document(error: DeskPilotError, correlation_id: str) -> dict[str, Any]:
    if not correlation_id.strip():
        raise ValueError("correlation_id is required")
    result: dict[str, Any] = {
        "type": f"https://errors.deskpilot.invalid/{error.code.value}",
        "title": _PUBLIC_TITLES[error.code],
        "status": error.status,
        "code": error.code.value,
        "correlation_id": correlation_id,
        "retryable": error.code in {
            ErrorCode.RATE_LIMITED,
            ErrorCode.DEPENDENCY_UNAVAILABLE,
            ErrorCode.DEADLINE_EXCEEDED,
        },
    }
    if error.safe_detail:
        result["detail"] = error.safe_detail
    if error.retry_after_seconds:
        result["retry_after_seconds"] = error.retry_after_seconds
    return result


def unexpected_problem(correlation_id: str) -> dict[str, Any]:
    return problem_document(DeskPilotError(ErrorCode.INTERNAL_ERROR), correlation_id)

