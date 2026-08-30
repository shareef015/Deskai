from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Mapping, Protocol
from urllib.parse import urlparse


APPROVED_SCHEMES = frozenset({"env", "file", "vault"})


class SecretResolutionError(RuntimeError):
    """Safe, value-free error raised when a secret cannot be resolved."""


@dataclass(frozen=True, slots=True)
class SecretReference:
    scheme: str
    location: str

    @classmethod
    def parse(cls, raw: str) -> "SecretReference":
        parsed = urlparse(raw)
        if parsed.scheme not in APPROVED_SCHEMES:
            raise SecretResolutionError("secret reference uses an unapproved provider")
        location = (parsed.netloc + parsed.path).strip("/")
        if not location or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise SecretResolutionError("secret reference is malformed")
        if parsed.scheme == "file" and not raw.startswith("file:///"):
            raise SecretResolutionError("file secret reference must use an absolute path")
        return cls(parsed.scheme, "/" + location if parsed.scheme == "file" else location)

    def __str__(self) -> str:
        return f"{self.scheme}://[REDACTED]"


@dataclass(frozen=True, slots=True)
class SecretValue:
    _value: str

    def reveal(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "[REDACTED]"

    def __repr__(self) -> str:
        return "SecretValue('[REDACTED]')"


@dataclass(frozen=True, slots=True)
class RotationMetadata:
    secret_id: str
    version: str
    rotated_at: datetime
    expires_at: datetime

    def validate(self, *, now: datetime | None = None, warning_days: int = 14) -> bool:
        instant = now or datetime.now(UTC)
        if self.rotated_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise SecretResolutionError("rotation timestamps must be timezone-aware")
        if self.expires_at <= instant:
            raise SecretResolutionError("secret is expired")
        return self.expires_at <= instant + timedelta(days=warning_days)


class SecretProvider(Protocol):
    def resolve(self, reference: SecretReference) -> SecretValue: ...


class EnvironmentSecretProvider:
    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = environment if environment is not None else os.environ

    def resolve(self, reference: SecretReference) -> SecretValue:
        if reference.scheme != "env":
            raise SecretResolutionError("environment provider received wrong reference type")
        value = self._environment.get(reference.location)
        if not value:
            raise SecretResolutionError("required environment secret is unavailable")
        return SecretValue(value)


class FileSecretProvider:
    def __init__(self, allowed_roots: tuple[Path, ...]) -> None:
        self._roots = tuple(path.resolve() for path in allowed_roots)

    def resolve(self, reference: SecretReference) -> SecretValue:
        if reference.scheme != "file":
            raise SecretResolutionError("file provider received wrong reference type")
        path = Path(reference.location).resolve()
        if not any(path.is_relative_to(root) for root in self._roots):
            raise SecretResolutionError("file secret is outside approved roots")
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise SecretResolutionError("required file secret is unavailable") from exc
        if not value:
            raise SecretResolutionError("required file secret is empty")
        return SecretValue(value)


class VaultSecretProvider(Protocol):
    """Deployment adapter for Vault or a customer-approved cloud secret store."""

    def resolve(self, reference: SecretReference) -> SecretValue: ...


class SecretResolver:
    def __init__(self, providers: Mapping[str, SecretProvider]) -> None:
        self._providers = dict(providers)

    def resolve(self, raw_reference: str) -> SecretValue:
        reference = SecretReference.parse(raw_reference)
        provider = self._providers.get(reference.scheme)
        if provider is None:
            raise SecretResolutionError("required secret provider is not configured")
        return provider.resolve(reference)

