from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

Handler = Callable[[Mapping[str, Any]], Awaitable[None]]


class JobRegistry:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], Handler] = {}

    def register(self, job_type: str, schema_version: str, handler: Handler) -> None:
        key = (job_type, schema_version)
        if key in self._handlers:
            raise ValueError("duplicate job handler")
        self._handlers[key] = handler

    def resolve(self, job_type: str, schema_version: str) -> Handler:
        try:
            return self._handlers[(job_type, schema_version)]
        except KeyError as exc:
            raise ValueError("unsupported job type or schema") from exc
