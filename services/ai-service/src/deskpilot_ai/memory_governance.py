from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Literal

MemoryClass = Literal["working", "episodic", "reusable_knowledge"]
MAX_TTL_DAYS = {"working":1, "episodic":30, "reusable_knowledge":365}
MEMORY_NAMESPACE = uuid.UUID("234ea9d4-a9e3-5df3-91a0-f16ce8d54e95")


class MemoryDenied(ValueError):
    pass


@dataclass(frozen=True)
class MemoryRequest:
    tenant_id: str
    subject_id: str
    incident_id: str | None
    memory_class: MemoryClass
    purpose: Literal["active_incident", "support_continuity", "curated_knowledge"]
    consent_status: Literal["not_required", "granted", "declined", "revoked"]
    content_fingerprint: str
    source_provenance_sha256: str
    sensitivity: Literal["internal", "sensitive"]
    encrypted: bool
    human_curated: bool
    ttl_days: int


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    tenant_id: str
    subject_id: str
    incident_id: str | None
    memory_class: MemoryClass
    purpose: str
    content_fingerprint: str
    source_provenance_sha256: str
    sensitivity: str
    encrypted: bool
    consent_status: str
    human_curated: bool
    created_at: str
    expires_at: str
    status: Literal["active", "deleted"]
    record_sha256: str


@dataclass(frozen=True)
class RecallScope:
    tenant_id: str
    subject_id: str
    incident_id: str | None
    purpose: str
    allowed_classes: frozenset[MemoryClass]


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def create_record(request: MemoryRequest, *, created_at: dt.datetime) -> MemoryRecord:
    if created_at.tzinfo is None or len(request.content_fingerprint)!=64 or len(request.source_provenance_sha256)!=64: raise MemoryDenied("memory provenance incomplete")
    if not 1<=request.ttl_days<=MAX_TTL_DAYS[request.memory_class]: raise MemoryDenied("memory TTL exceeds policy")
    if request.sensitivity=="sensitive" and not request.encrypted: raise MemoryDenied("sensitive memory requires encryption")
    if request.memory_class=="working":
        if request.purpose!="active_incident" or not request.incident_id: raise MemoryDenied("working memory is incident scoped")
    elif request.memory_class=="episodic":
        if request.purpose!="support_continuity" or request.consent_status!="granted": raise MemoryDenied("episodic memory requires scoped consent")
    else:
        if request.purpose!="curated_knowledge" or not request.human_curated or request.consent_status not in {"not_required","granted"}: raise MemoryDenied("reusable knowledge requires human curation")
    stable=":".join((request.tenant_id,request.subject_id,request.incident_id or "none",request.memory_class,request.purpose,request.content_fingerprint));memory_id=str(uuid.uuid5(MEMORY_NAMESPACE,stable))
    created=created_at.astimezone(dt.timezone.utc);expires=created+dt.timedelta(days=request.ttl_days)
    payload={**request.__dict__,"memory_id":memory_id,"created_at":created.isoformat(),"expires_at":expires.isoformat()}
    return MemoryRecord(memory_id,request.tenant_id,request.subject_id,request.incident_id,request.memory_class,request.purpose,request.content_fingerprint,request.source_provenance_sha256,request.sensitivity,request.encrypted,request.consent_status,request.human_curated,created.isoformat().replace("+00:00","Z"),expires.isoformat().replace("+00:00","Z"),"active",_digest(payload))


def recall(records: tuple[MemoryRecord,...], scope: RecallScope, *, now: dt.datetime) -> tuple[MemoryRecord,...]:
    if now.tzinfo is None: raise MemoryDenied("timezone-aware recall required")
    selected=[]
    for item in records:
        if item.status!="active" or item.tenant_id!=scope.tenant_id or item.subject_id!=scope.subject_id or item.memory_class not in scope.allowed_classes or item.purpose!=scope.purpose: continue
        if now.astimezone(dt.timezone.utc)>dt.datetime.fromisoformat(item.expires_at.replace("Z","+00:00")): continue
        if item.memory_class=="working" and item.incident_id!=scope.incident_id: continue
        if item.memory_class=="episodic" and item.consent_status!="granted": continue
        selected.append(item)
    return tuple(sorted(selected,key=lambda x:(x.memory_class,x.created_at,x.memory_id)))


def resolve_conflicts(records: tuple[MemoryRecord,...]) -> tuple[MemoryRecord,...]:
    groups: dict[tuple[str,str,str,str],list[MemoryRecord]]={}
    for item in records:groups.setdefault((item.tenant_id,item.subject_id,item.memory_class,item.purpose),[]).append(item)
    resolved=[]
    for items in groups.values():
        fingerprints={x.content_fingerprint for x in items}
        if len(fingerprints)>1: raise MemoryDenied("conflicting durable memory requires human resolution")
        resolved.append(max(items,key=lambda x:(x.created_at,x.memory_id)))
    return tuple(sorted(resolved,key=lambda x:x.memory_id))


def delete_record(record: MemoryRecord, *, deletion_actor_id: str, reason: str) -> dict[str,str]:
    if not deletion_actor_id or not reason.strip(): raise MemoryDenied("authorized deletion reason required")
    tombstone=_digest({"memory_id":record.memory_id,"record":record.record_sha256,"actor":deletion_actor_id,"reason":reason})
    return {"memory_id":record.memory_id,"status":"deleted","deletion_actor_id":deletion_actor_id,"deletion_reason":reason,"tombstone_sha256":tombstone}
