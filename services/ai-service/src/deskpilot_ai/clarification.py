from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
MAX_QUESTIONS=2;MAX_ROUNDS=3;MAX_QUESTION_CHARS=180;MAX_NEEDS=12
PRIORITY={"safety":0,"affected_device_id":1,"symptom":2,"business_impact":3,"timeline":4,"domain":5,"contradiction":6,"optional":7}
QUESTION_CATALOG={
 "affected_device_id":("affected_device_id","Which registered Windows device is affected?",10),
 "symptoms":("symptom","What exactly happens when you try, including any visible error message?",9),
 "business_impact":("business_impact","Is only your work affected, or are other people blocked too?",8),
 "reported_timeline":("timeline","When did this issue begin?",6),
 "domain":("domain","Is the problem with Outlook, printing, scanning, or Windows network access?",7)}
class ClarificationError(ValueError):pass
@dataclass(frozen=True)
class ClarificationNeed:question_id:str;field:str;category:str;question:str;information_gain:int
@dataclass(frozen=True)
class ClarificationPlan:
 outcome:Literal["ask","complete","escalated"];questions:tuple[ClarificationNeed,...];round_number:int;reason:str;provenance_sha256:str
def build_needs(*,missing_fields:tuple[str,...],contradiction_keys:tuple[str,...])->tuple[ClarificationNeed,...]:
 needs=[]
 for field in sorted(set(missing_fields)):
  if field in QUESTION_CATALOG:
   category,question,gain=QUESTION_CATALOG[field];needs.append(ClarificationNeed(f"field:{field}",field,category,question,gain))
 for key in sorted(set(contradiction_keys)):
  needs.append(ClarificationNeed(f"contradiction:{key}",key,"contradiction",f"I found conflicting information about {key.replace(':',' ')}. What do you currently observe?",8))
 if len(needs)>MAX_NEEDS:raise ClarificationError("too many clarification needs")
 return tuple(needs)
def plan_clarification(*,needs:tuple[ClarificationNeed,...],answered_fields:frozenset[str],asked_question_ids:frozenset[str],round_number:int)->ClarificationPlan:
 if round_number<0:raise ClarificationError("invalid clarification round")
 remaining=tuple(x for x in needs if x.field not in answered_fields and x.question_id not in asked_question_ids)
 if not remaining:
  payload={"outcome":"complete","round":round_number,"questions":[]};return ClarificationPlan("complete",(),round_number,"no_unresolved_clarification",hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest())
 if round_number>=MAX_ROUNDS:
  payload={"outcome":"escalated","round":round_number,"remaining":[x.question_id for x in remaining]};return ClarificationPlan("escalated",(),round_number,"clarification_round_limit_exceeded",hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest())
 for need in remaining:
  if need.category not in PRIORITY or not need.question.strip() or len(need.question)>MAX_QUESTION_CHARS or "password" in need.question.lower() or "mfa" in need.question.lower():raise ClarificationError("unsafe or invalid clarification need")
 selected=tuple(sorted(remaining,key=lambda x:(PRIORITY[x.category],-x.information_gain,x.question_id))[:MAX_QUESTIONS]);payload={"outcome":"ask","round":round_number+1,"questions":[x.question_id for x in selected]};return ClarificationPlan("ask",selected,round_number+1,"highest_information_unanswered_needs",hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest())
def clarification_state_update(plan:ClarificationPlan,asked_question_ids:frozenset[str])->dict[str,object]:
 phase="clarification" if plan.outcome=="ask" else "classification" if plan.outcome=="complete" else "escalated"
 return {"phase":phase,"final_status":"escalated" if phase=="escalated" else None,"clarification_round":plan.round_number,"clarification_questions":tuple(x.question for x in plan.questions),"asked_clarification_ids":tuple(sorted(asked_question_ids|{x.question_id for x in plan.questions})),"clarification_reason":plan.reason,"clarification_provenance_sha256":plan.provenance_sha256}
