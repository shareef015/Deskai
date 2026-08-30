from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from typing import Literal

CacheClass = Literal["prompt", "embedding", "retrieval", "response"]
MAX_TTL_SECONDS = {"prompt":86400, "embedding":604800, "retrieval":1800, "response":600}
MIN_RESPONSE_SIMILARITY = 0.94
MIN_RETRIEVAL_SIMILARITY = 0.90
HIGH_RISK_BYPASS_STAGES = frozenset({"evidence_fusion", "remediation_planning", "approval", "execution", "verification", "closure", "escalation"})


class CacheDenied(ValueError):
    pass


@dataclass(frozen=True)
class CacheContext:
    tenant_id: str
    cache_class: CacheClass
    task_stage: str
    risk: Literal["low", "medium", "high"]
    data_class: Literal["public", "internal", "sensitive"]
    model_id: str
    model_release: str
    prompt_fingerprint: str
    config_fingerprint: str
    index_fingerprint: str
    policy_fingerprint: str
    normalized_input_fingerprint: str


@dataclass(frozen=True)
class CacheEntry:
    key_sha256: str
    tenant_id: str
    cache_class: CacheClass
    created_at: str
    expires_at: str
    encrypted: bool
    release_fingerprint: str
    grounding_evidence_ids: tuple[str, ...]
    grounding_fingerprint: str | None
    value_fingerprint: str
    estimated_cost_saved_microusd: int


@dataclass(frozen=True)
class CacheLookup:
    outcome: Literal["hit", "miss", "bypass", "stale", "revalidation_failed"]
    key_sha256: str
    reason: str
    cost_saved_microusd: int
    requires_fill_lease: bool


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def cache_key(context: CacheContext) -> str:
    fields = context.__dict__
    if not all(isinstance(value,str) and value for value in fields.values() if isinstance(value,str)):
        raise CacheDenied("cache context incomplete")
    return _digest(fields)


def cache_eligible(context: CacheContext) -> tuple[bool,str]:
    if context.risk == "high" or context.task_stage in HIGH_RISK_BYPASS_STAGES:
        return False,"high_risk_or_governed_stage"
    if context.cache_class == "response" and context.data_class == "sensitive":
        return False,"sensitive_response_bypass"
    return True,"eligible"


def create_entry(context: CacheContext, *, created_at: dt.datetime, ttl_seconds: int, encrypted: bool, grounding_evidence_ids: tuple[str,...], grounding_fingerprint: str | None, value_fingerprint: str, estimated_cost_saved_microusd: int) -> CacheEntry:
    eligible,reason=cache_eligible(context)
    if not eligible: raise CacheDenied(reason)
    if created_at.tzinfo is None or not 1 <= ttl_seconds <= MAX_TTL_SECONDS[context.cache_class]: raise CacheDenied("invalid TTL")
    if context.data_class == "sensitive" and not encrypted: raise CacheDenied("sensitive cache must be encrypted")
    if len(value_fingerprint)!=64: raise CacheDenied("value fingerprint required")
    if context.cache_class in {"retrieval","response"} and (not grounding_evidence_ids or not grounding_fingerprint or len(grounding_fingerprint)!=64): raise CacheDenied("grounding metadata required")
    created=created_at.astimezone(dt.timezone.utc);expires=created+dt.timedelta(seconds=ttl_seconds)
    release=_digest((context.model_id,context.model_release,context.prompt_fingerprint,context.config_fingerprint,context.index_fingerprint,context.policy_fingerprint))
    return CacheEntry(cache_key(context),context.tenant_id,context.cache_class,created.isoformat().replace("+00:00","Z"),expires.isoformat().replace("+00:00","Z"),encrypted,release,grounding_evidence_ids,grounding_fingerprint,value_fingerprint,max(0,estimated_cost_saved_microusd))


def lookup(context: CacheContext, entry: CacheEntry | None, *, now: dt.datetime, similarity: float, current_grounding_fingerprint: str | None, fill_lease_held: bool=False) -> CacheLookup:
    key=cache_key(context);eligible,reason=cache_eligible(context)
    if not eligible:return CacheLookup("bypass",key,reason,0,False)
    if entry is None:return CacheLookup("miss",key,"not_found",0,not fill_lease_held)
    if entry.key_sha256!=key or entry.tenant_id!=context.tenant_id or entry.cache_class!=context.cache_class:return CacheLookup("miss",key,"scope_or_key_mismatch",0,not fill_lease_held)
    if now.tzinfo is None or now.astimezone(dt.timezone.utc)>dt.datetime.fromisoformat(entry.expires_at.replace("Z","+00:00")):return CacheLookup("stale",key,"expired",0,not fill_lease_held)
    expected_release=_digest((context.model_id,context.model_release,context.prompt_fingerprint,context.config_fingerprint,context.index_fingerprint,context.policy_fingerprint))
    if entry.release_fingerprint!=expected_release:return CacheLookup("stale",key,"release_invalidated",0,not fill_lease_held)
    minimum=MIN_RESPONSE_SIMILARITY if context.cache_class=="response" else MIN_RETRIEVAL_SIMILARITY if context.cache_class=="retrieval" else 1.0
    if similarity<minimum:return CacheLookup("miss",key,"similarity_below_threshold",0,not fill_lease_held)
    if context.cache_class in {"retrieval","response"} and current_grounding_fingerprint!=entry.grounding_fingerprint:return CacheLookup("revalidation_failed",key,"grounding_changed",0,not fill_lease_held)
    return CacheLookup("hit",key,"validated_hit",entry.estimated_cost_saved_microusd,False)
