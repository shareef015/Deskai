from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

TrustSource = Literal["system", "policy", "authenticated_user", "retrieved_content", "endpoint_content", "tool_result"]
TRUST_RANK = {"system":5,"policy":4,"authenticated_user":3,"tool_result":2,"retrieved_content":1,"endpoint_content":1}
MAX_CONTENT_CHARS = 8000
INJECTION_PATTERNS = (
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|system)\s+instructions"),
    re.compile(r"(?i)(reveal|print|show|repeat)\s+(the\s+)?(system prompt|hidden instructions|developer message)"),
    re.compile(r"(?i)(act as|you are now)\s+(an?\s+)?(administrator|system|developer)"),
    re.compile(r"(?i)(execute|run)\s+(this\s+)?(powershell|shell|command|script)"),
)
SECRET_REQUEST = re.compile(r"(?i)(password|credential|private key|api key|access token|wifi key|vpn secret)")
PROHIBITED_TOOL_KEYS = frozenset({"command","script","shell","powershell","cmd","raw_input","authorization","credential","password","secret","token"})


class FirewallDenied(ValueError):
    pass


@dataclass(frozen=True)
class ContentBlock:
    block_id: str
    source: TrustSource
    content: str
    content_fingerprint: str
    tenant_id: str


@dataclass(frozen=True)
class FirewallDecision:
    outcome: Literal["allow", "isolate", "block"]
    trusted_instructions: tuple[str,...]
    isolated_data: tuple[dict[str,str],...]
    detections: tuple[str,...]
    sanitized_tool_args: dict[str,object]
    reason: str
    provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def _sanitize_args(args: dict[str,object], allowed_keys: frozenset[str]) -> dict[str,object]:
    if not set(args)<=allowed_keys or set(args)&PROHIBITED_TOOL_KEYS: raise FirewallDenied("tool arguments violate typed allowlist")
    sanitized={}
    for key,value in sorted(args.items()):
        if isinstance(value,str):
            if len(value)>512 or any(p.search(value) for p in INJECTION_PATTERNS) or SECRET_REQUEST.search(value): raise FirewallDenied("unsafe tool argument")
            sanitized[key]=value
        elif isinstance(value,(int,float,bool)) or value is None:sanitized[key]=value
        else: raise FirewallDenied("nested or executable tool argument prohibited")
    return sanitized


def inspect(*, tenant_id: str, blocks: tuple[ContentBlock,...], tool_args: dict[str,object], allowed_tool_arg_keys: frozenset[str]) -> FirewallDecision:
    if not tenant_id or not blocks or len({b.block_id for b in blocks})!=len(blocks): raise FirewallDenied("invalid firewall input")
    trusted=[];isolated=[];detections=[];block=False
    for item in sorted(blocks,key=lambda b:(-TRUST_RANK[b.source],b.block_id)):
        if item.tenant_id!=tenant_id or len(item.content)>MAX_CONTENT_CHARS or _digest(item.content)!=item.content_fingerprint: raise FirewallDenied("content scope, size, or fingerprint mismatch")
        found=[f"injection:{index}" for index,pattern in enumerate(INJECTION_PATTERNS) if pattern.search(item.content)]
        secret=bool(SECRET_REQUEST.search(item.content))
        if item.source in {"retrieved_content","endpoint_content","tool_result"}:
            if found:detections.extend(f"{item.block_id}:{code}" for code in found)
            if secret:detections.append(f"{item.block_id}:secret_reference")
            isolated.append({"block_id":item.block_id,"source":item.source,"data_fingerprint":item.content_fingerprint,"handling":"untrusted_data_only"})
        else:
            if item.source=="authenticated_user" and (found or secret):
                detections.extend(f"{item.block_id}:{code}" for code in found);detections.extend([f"{item.block_id}:secret_request"] if secret else []);block=True
            else: trusted.append(item.content)
    try:sanitized=_sanitize_args(tool_args,allowed_tool_arg_keys)
    except FirewallDenied as exc:
        detections.append("tool_args:blocked");sanitized={};block=True
    outcome="block" if block else "isolate" if isolated or detections else "allow"
    reason="security_violation" if block else "untrusted_content_isolated" if outcome=="isolate" else "trusted_content_only"
    payload={"tenant":tenant_id,"trusted_fingerprints":[_digest(x) for x in trusted],"isolated":isolated,"detections":sorted(set(detections)),"tool_args":sanitized,"outcome":outcome}
    return FirewallDecision(outcome,tuple(trusted),tuple(isolated),tuple(sorted(set(detections))),sanitized,reason,_digest(payload))
