from __future__ import annotations
import hashlib,json,re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
MAX_TURNS=40;MAX_QUESTIONS=2;MAX_RESPONSE_CHARS=1200;MAX_SUMMARY_CHARS=500
SECRET_PATTERNS=(re.compile(r"(?i)\b(password|passcode|mfa|otp|private key)\b\s*[:=]\s*\S+"),re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"))
class ConversationError(ValueError):pass
@dataclass(frozen=True)
class ConversationContext:
 employee_display_name:str|None;local_time:datetime;turn_count:int;incident_id:str|None;device_display_name:str|None;intent_summary:str|None;consent_status:Literal["not_requested","pending","granted","declined","revoked","expired"];locale:str="en"
@dataclass(frozen=True)
class ConversationResponse:
 message:str;outcome:Literal["continue","request_consent","handoff","cancelled","escalated"];intent_summary:str|None;questions:tuple[str,...];provenance_sha256:str
def greeting(local_time:datetime,name:str|None=None)->str:
 hour=local_time.hour
 period="morning" if 5<=hour<12 else "afternoon" if 12<=hour<17 else "evening" if 17<=hour<22 else None
 salutation=f"Good {period}" if period else "Hello"
 return f"{salutation}{', '+name.strip() if name and name.strip() else ''}. How can I help you?"
def safe_summary(text:str|None)->str|None:
 if not text:return None
 value=" ".join(text.split())
 for pattern in SECRET_PATTERNS:value=pattern.sub("[REDACTED]",value)
 return value[:MAX_SUMMARY_CHARS]
def _response(message:str,outcome,summary,questions=())->ConversationResponse:
 if len(questions)>MAX_QUESTIONS:raise ConversationError("too many questions")
 if len(message)>MAX_RESPONSE_CHARS:raise ConversationError("response too long")
 payload={"message":message,"outcome":outcome,"intent_summary":summary,"questions":questions};return ConversationResponse(message,outcome,summary,questions,hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest())
def begin(context:ConversationContext)->ConversationResponse:
 if context.locale!="en":return _response("A support engineer will continue in your preferred language.","handoff",safe_summary(context.intent_summary))
 if context.turn_count<0:return _response("I’m unable to continue this session safely. A support engineer can help you.","escalated",safe_summary(context.intent_summary))
 return _response(greeting(context.local_time,context.employee_display_name),"continue",safe_summary(context.intent_summary),("How can I help you?",))
def continue_conversation(context:ConversationContext,employee_message:str,*,intent_complete:bool,needs_diagnostics:bool=False)->ConversationResponse:
 summary=safe_summary(context.intent_summary or employee_message)
 if context.turn_count>=MAX_TURNS:return _response("We have reached the safe conversation limit. I’ll preserve the incident details for a support engineer to continue.","escalated",summary)
 normalized=employee_message.strip().lower()
 if normalized in {"cancel","stop","never mind","nevermind"}:return _response("Understood. I have stopped this support conversation. No new diagnostics or changes will be performed.","cancelled",summary)
 if context.consent_status in {"declined","revoked","expired"} and needs_diagnostics:return _response("I will not connect to the device or run diagnostics. I can provide general guidance or hand this incident to a support engineer.","handoff",summary)
 if not intent_complete:return _response("I’ll keep the details you already provided. Which Windows device is affected, and what happens when you try?","continue",summary,("Which Windows device is affected?","What happens when you try?"))
 if needs_diagnostics and context.consent_status=="not_requested":
  device=f" on {context.device_display_name}" if context.device_display_name else " on the registered Windows device"
  return _response(f"I understand the issue. May I run read-only diagnostics{device}? This checks relevant status and configuration but does not make changes.","request_consent",summary,("Do you allow these read-only diagnostics?",))
 return _response("Thank you. I have kept the incident context and will continue with the next safe support step.","continue",summary)
def escalation_response(context:ConversationContext,reason:Literal["unsupported","low_confidence","technical_failure","approval_required"])->ConversationResponse:
 wording={"unsupported":"This request is outside the supported Windows service-desk scope.","low_confidence":"I do not have enough reliable information to continue safely.","technical_failure":"The automated support step could not complete safely.","approval_required":"A qualified approver or support engineer must review the proposed action."}[reason]
 return _response(f"{wording} I’ll preserve the incident summary so a support engineer can continue.","escalated",safe_summary(context.intent_summary))
