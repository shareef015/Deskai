from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
class NavigationDenied(ValueError):pass
Mode=Literal["live","synthetic"]
@dataclass(frozen=True)
class NavigationItem:key:str;label:str;href:str;group:str;roles:frozenset[str];modes:frozenset[Mode]
@dataclass(frozen=True)
class ShellContext:tenant_id:str;tenant_label:str;roles:frozenset[str];mode:Mode;authenticated:bool
@dataclass(frozen=True)
class ShellManifest:tenant_label:str;mode:Mode;groups:tuple[tuple[str,tuple[NavigationItem,...]],...];default_href:str;manifest_sha256:str
ITEMS=(NavigationItem("incidents","Incidents","/incident-workspace","Support",frozenset({"employee","service_desk_engineer"}),frozenset({"live","synthetic"})),NavigationItem("conversation","Conversation","/conversation-workspace","Support",frozenset({"employee","service_desk_engineer"}),frozenset({"live","synthetic"})),NavigationItem("evidence","Evidence explorer","/evidence-explorer","Investigation",frozenset({"service_desk_engineer"}),frozenset({"live","synthetic"})),NavigationItem("remediation","Remediation review","/remediation-review","Investigation",frozenset({"service_desk_engineer","remediation_approver"}),frozenset({"live","synthetic"})),NavigationItem("verification","Verification","/execution-verification","Resolution",frozenset({"service_desk_engineer","remediation_approver"}),frozenset({"live","synthetic"})),NavigationItem("handoff","Human handoff","/human-handoff","Resolution",frozenset({"service_desk_engineer"}),frozenset({"live","synthetic"})),NavigationItem("operations","Operations","/operations","Operations",frozenset({"operations_viewer"}),frozenset({"live","synthetic"})),NavigationItem("observability","Agent observability","/agent-observability","Operations",frozenset({"operations_viewer"}),frozenset({"live","synthetic"})),NavigationItem("demo","Guided demo","/guided-demo","Demonstration",frozenset({"demo_operator"}),frozenset({"synthetic"})))
def build_manifest(context:ShellContext)->ShellManifest:
 if not context.authenticated or not context.tenant_id or not context.tenant_label or not context.roles:raise NavigationDenied("authenticated tenant and role context required")
 visible=tuple(item for item in ITEMS if context.roles.intersection(item.roles) and context.mode in item.modes)
 if not visible:raise NavigationDenied("no authorized destinations")
 order=("Support","Investigation","Resolution","Operations","Demonstration");groups=tuple((group,tuple(item for item in visible if item.group==group)) for group in order if any(item.group==group for item in visible));payload={"tenant":context.tenant_id,"mode":context.mode,"roles":sorted(context.roles),"items":[item.key for item in visible]};fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest();return ShellManifest(context.tenant_label,context.mode,groups,visible[0].href,fingerprint)
def authorize_path(context:ShellContext,path:str)->NavigationItem:
 for _,items in build_manifest(context).groups:
  for item in items:
   if item.href==path:return item
 raise NavigationDenied("destination denied")
