from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

PROHIBITED_PARAMETER_KEYS = frozenset({"command","script","shell","powershell","cmd","raw","credential","password","secret","token","authorization"})


class ToolDenied(ValueError):
    pass


@dataclass(frozen=True)
class ToolSchema:
    tool_id: str
    version: str
    capability: str
    risk: Literal["read_only","low","medium","high"]
    parameter_keys: frozenset[str]
    required_parameter_keys: frozenset[str]
    maximum_calls_per_minute: int
    requires_consent: bool
    requires_approval: bool
    dynamic: bool
    registry_fingerprint: str


@dataclass(frozen=True)
class AgentGrant:
    tenant_id: str
    agent_id: str
    capabilities: frozenset[str]
    tool_versions: frozenset[str]
    grant_fingerprint: str


@dataclass(frozen=True)
class ToolRequest:
    tenant_id: str
    incident_id: str
    device_id: str
    agent_id: str
    tool_id: str
    tool_version: str
    capability: str
    parameters: dict[str,object]
    consent_status: str
    approval_status: str
    approval_plan_sha256: str | None
    expected_plan_sha256: str | None
    calls_in_current_minute: int


@dataclass(frozen=True)
class AuthorizationDecision:
    outcome: Literal["allow","deny"]
    reason: str
    sanitized_parameters: dict[str,object]
    tool_registry_fingerprint: str
    grant_fingerprint: str
    decision_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()


def authorize(schema: ToolSchema, grant: AgentGrant, request: ToolRequest) -> AuthorizationDecision:
    reason="authorized";sanitized={};allow=True
    if schema.dynamic or not schema.tool_id or len(schema.registry_fingerprint)!=64: allow,reason=False,"dynamic_or_unregistered_tool"
    elif request.tenant_id!=grant.tenant_id or request.agent_id!=grant.agent_id or not all((request.incident_id,request.device_id)): allow,reason=False,"scope_mismatch"
    elif (request.tool_id,request.tool_version,request.capability)!=(schema.tool_id,schema.version,schema.capability): allow,reason=False,"schema_version_or_capability_mismatch"
    elif schema.capability not in grant.capabilities or f"{schema.tool_id}@{schema.version}" not in grant.tool_versions: allow,reason=False,"least_privilege_grant_denied"
    elif request.calls_in_current_minute>=schema.maximum_calls_per_minute: allow,reason=False,"rate_limit_exceeded"
    elif schema.requires_consent and request.consent_status!="granted": allow,reason=False,"consent_required"
    elif schema.requires_approval and (request.approval_status!="approved" or not request.approval_plan_sha256 or request.approval_plan_sha256!=request.expected_plan_sha256): allow,reason=False,"exact_approval_required"
    elif set(request.parameters)&PROHIBITED_PARAMETER_KEYS or not set(request.parameters)<=schema.parameter_keys or not schema.required_parameter_keys<=set(request.parameters): allow,reason=False,"parameter_schema_denied"
    else:
        for key,value in sorted(request.parameters.items()):
            if isinstance(value,str) and 0<len(value)<=256:sanitized[key]=value
            elif isinstance(value,(int,float,bool)) or value is None:sanitized[key]=value
            else:allow,reason=False,"parameter_type_or_size_denied";sanitized={};break
    payload={"scope":(request.tenant_id,request.incident_id,request.device_id),"agent":request.agent_id,"tool":f"{schema.tool_id}@{schema.version}","capability":schema.capability,"parameters":sanitized,"outcome":"allow" if allow else "deny","reason":reason,"registry":schema.registry_fingerprint,"grant":grant.grant_fingerprint}
    return AuthorizationDecision("allow" if allow else "deny",reason,sanitized,schema.registry_fingerprint,grant.grant_fingerprint,_digest(payload))
