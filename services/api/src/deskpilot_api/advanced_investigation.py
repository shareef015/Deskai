from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
class InvestigationDenied(ValueError):pass
@dataclass(frozen=True)
class InvestigationContext:tenant_id:str;incident_id:str;actor_id:str;roles:frozenset[str];diagnostic_consent:bool;mode:Literal["live","synthetic"]
@dataclass(frozen=True)
class EvidenceNode:node_id:str;kind:Literal["incident","entity","document","observation","agent_step"];label:str;evidence_ids:tuple[str,...]
@dataclass(frozen=True)
class EvidenceEdge:source_id:str;target_id:str;relation:str;evidence_ids:tuple[str,...]
@dataclass(frozen=True)
class InvestigationView:incident_id:str;nodes:tuple[EvidenceNode,...];edges:tuple[EvidenceEdge,...];retrieval_ids:tuple[str,...];trace_ids:tuple[str,...];specialist_summaries:tuple[str,...];provenance_sha256:str
ALLOWED_ROLES=frozenset({"service_desk_engineer","advanced_investigator","operations_viewer"})
def build_view(context:InvestigationContext,nodes:tuple[EvidenceNode,...],edges:tuple[EvidenceEdge,...],retrieval_ids:tuple[str,...],trace_ids:tuple[str,...],specialist_summaries:tuple[str,...])->InvestigationView:
 if not context.tenant_id or not context.incident_id or not context.actor_id or not context.roles.intersection(ALLOWED_ROLES):raise InvestigationDenied("authorized tenant-scoped investigator required")
 if not context.diagnostic_consent:raise InvestigationDenied("diagnostic consent required")
 if len(nodes)>80 or len(edges)>160 or len(retrieval_ids)>50 or len(trace_ids)>100:raise InvestigationDenied("investigation view budget exceeded")
 node_ids={node.node_id for node in nodes}
 if len(node_ids)!=len(nodes) or any(edge.source_id not in node_ids or edge.target_id not in node_ids for edge in edges):raise InvestigationDenied("invalid evidence graph")
 if any(not node.evidence_ids for node in nodes) or any(not edge.evidence_ids for edge in edges):raise InvestigationDenied("ungrounded graph item")
 ordered_nodes=tuple(sorted(nodes,key=lambda item:(item.kind,item.node_id)));ordered_edges=tuple(sorted(edges,key=lambda item:(item.source_id,item.target_id,item.relation)));payload={"tenant":context.tenant_id,"incident":context.incident_id,"mode":context.mode,"nodes":[node.__dict__ for node in ordered_nodes],"edges":[edge.__dict__ for edge in ordered_edges],"retrieval":sorted(set(retrieval_ids)),"traces":sorted(set(trace_ids)),"specialists":sorted(set(specialist_summaries))};digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest();return InvestigationView(context.incident_id,ordered_nodes,ordered_edges,tuple(sorted(set(retrieval_ids))),tuple(sorted(set(trace_ids))),tuple(sorted(set(specialist_summaries))),digest)
