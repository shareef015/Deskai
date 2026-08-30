from __future__ import annotations

from dataclasses import dataclass
import re


_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class RequestValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RequestLimits:
    max_content_length: int = 1_048_576
    allowed_content_types: frozenset[str] = frozenset({"application/json"})

    def validate(self, *, method: str, content_length: int | None, content_type: str | None) -> None:
        if content_length is not None and (content_length < 0 or content_length > self.max_content_length):
            raise RequestValidationError("request_body_too_large")
        if method.upper() in {"POST", "PUT", "PATCH"}:
            media_type = (content_type or "").split(";", 1)[0].strip().lower()
            if media_type not in self.allowed_content_types:
                raise RequestValidationError("unsupported_content_type")


def validate_request_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not _REQUEST_ID.fullmatch(value):
        raise RequestValidationError("invalid_request_id")
    return value
