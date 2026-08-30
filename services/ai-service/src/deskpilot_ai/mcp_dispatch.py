from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import uuid
from dataclasses import asdict,dataclass
from typing import Literal

MAX_ENVELOPE_TTL_SECONDS=120
MCP_NAMESPACE=uuid.UUID("35f21bad-209c-5f40-b203-bcc66c539c34")


class MCPDenied(ValueError):pass


@dataclass(frozen=True)
class EndpointAttestation:
 tenant_id:str;device_id:str;agent_id:str;certificate_fingerprint:str;agent_build:str;policy_fingerprint:str;health:Literal["healthy","degraded","quarantined"];attested_at:str;attestation_sha256:str

@dataclass(frozen=True)
class AuthorizedCapability:
 tenant_id:str;incident_id:str;device_id:str;tool_id:str;tool_version:str;capability_id:str;parameters:dict[str,object];authorization_decision_sha256:str;plan_sha256:str|None

@dataclass(frozen=True)
class MCPEnvelope:
 envelope_id:str;tenant_id:str;incident_id:str;device_id:str;endpoint_agent_id:str;tool_id:str;tool_version:str;capability_id:str;parameters:dict[str,object];authorization_decision_sha256:str;plan_sha256:str|None;nonce:str;issued_at:str;expires_at:str;signature_sha256:str

@dataclass(frozen=True)
class MCPResult:
 envelope_id:str;nonce:str;tenant_id:str;incident_id:str;device_id:str;tool_id:str;tool_version:str;status:Literal["success","partial","failure","timeout"];typed_fields:dict[str,object];evidence_ids:tuple[str,...];content_included:bool;result_sha256:str;signature_sha256:str

def _canonical(value:object)->bytes:return json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()
def _digest(value:object)->str:return hashlib.sha256(_canonical(value)).hexdigest()
def _parse(value:str)->dt.datetime:
 parsed=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
 if parsed.tzinfo is None:raise MCPDenied("timezone-aware timestamp required")
 return parsed.astimezone(dt.timezone.utc)

def dispatch(capability:AuthorizedCapability,attestation:EndpointAttestation,*,now:dt.datetime,ttl_seconds:int,signing_key:bytes,approved_agent_builds:frozenset[str],expected_policy_fingerprint:str)->MCPEnvelope:
 if len(signing_key)<32 or now.tzinfo is None or not 1<=ttl_seconds<=MAX_ENVELOPE_TTL_SECONDS:raise MCPDenied("invalid dispatch security parameters")
 if attestation.health!="healthy" or attestation.tenant_id!=capability.tenant_id or attestation.device_id!=capability.device_id or attestation.agent_build not in approved_agent_builds or attestation.policy_fingerprint!=expected_policy_fingerprint:raise MCPDenied("endpoint attestation rejected")
 if any(len(x)!=64 for x in (attestation.certificate_fingerprint,attestation.attestation_sha256,capability.authorization_decision_sha256)):raise MCPDenied("attestation or authorization provenance missing")
 stable=":".join((capability.tenant_id,capability.incident_id,capability.device_id,capability.tool_id,capability.tool_version,capability.authorization_decision_sha256));eid=str(uuid.uuid5(MCP_NAMESPACE,stable));nonce=_digest((stable,attestation.attestation_sha256,now.isoformat()))[:32]
 issued=now.astimezone(dt.timezone.utc);expires=issued+dt.timedelta(seconds=ttl_seconds)
 claims={"envelope_id":eid,"tenant_id":capability.tenant_id,"incident_id":capability.incident_id,"device_id":capability.device_id,"endpoint_agent_id":attestation.agent_id,"tool_id":capability.tool_id,"tool_version":capability.tool_version,"capability_id":capability.capability_id,"parameters":capability.parameters,"authorization_decision_sha256":capability.authorization_decision_sha256,"plan_sha256":capability.plan_sha256,"nonce":nonce,"issued_at":issued.isoformat().replace("+00:00","Z"),"expires_at":expires.isoformat().replace("+00:00","Z")}
 sig=hmac.new(signing_key,_canonical(claims),hashlib.sha256).hexdigest();return MCPEnvelope(**claims,signature_sha256=sig)

def validate_result(envelope:MCPEnvelope,result:MCPResult,*,now:dt.datetime,signing_key:bytes,seen_nonces:frozenset[str],allowed_result_keys:frozenset[str])->dict[str,object]:
 claims=asdict(envelope);signature=claims.pop("signature_sha256")
 if not hmac.compare_digest(signature,hmac.new(signing_key,_canonical(claims),hashlib.sha256).hexdigest()):raise MCPDenied("MCP envelope tampered")
 if now.tzinfo is None or now.astimezone(dt.timezone.utc)>_parse(envelope.expires_at):raise MCPDenied("MCP envelope expired")
 if envelope.nonce in seen_nonces or result.nonce!=envelope.nonce:raise MCPDenied("MCP nonce replay or mismatch")
 if (result.envelope_id,result.tenant_id,result.incident_id,result.device_id,result.tool_id,result.tool_version)!=(envelope.envelope_id,envelope.tenant_id,envelope.incident_id,envelope.device_id,envelope.tool_id,envelope.tool_version):raise MCPDenied("MCP result scope mismatch")
 if result.content_included or not set(result.typed_fields)<=allowed_result_keys or any(not isinstance(v,(str,int,float,bool,type(None))) for v in result.typed_fields.values()):raise MCPDenied("unbounded MCP result")
 if not result.evidence_ids or len(result.result_sha256)!=64:raise MCPDenied("MCP result evidence missing")
 result_claims=asdict(result);result_sig=result_claims.pop("signature_sha256")
 if not hmac.compare_digest(result_sig,hmac.new(signing_key,_canonical(result_claims),hashlib.sha256).hexdigest()):raise MCPDenied("MCP result signature invalid")
 lineage=_digest((envelope.authorization_decision_sha256,envelope.envelope_id,result.result_sha256,result.evidence_ids))
 return {"mcp_dispatch_status":"validated","mcp_envelope_id":envelope.envelope_id,"mcp_result_status":result.status,"mcp_result_sha256":result.result_sha256,"mcp_evidence_ids":result.evidence_ids,"mcp_evidence_lineage_sha256":lineage,"consumed_nonce":envelope.nonce}

def quarantine(attestation:EndpointAttestation,reason:str)->dict[str,str]:
 if not reason.strip():raise MCPDenied("quarantine reason required")
 return {"endpoint_agent_id":attestation.agent_id,"device_id":attestation.device_id,"status":"quarantined","reason":reason,"quarantine_sha256":_digest((attestation.attestation_sha256,reason))}
