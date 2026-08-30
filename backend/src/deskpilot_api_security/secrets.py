from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping


_SECRET_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{2,255}$")


class SecretConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SecretRef:
    provider: str
    name: str
    version: str | None = None

    def __post_init__(self) -> None:
        if self.provider not in {"env", "vault", "aws-secrets-manager", "azure-key-vault", "gcp-secret-manager"}:
            raise SecretConfigurationError("unsupported_secret_provider")
        if not _SECRET_NAME.fullmatch(self.name):
            raise SecretConfigurationError("invalid_secret_reference")


def reject_inline_secrets(config: Mapping[str, object]) -> None:
    forbidden_fragments = ("password", "secret", "api_key", "apikey", "token", "private_key")
    for key, value in config.items():
        lower = key.lower()
        if any(fragment in lower for fragment in forbidden_fragments) and isinstance(value, str) and value:
            raise SecretConfigurationError(f"inline_secret_forbidden:{key}")
