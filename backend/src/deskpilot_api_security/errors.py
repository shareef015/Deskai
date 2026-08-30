from __future__ import annotations

from dataclasses import dataclass
import secrets


@dataclass(frozen=True, slots=True)
class ProblemDetails:
    status: int
    code: str
    title: str
    correlation_id: str
    detail: str | None = None

    def as_dict(self) -> dict[str, object]:
        body: dict[str, object] = {
            "status": self.status,
            "code": self.code,
            "title": self.title,
            "correlationId": self.correlation_id,
        }
        if self.detail:
            body["detail"] = self.detail
        return body


def public_problem(status: int, code: str, title: str, *, correlation_id: str | None = None, detail: str | None = None) -> ProblemDetails:
    # Caller-controlled detail must contain only explicitly safe text; never serialize exceptions/SQL/secrets.
    return ProblemDetails(status, code, title, correlation_id or secrets.token_hex(12), detail)
