from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import hmac


class TokenVaultError(RuntimeError):
    pass


def _digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ProviderTokenSet:
    access_token: str
    access_expires_at: int
    refresh_token: str | None = None
    refresh_expires_at: int | None = None
    token_type: str = "Bearer"
    id_token: str | None = None


@dataclass(slots=True)
class TokenFamilyRecord:
    session_id: str
    tokens: ProviderTokenSet
    generation: int = 1
    used_refresh_hashes: set[str] = field(default_factory=set)
    compromised: bool = False


class InMemoryTokenVault:
    """Deterministic reference vault. Replace with encrypted KMS-backed storage in production."""

    def __init__(self) -> None:
        self._families: dict[str, TokenFamilyRecord] = {}

    def bind(self, session_id: str, tokens: ProviderTokenSet) -> None:
        self._families[session_id] = TokenFamilyRecord(session_id=session_id, tokens=tokens)

    def get(self, session_id: str) -> ProviderTokenSet | None:
        record = self._families.get(session_id)
        return None if record is None or record.compromised else record.tokens

    def rotate(self, session_id: str, *, presented_refresh_token: str, replacement: ProviderTokenSet) -> TokenFamilyRecord:
        record = self._families.get(session_id)
        if record is None or record.compromised:
            raise TokenVaultError("token_family_unavailable")
        current = record.tokens.refresh_token
        presented_hash = _digest(presented_refresh_token)
        if presented_hash in record.used_refresh_hashes:
            record.compromised = True
            raise TokenVaultError("refresh_token_reuse_detected")
        if current is None or not hmac.compare_digest(_digest(current), presented_hash):
            raise TokenVaultError("refresh_token_mismatch")
        record.used_refresh_hashes.add(presented_hash)
        record.tokens = replacement
        record.generation += 1
        return record

    def revoke(self, session_id: str) -> bool:
        return self._families.pop(session_id, None) is not None
