from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping


Environment = Literal["development", "test", "production"]
_ALLOWED_KEYS = {
    "environment", "debug", "api_docs_enabled", "synthetic_mode",
    "external_data_transfer", "log_level", "max_managed_endpoints",
    "managed_endpoint_operating_systems", "database_url_ref", "redis_url_ref",
    "oidc_issuer", "oidc_audience", "endpoint_ca_certificate_ref",
}
_SECRET_MARKERS = ("password", "secret", "private_key", "api_key")


class ConfigurationError(ValueError):
    """Raised before service startup when configuration violates policy."""


@dataclass(frozen=True, slots=True)
class RuntimeConfiguration:
    values: Mapping[str, Any]
    fingerprint: str

    @property
    def environment(self) -> Environment:
        return self.values["environment"]


def _redacted(values: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: "[REDACTED]" if any(marker in key for marker in _SECRET_MARKERS) else value
        for key, value in values.items()
    }


def load_configuration(profile: Path, overrides: Mapping[str, Any] | None = None) -> RuntimeConfiguration:
    values = json.loads(profile.read_text(encoding="utf-8"))
    if not isinstance(values, dict):
        raise ConfigurationError("configuration profile must be a JSON object")
    values.update(overrides or {})
    unknown = sorted(set(values) - _ALLOWED_KEYS)
    if unknown:
        raise ConfigurationError(f"unknown configuration keys: {', '.join(unknown)}")
    _validate(values)
    canonical = json.dumps(_redacted(values), sort_keys=True, separators=(",", ":"))
    return RuntimeConfiguration(values=values, fingerprint=hashlib.sha256(canonical.encode()).hexdigest())


def _validate(values: Mapping[str, Any]) -> None:
    environment = values.get("environment")
    if environment not in {"development", "test", "production"}:
        raise ConfigurationError("environment must be development, test, or production")
    if set(values.get("managed_endpoint_operating_systems", [])) != {"windows_10", "windows_11"}:
        raise ConfigurationError("only Windows 10 and Windows 11 endpoints are supported")
    if values.get("max_managed_endpoints") != 10:
        raise ConfigurationError("the private pilot is restricted to ten endpoints")
    if environment == "production":
        unsafe = [key for key in ("debug", "api_docs_enabled", "synthetic_mode", "external_data_transfer") if values.get(key)]
        if unsafe:
            raise ConfigurationError(f"unsafe production settings: {', '.join(unsafe)}")
        required = ("database_url_ref", "redis_url_ref", "oidc_issuer", "oidc_audience", "endpoint_ca_certificate_ref")
        missing = [key for key in required if not values.get(key)]
        if missing:
            raise ConfigurationError(f"missing production settings: {', '.join(missing)}")
        for key in ("database_url_ref", "redis_url_ref", "endpoint_ca_certificate_ref"):
            if not str(values[key]).startswith(("env://", "file://", "vault://")):
                raise ConfigurationError(f"{key} must be a secret or file reference")
