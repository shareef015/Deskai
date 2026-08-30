from typing import Annotated
from fastapi import APIRouter,Depends,Request
from deskpilot_core.errors import DeskPilotError,ErrorCode
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from deskpilot_api.auth.dependencies import require_principal
from deskpilot_api.synthetic.guided_demo import DemoOperator,GuidedDemoService
from deskpilot_api.synthetic.guided_demo_schemas import ResetDemoRequest,StartDemoRequest

router=APIRouter(prefix="/api/v1/guided-demo",tags=["guided-demo"])
def service(request:Request)->GuidedDemoService:
 value=getattr(request.app.state,"guided_demo_service",None)
 if not isinstance(value,GuidedDemoService):raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE)
 return value
def operator(principal:AuthenticatedPrincipal)->DemoOperator:return DemoOperator(principal.subject,principal.roles,str(principal.tenant_id),principal.subject.startswith("svc-ai") or "ai_service" in principal.roles)
@router.get("")
def catalog(principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],demo:Annotated[GuidedDemoService,Depends(service)]):return demo.catalog(operator(principal))
@router.get("/state")
def state(principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],demo:Annotated[GuidedDemoService,Depends(service)]):return demo.state(operator(principal))
@router.post("/start")
def start(command:StartDemoRequest,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],demo:Annotated[GuidedDemoService,Depends(service)]):return demo.start(operator(principal),command.pack_id)
@router.post("/advance")
def advance(principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],demo:Annotated[GuidedDemoService,Depends(service)]):return demo.advance(operator(principal))
@router.post("/reset")
def reset(command:ResetDemoRequest,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],demo:Annotated[GuidedDemoService,Depends(service)]):return demo.reset(operator(principal),command.confirmation)
