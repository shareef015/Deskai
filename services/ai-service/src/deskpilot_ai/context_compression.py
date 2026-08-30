from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

MAX_CONTEXT_TOKENS = 12000
TARGET_COMPRESSED_TOKENS = 6000
MAX_SUMMARY_ITEMS = 80
PINNED_KEYS = frozenset({
    "tenant_id","incident_id","thread_id","checkpoint_id","employee_id","device_id","phase",
    "consent","approval","evidence_ids","contradiction_keys","selected_root_cause","remediation_plan_id",
    "remediation_plan_provenance_sha256","rollback_state","execution_status","verification_status",
    "human_decisions","budgets","audit_event_ids","agent_trace_head_sha256","state_version",
})


class CompressionError(ValueError):
    pass


@dataclass(frozen=True)
class HistoryItem:
    item_id: str
    sequence: int
    kind: Literal["message","decision","evidence","tool_result","transition","error"]
    redacted_summary: str
    source_fingerprint: str
    token_estimate: int
    freshness_epoch: int


@dataclass(frozen=True)
class CompressedContext:
    scope: dict[str,str]
    pinned_state: dict[str,object]
    summary_items: tuple[dict[str,object],...]
    covered_item_ids: tuple[str,...]
    source_head_sha256: str
    freshness_epoch: int
    original_token_estimate: int
    compressed_token_estimate: int
    compressor_version: str
    provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def compress(*, state: dict[str,object], history: tuple[HistoryItem,...], current_freshness_epoch: int) -> CompressedContext:
    missing=PINNED_KEYS-set(state)
    if missing: raise CompressionError(f"pinned state missing: {sorted(missing)}")
    if not history or len({x.item_id for x in history})!=len(history) or tuple(x.sequence for x in history)!=tuple(range(1,len(history)+1)):
        raise CompressionError("history must be unique and sequential")
    for item in history:
        if len(item.source_fingerprint)!=64 or item.token_estimate<0 or item.freshness_epoch>current_freshness_epoch: raise CompressionError("invalid history provenance or freshness")
    original=sum(x.token_estimate for x in history)
    pinned={key:state[key] for key in sorted(PINNED_KEYS)}
    scope={key:str(state[key]) for key in ("tenant_id","incident_id","thread_id","checkpoint_id")}
    candidates=history[-MAX_SUMMARY_ITEMS:]
    summary=tuple({"item_id":x.item_id,"sequence":x.sequence,"kind":x.kind,"summary":x.redacted_summary[:240],"source_fingerprint":x.source_fingerprint,"freshness_epoch":x.freshness_epoch} for x in candidates)
    compressed=min(TARGET_COMPRESSED_TOKENS,max(1,sum(max(1,len(str(x["summary"]))//4) for x in summary)+len(json.dumps(pinned))//4))
    source_head=_digest(tuple((x.item_id,x.sequence,x.source_fingerprint,x.freshness_epoch) for x in history))
    payload={"scope":scope,"pinned":pinned,"summary":summary,"covered":tuple(x.item_id for x in history),"source_head":source_head,"freshness":current_freshness_epoch,"original":original,"compressed":compressed,"version":"1.0.0"}
    return CompressedContext(scope,pinned,summary,tuple(x.item_id for x in history),source_head,current_freshness_epoch,original,compressed,"1.0.0",_digest(payload))


def should_compress(*, current_tokens: int, next_step_reserved_tokens: int) -> bool:
    if current_tokens<0 or next_step_reserved_tokens<0: raise CompressionError("invalid token estimate")
    return current_tokens+next_step_reserved_tokens>MAX_CONTEXT_TOKENS


def validate_rehydration(compressed: CompressedContext, *, live_state: dict[str,object], live_source_head_sha256: str, current_freshness_epoch: int) -> dict[str,object]:
    if compressed.compressor_version!="1.0.0" or len(compressed.provenance_sha256)!=64: raise CompressionError("unsupported compressed context")
    if live_source_head_sha256!=compressed.source_head_sha256: raise CompressionError("source history changed")
    if current_freshness_epoch!=compressed.freshness_epoch: raise CompressionError("compressed context is stale")
    for key in PINNED_KEYS:
        if live_state.get(key)!=compressed.pinned_state.get(key): raise CompressionError(f"pinned state changed: {key}")
    return {**compressed.pinned_state,"compressed_history":compressed.summary_items,"compressed_history_provenance_sha256":compressed.provenance_sha256,"context_original_tokens":compressed.original_token_estimate,"context_compressed_tokens":compressed.compressed_token_estimate}
