from __future__ import annotations
import hashlib,json,re
from dataclasses import dataclass,field
from typing import Literal
PII=re.compile(r"(?i)([\w.+-]+@[\w.-]+|\b\d{6,}\b|\\\\[\w.-]+\\[\w.$-]+)")
class KnowledgeDenied(ValueError):pass
@dataclass(frozen=True)
class Actor:subject:str;tenant_id:str;roles:frozenset[str];authenticated:bool
@dataclass(frozen=True)
class Candidate:
 candidate_id:str;tenant_id:str;author_id:str;title:str;symptoms:tuple[str,...];resolution_steps:tuple[str,...];evidence_ids:tuple[str,...];source_closure_sha256:str;quality_scores:dict[str,float];duplicate_of:str|None;content_sha256:str
@dataclass(frozen=True)
class Version:version_id:str;candidate_id:str;tenant_id:str;version:int;content_sha256:str;status:Literal["published","retired","rolled_back"];approved_by_sha256:str;index_generation:int;index_refresh_sha256:str
@dataclass
class Record:candidate:Candidate;status:str="review";versions:list[Version]=field(default_factory=list)
def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
class KnowledgeStore:
 def __init__(self)->None:self.rows:dict[str,Record]={};self.index_generation:dict[str,int]={}
 def submit(self,actor:Actor,candidate:Candidate)->Record:
  self._scope(actor,candidate.tenant_id)
  if actor.subject!=candidate.author_id or not actor.roles.intersection({"service_desk_engineer","knowledge_author"}):raise KnowledgeDenied("author denied")
  if candidate.candidate_id in self.rows:raise KnowledgeDenied("candidate immutable")
  content=(candidate.title,)+candidate.symptoms+candidate.resolution_steps
  if any(PII.search(value) for value in content):raise KnowledgeDenied("candidate not de-identified")
  if not candidate.evidence_ids or len(candidate.source_closure_sha256)!=64:raise KnowledgeDenied("provenance required")
  if candidate.content_sha256!=_digest(content):raise KnowledgeDenied("content digest mismatch")
  if any(not 0<=score<=1 for score in candidate.quality_scores.values()):raise KnowledgeDenied("quality score invalid")
  record=Record(candidate);self.rows[candidate.candidate_id]=record;return record
 def publish(self,actor:Actor,candidate_id:str,minimums:dict[str,float])->Version:
  record=self._record(actor,candidate_id);candidate=record.candidate
  if actor.subject==candidate.author_id or not actor.roles.intersection({"knowledge_approver","technical_approver"}):raise KnowledgeDenied("independent approval required")
  if record.status not in {"review","retired"}:raise KnowledgeDenied("publication state denied")
  if candidate.duplicate_of:raise KnowledgeDenied("duplicate candidate cannot publish")
  if any(candidate.quality_scores.get(key,0)<value for key,value in minimums.items()):raise KnowledgeDenied("quality gate failed")
  generation=self.index_generation.get(candidate.tenant_id,0)+1;self.index_generation[candidate.tenant_id]=generation;number=len(record.versions)+1;refresh=_digest((candidate.tenant_id,candidate.content_sha256,generation))
  version=Version(f"{candidate_id}-v{number}",candidate_id,candidate.tenant_id,number,candidate.content_sha256,"published",_digest(actor.subject),generation,refresh);record.versions.append(version);record.status="published";return version
 def retire(self,actor:Actor,candidate_id:str)->Version:
  record=self._record(actor,candidate_id)
  if "knowledge_approver" not in actor.roles or record.status!="published":raise KnowledgeDenied("retirement denied")
  prior=record.versions[-1];version=Version(f"{candidate_id}-v{len(record.versions)+1}",candidate_id,record.candidate.tenant_id,len(record.versions)+1,prior.content_sha256,"retired",_digest(actor.subject),prior.index_generation+1,_digest((prior.index_refresh_sha256,"retired")));record.versions.append(version);record.status="retired";return version
 def rollback(self,actor:Actor,candidate_id:str,target_version:int)->Version:
  record=self._record(actor,candidate_id)
  if "knowledge_approver" not in actor.roles:raise KnowledgeDenied("rollback denied")
  target=next((version for version in record.versions if version.version==target_version and version.status=="published"),None)
  if not target:raise KnowledgeDenied("published target required")
  generation=self.index_generation.get(record.candidate.tenant_id,0)+1;self.index_generation[record.candidate.tenant_id]=generation;version=Version(f"{candidate_id}-v{len(record.versions)+1}",candidate_id,record.candidate.tenant_id,len(record.versions)+1,target.content_sha256,"rolled_back",_digest(actor.subject),generation,_digest((target.version_id,generation)));record.versions.append(version);record.status="published";return version
 def _record(self,actor:Actor,candidate_id:str)->Record:
  record=self.rows.get(candidate_id)
  if not record:raise KnowledgeDenied("candidate not found")
  self._scope(actor,record.candidate.tenant_id);return record
 def _scope(self,actor:Actor,tenant_id:str)->None:
  if not actor.authenticated or actor.tenant_id!=tenant_id:raise KnowledgeDenied("authenticated tenant scope required")
