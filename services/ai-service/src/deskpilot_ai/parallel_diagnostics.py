from __future__ import annotations
import asyncio,hashlib,json
from dataclasses import dataclass
from typing import Any,Awaitable,Callable,Literal
from .specialist_subgraphs import Domain,SpecialistOutput
from .state import EvidenceRecord
MAX_BRANCHES=2;BRANCH_TIMEOUT_SECONDS=15;MAX_EVIDENCE=64
BranchStatus=Literal["complete","partial","timeout","failed","cancelled"]
@dataclass(frozen=True)
class BranchResult:
 domain:Domain;status:BranchStatus;output:SpecialistOutput|None;safe_error:str|None=None
@dataclass(frozen=True)
class FanoutResult:
 status:Literal["complete","partial","contradictory","failed"]
 evidence:tuple[EvidenceRecord,...]
 hypotheses:tuple[str,...]
 branches:tuple[BranchResult,...]
 contradiction_keys:tuple[str,...]
 next_phase:Literal["evidence_fusion","clarification","escalated"]
 provenance_sha256:str
class EvidenceReductionError(ValueError):pass
def merge_evidence(branches:tuple[BranchResult,...],*,tenant_id:str,incident_id:str)->tuple[tuple[EvidenceRecord,...],tuple[str,...]]:
 unique:dict[tuple[str,str,str],EvidenceRecord]={};semantic:dict[tuple[str,str],set[str]]={}
 for branch in branches:
  for item in branch.output.evidence if branch.output else ():
   if item.get("tenant_id")!=tenant_id or item.get("incident_id")!=incident_id:raise EvidenceReductionError("cross-scope evidence")
   if item.get("content_included") is not False:raise EvidenceReductionError("raw evidence content prohibited")
   key=(tenant_id,incident_id,str(item["digest"]));existing=unique.get(key)
   if existing is None or str(item["evidence_id"])<str(existing["evidence_id"]):unique[key]=item
   semantic.setdefault((str(item["source"]),str(item["kind"])),set()).add(str(item["digest"]))
 ordered=tuple(sorted(unique.values(),key=lambda x:(str(x["observed_at"]),str(x["source"]),str(x["kind"]),str(x["evidence_id"]))))
 if len(ordered)>MAX_EVIDENCE:raise EvidenceReductionError("evidence limit exceeded")
 contradictions=tuple(sorted(f"{source}:{kind}" for (source,kind),digests in semantic.items() if len(digests)>1))
 return ordered,contradictions
async def _run(domain:Domain,runner:Callable[[Domain],Awaitable[SpecialistOutput]],timeout:float)->BranchResult:
 try:return BranchResult(domain,"complete",await asyncio.wait_for(runner(domain),timeout=timeout))
 except TimeoutError:return BranchResult(domain,"timeout",None,"branch_timeout")
 except asyncio.CancelledError:raise
 except Exception:return BranchResult(domain,"failed",None,"branch_failed")
async def fanout_diagnostics(domains:tuple[Domain,...],runner:Callable[[Domain],Awaitable[SpecialistOutput]],*,tenant_id:str,incident_id:str,timeout_seconds:float=BRANCH_TIMEOUT_SECONDS)->FanoutResult:
 if not domains or len(domains)>MAX_BRANCHES or len(set(domains))!=len(domains):raise ValueError("invalid diagnostic branches")
 if timeout_seconds<=0 or timeout_seconds>BRANCH_TIMEOUT_SECONDS:raise ValueError("invalid branch timeout")
 tasks=[asyncio.create_task(_run(domain,runner,timeout_seconds)) for domain in sorted(domains)]
 try:branches=tuple(await asyncio.gather(*tasks))
 except asyncio.CancelledError:
  for task in tasks:task.cancel()
  await asyncio.gather(*tasks,return_exceptions=True);raise
 evidence,contradictions=merge_evidence(branches,tenant_id=tenant_id,incident_id=incident_id)
 hypotheses=tuple(sorted({hypothesis for branch in branches if branch.output for hypothesis in branch.output.hypotheses}))
 successes=sum(branch.output is not None and branch.output.status in {"complete","insufficient_evidence","contradictory_evidence"} for branch in branches)
 if contradictions:status="contradictory";next_phase="evidence_fusion"
 elif successes==len(branches):status="complete";next_phase="evidence_fusion"
 elif successes>0:status="partial";next_phase="evidence_fusion" if evidence else "clarification"
 else:status="failed";next_phase="escalated"
 payload={"branches":[{"domain":x.domain,"status":x.status,"output_status":x.output.status if x.output else None} for x in branches],"evidence_ids":[x["evidence_id"] for x in evidence],"contradictions":contradictions,"next_phase":next_phase}
 provenance=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 return FanoutResult(status,evidence,hypotheses,branches,contradictions,next_phase,provenance)
def supervisor_fanout_handoff(result:FanoutResult)->dict[str,Any]:return {"phase":result.next_phase,"final_status":"escalated" if result.next_phase=="escalated" else None,"evidence":result.evidence,"hypotheses":result.hypotheses,"diagnostic_fanout_status":result.status,"contradiction_keys":result.contradiction_keys,"diagnostic_fanout_provenance_sha256":result.provenance_sha256}
