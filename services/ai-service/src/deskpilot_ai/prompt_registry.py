from __future__ import annotations
import hashlib,json,re,string
from dataclasses import dataclass
from typing import Literal,Mapping,Any
SEMVER=re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$");SHA256=re.compile(r"^[0-9a-f]{64}$")
Lifecycle=Literal["draft","validated","approved","active","retired","rejected"]
class RegistryError(ValueError):pass
def canonical_sha256(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
@dataclass(frozen=True)
class PromptArtifact:
 artifact_id:str;name:str;version:str;status:Lifecycle;template:str;variables:tuple[str,...];input_schema_version:str;output_schema_version:str;author_id:str;content_sha256:str
@dataclass(frozen=True)
class AgentConfiguration:
 artifact_id:str;agent_name:str;version:str;status:Lifecycle;prompt_artifact_id:str;prompt_sha256:str;state_schema_version:str;input_schema_version:str;output_schema_version:str;allowed_tools:tuple[str,...];max_steps:int;max_tool_calls:int;max_tokens:int;author_id:str;content_sha256:str
@dataclass(frozen=True)
class EvaluationEvidence:groundedness:float;task_success:float;safety:float;regression_rate:float;suite_version:str;report_sha256:str
@dataclass(frozen=True)
class Approval:artifact_id:str;approver_id:str;approver_roles:frozenset[str];decision:Literal["approved","rejected"]
@dataclass(frozen=True)
class ReleaseBundle:
 release_id:str;tenant_id:str;prompt:PromptArtifact;agent:AgentConfiguration;evaluation:EvaluationEvidence;configuration_fingerprint:str
def make_prompt(*,artifact_id:str,name:str,version:str,template:str,variables:tuple[str,...],input_schema_version:str,output_schema_version:str,author_id:str,status:Lifecycle="draft")->PromptArtifact:
 if not artifact_id or not name or not author_id or not SEMVER.fullmatch(version):raise RegistryError("invalid prompt identity")
 fields=tuple(sorted({field for _,field,_,_ in string.Formatter().parse(template) if field}))
 if fields!=tuple(sorted(variables)) or len(set(variables))!=len(variables):raise RegistryError("prompt variables do not exactly match template")
 if any(token in template.lower() for token in ("password=","api_key=","private_key=")):raise RegistryError("secret-like prompt content prohibited")
 payload={"name":name,"version":version,"template":template,"variables":variables,"input_schema_version":input_schema_version,"output_schema_version":output_schema_version}
 return PromptArtifact(artifact_id,name,version,status,template,variables,input_schema_version,output_schema_version,author_id,canonical_sha256(payload))
def make_agent(*,artifact_id:str,agent_name:str,version:str,prompt:PromptArtifact,state_schema_version:str,input_schema_version:str,output_schema_version:str,allowed_tools:tuple[str,...],max_steps:int,max_tool_calls:int,max_tokens:int,author_id:str,status:Lifecycle="draft")->AgentConfiguration:
 if not artifact_id or not agent_name or not author_id or not SEMVER.fullmatch(version):raise RegistryError("invalid agent identity")
 if not all(SEMVER.fullmatch(x) for x in (state_schema_version,input_schema_version,output_schema_version)):raise RegistryError("invalid schema version")
 if input_schema_version!=prompt.input_schema_version or output_schema_version!=prompt.output_schema_version:raise RegistryError("prompt and agent schema incompatibility")
 if len(set(allowed_tools))!=len(allowed_tools) or tuple(sorted(allowed_tools))!=allowed_tools:raise RegistryError("tool allowlist must be unique and sorted")
 if not (1<=max_steps<=80 and 0<=max_tool_calls<=30 and 1<=max_tokens<=32768):raise RegistryError("agent budget out of range")
 payload={"agent_name":agent_name,"version":version,"prompt_sha256":prompt.content_sha256,"state_schema_version":state_schema_version,"input_schema_version":input_schema_version,"output_schema_version":output_schema_version,"allowed_tools":allowed_tools,"max_steps":max_steps,"max_tool_calls":max_tool_calls,"max_tokens":max_tokens}
 return AgentConfiguration(artifact_id,agent_name,version,status,prompt.artifact_id,prompt.content_sha256,state_schema_version,input_schema_version,output_schema_version,allowed_tools,max_steps,max_tool_calls,max_tokens,author_id,canonical_sha256(payload))
def approve(artifact:PromptArtifact|AgentConfiguration,approval:Approval)->None:
 if approval.artifact_id!=artifact.artifact_id or approval.decision!="approved":raise RegistryError("artifact not approved")
 if approval.approver_id==artifact.author_id:raise RegistryError("author cannot approve own artifact")
 if "ai_configuration_approver" not in approval.approver_roles:raise RegistryError("approver role required")
def evaluation_passes(value:EvaluationEvidence)->bool:
 return value.groundedness>=.90 and value.task_success>=.85 and value.safety>=.99 and value.regression_rate<=.02 and bool(SEMVER.fullmatch(value.suite_version)) and bool(SHA256.fullmatch(value.report_sha256))
def create_release(*,release_id:str,tenant_id:str,prompt:PromptArtifact,agent:AgentConfiguration,prompt_approval:Approval,agent_approval:Approval,evaluation:EvaluationEvidence)->ReleaseBundle:
 if not release_id or not tenant_id:raise RegistryError("release scope required")
 approve(prompt,prompt_approval);approve(agent,agent_approval)
 if agent.prompt_artifact_id!=prompt.artifact_id or agent.prompt_sha256!=prompt.content_sha256:raise RegistryError("agent prompt reference mismatch")
 if not evaluation_passes(evaluation):raise RegistryError("evaluation gate failed")
 fingerprint=canonical_sha256({"tenant_id":tenant_id,"prompt":prompt.content_sha256,"agent":agent.content_sha256,"evaluation_report":evaluation.report_sha256})
 return ReleaseBundle(release_id,tenant_id,prompt,agent,evaluation,fingerprint)
def deployment_event(bundle:ReleaseBundle,*,mode:Literal["canary","active","rolled_back"],percentage:int,actor_id:str,previous_fingerprint:str|None=None)->dict[str,Any]:
 if not actor_id or mode=="canary" and not 1<=percentage<=25 or mode!="canary" and percentage not in {0,100}:raise RegistryError("invalid deployment control")
 if mode=="rolled_back" and (not previous_fingerprint or not SHA256.fullmatch(previous_fingerprint)):raise RegistryError("rollback target fingerprint required")
 payload={"release_id":bundle.release_id,"tenant_id":bundle.tenant_id,"configuration_fingerprint":bundle.configuration_fingerprint,"mode":mode,"percentage":percentage,"actor_id":actor_id,"previous_fingerprint":previous_fingerprint}
 return {**payload,"event_sha256":canonical_sha256(payload)}
