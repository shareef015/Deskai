from __future__ import annotations
from typing import Any,Mapping

def _interrupt(request:Mapping[str,Any])->dict[str,Any]:
 from langgraph.types import interrupt
 result=interrupt(dict(request))
 if not isinstance(result,dict) or result.get("validated_by_server") is not True or result.get("request_id")!=request.get("request_id") or result.get("kind")!=request.get("kind"):raise PermissionError("invalid interrupt resume envelope")
 return result
def diagnostic_consent_interrupt_node(state:Mapping[str,Any])->dict[str,Any]:
 decision=_interrupt(state["pending_interrupt"]);granted=decision["decision"]=="granted";return {"consent":{"status":"granted" if granted else "declined","consent_id":decision["decision_fingerprint"],"device_id":state["device_id"],"capabilities":tuple(state["pending_interrupt"]["capabilities"]),"expires_at":state["pending_interrupt"]["expires_at"]},"phase":"diagnosis" if granted else "cancelled","pending_interrupt":None}
def remediation_approval_interrupt_node(state:Mapping[str,Any])->dict[str,Any]:
 decision=_interrupt(state["pending_interrupt"]);approved=decision["decision"]=="approved";return {"approval":{"status":"approved" if approved else "rejected","approval_id":decision["decision_fingerprint"],"action_id":state["pending_interrupt"]["action_id"],"risk_level":state["pending_interrupt"]["risk_level"],"approver_id":decision["actor_id"],"expires_at":state["pending_interrupt"]["expires_at"]},"phase":"execution" if approved else "escalated","pending_interrupt":None}
def employee_confirmation_interrupt_node(state:Mapping[str,Any])->dict[str,Any]:
 decision=_interrupt(state["pending_interrupt"]);confirmed=decision["decision"]=="confirmed";return {"phase":"resolved" if confirmed else "escalated","final_status":"resolved" if confirmed else "escalated","pending_interrupt":None}
