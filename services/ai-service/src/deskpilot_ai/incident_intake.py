from __future__ import annotations
import hashlib,re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
MAX_SOURCE_CHARS=4000;MAX_SUMMARY_CHARS=300;MAX_SYMPTOMS=8;MAX_SYMPTOM_CHARS=160;MAX_DOMAINS=4;MAX_UNCERTAIN=8;MAX_CLARIFICATIONS=4;MAX_EVIDENCE_REFS=16
DOMAINS=frozenset({"outlook","printer","scanner","windows_network"});IMPACTS=frozenset({"individual_low","individual_blocked","team_degraded","team_blocked","unknown"})
SECRET_PATTERNS=(re.compile(r"(?i)\b(password|passcode|otp|mfa|api[_ -]?key|private key)\b\s*[:=]\s*\S+"),re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"))
class IntakeValidationError(ValueError):pass
@dataclass(frozen=True)
class DomainCandidate:domain:str;confidence:float;source_span:tuple[int,int]
@dataclass(frozen=True)
class IntakeExtraction:
 summary:str;symptoms:tuple[str,...];business_impact:str;affected_device_id:str|None;timeline:str|None;domain_candidates:tuple[DomainCandidate,...];uncertain_fields:tuple[str,...];clarification_needs:tuple[str,...];evidence_references:tuple[str,...];source_digest:str;extraction_version:str="1.0.0"
def sanitize_source(text:str)->str:
 if not isinstance(text,str) or not text.strip() or len(text)>MAX_SOURCE_CHARS:raise IntakeValidationError("invalid source message")
 value=" ".join(text.split())
 for pattern in SECRET_PATTERNS:value=pattern.sub("[REDACTED]",value)
 return value
def source_digest(text:str)->str:return hashlib.sha256(sanitize_source(text).encode()).hexdigest()
def _valid_timeline(value:str|None)->bool:
 if value is None:return True
 try:datetime.fromisoformat(value.replace("Z","+00:00"));return True
 except ValueError:return value in {"just_now","today","yesterday","unknown"}
def validate_extraction(value:IntakeExtraction,*,sanitized_source:str,registered_device_ids:frozenset[str])->None:
 if not value.summary.strip() or len(value.summary)>MAX_SUMMARY_CHARS:raise IntakeValidationError("invalid summary")
 if not value.symptoms or len(value.symptoms)>MAX_SYMPTOMS or any(not x.strip() or len(x)>MAX_SYMPTOM_CHARS for x in value.symptoms):raise IntakeValidationError("invalid symptoms")
 if value.business_impact not in IMPACTS:raise IntakeValidationError("invalid business impact")
 if value.affected_device_id is not None and value.affected_device_id not in registered_device_ids:raise IntakeValidationError("unregistered device")
 if not _valid_timeline(value.timeline):raise IntakeValidationError("invalid timeline")
 if len(value.domain_candidates)>MAX_DOMAINS or len({x.domain for x in value.domain_candidates})!=len(value.domain_candidates):raise IntakeValidationError("invalid domain candidates")
 for candidate in value.domain_candidates:
  start,end=candidate.source_span
  if candidate.domain not in DOMAINS or isinstance(candidate.confidence,bool) or not 0<=candidate.confidence<=1 or not 0<=start<end<=len(sanitized_source):raise IntakeValidationError("invalid domain candidate")
 if len(value.uncertain_fields)>MAX_UNCERTAIN or len(set(value.uncertain_fields))!=len(value.uncertain_fields):raise IntakeValidationError("invalid uncertain fields")
 if len(value.clarification_needs)>MAX_CLARIFICATIONS or len(set(value.clarification_needs))!=len(value.clarification_needs):raise IntakeValidationError("invalid clarification needs")
 if len(value.evidence_references)>MAX_EVIDENCE_REFS or len(set(value.evidence_references))!=len(value.evidence_references):raise IntakeValidationError("invalid evidence references")
 if value.source_digest!=hashlib.sha256(sanitized_source.encode()).hexdigest():raise IntakeValidationError("source digest mismatch")
 if value.business_impact=="unknown" and "business_impact" not in value.uncertain_fields:raise IntakeValidationError("unknown impact must be explicit")
 if value.affected_device_id is None and "affected_device_id" not in value.uncertain_fields:raise IntakeValidationError("missing device must be explicit")
def intake_state_update(value:IntakeExtraction,*,sanitized_source:str,registered_device_ids:frozenset[str])->dict[str,object]:
 validate_extraction(value,sanitized_source=sanitized_source,registered_device_ids=registered_device_ids)
 needs_clarification=bool(value.clarification_needs or value.uncertain_fields)
 return {"phase":"clarification" if needs_clarification else "classification","incident_summary":value.summary,"symptoms":value.symptoms,"business_impact":value.business_impact,"affected_device_id":value.affected_device_id,"reported_timeline":value.timeline,"domain_candidates":tuple({"domain":x.domain,"confidence":x.confidence,"source_span":x.source_span} for x in value.domain_candidates),"uncertain_fields":value.uncertain_fields,"clarification_needs":value.clarification_needs,"intake_evidence_references":value.evidence_references,"intake_source_digest":value.source_digest,"intake_extraction_version":value.extraction_version}
