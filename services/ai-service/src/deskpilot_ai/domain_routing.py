from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Iterable,Literal
Domain=Literal["outlook","printer","scanner","windows_network"]
SUPPORTED_DOMAINS:tuple[Domain,...]=("outlook","printer","scanner","windows_network")
DOMAIN_NODES={"outlook":"outlook_specialist","printer":"printer_specialist","scanner":"scanner_specialist","windows_network":"windows_network_specialist"}
MIN_CONFIDENCE=.72;MIN_MARGIN=.15;MAX_CANDIDATES=4;MAX_CLARIFICATION_ROUNDS=3;MAX_PARALLEL_DOMAINS=2
@dataclass(frozen=True)
class DomainScore:domain:str;confidence:float;evidence_codes:tuple[str,...]=()
@dataclass(frozen=True)
class DomainRoute:
 outcome:Literal["single","parallel","clarify","escalate"]
 domains:tuple[Domain,...]
 next_nodes:tuple[str,...]
 reason:str
 confidence:float
 provenance_sha256:str
def _digest(payload:object)->str:return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def select_domain_route(candidates:Iterable[DomainScore],*,clarification_rounds:int)->DomainRoute:
 raw=tuple(candidates)
 canonical=tuple(sorted(raw,key=lambda x:(-x.confidence,x.domain,x.evidence_codes)))
 audit=[{"domain":x.domain,"confidence":x.confidence,"evidence_codes":list(x.evidence_codes)} for x in canonical]
 def result(outcome,domains,nodes,reason,confidence):return DomainRoute(outcome,domains,nodes,reason,confidence,_digest({"candidates":audit,"clarification_rounds":clarification_rounds,"reason":reason}))
 if clarification_rounds<0:return result("escalate",(),("escalate",),"invalid_clarification_count",0.0)
 if not canonical:return result("clarify",(),("clarification",),"no_domain_candidates",0.0)
 if len(canonical)>MAX_CANDIDATES or any(x.domain not in SUPPORTED_DOMAINS or isinstance(x.confidence,bool) or not 0<=x.confidence<=1 for x in canonical):return result("escalate",(),("escalate",),"invalid_candidate_set",0.0)
 if len({x.domain for x in canonical})!=len(canonical):return result("escalate",(),("escalate",),"duplicate_domain_candidate",0.0)
 top=canonical[0]
 if top.confidence<MIN_CONFIDENCE:
  if clarification_rounds>=MAX_CLARIFICATION_ROUNDS:return result("escalate",(),("escalate",),"confidence_unresolved_after_limit",top.confidence)
  return result("clarify",(),("clarification",),"confidence_below_threshold",top.confidence)
 qualified=tuple(x for x in canonical if x.confidence>=MIN_CONFIDENCE)
 if len(qualified)>=2 and top.confidence-qualified[1].confidence<MIN_MARGIN:
  chosen=tuple(x.domain for x in qualified[:MAX_PARALLEL_DOMAINS]);return result("parallel",chosen,tuple(DOMAIN_NODES[x] for x in chosen),"multi_domain_evidence",top.confidence)
 return result("single",(top.domain,),(DOMAIN_NODES[top.domain],),"dominant_supported_domain",top.confidence)
def route_update(route:DomainRoute)->dict[str,object]:
 return {"domain":route.domains[0] if len(route.domains)==1 else "unknown","candidate_domains":route.domains,"domain_route_outcome":route.outcome,"domain_route_reason":route.reason,"domain_route_confidence":route.confidence,"domain_route_provenance_sha256":route.provenance_sha256}
