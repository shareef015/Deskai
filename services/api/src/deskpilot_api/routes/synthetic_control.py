from typing import Annotated
from fastapi import APIRouter,Depends,Request
from deskpilot_core.errors import DeskPilotError,ErrorCode
from deskpilot_api.auth.claims import AuthenticatedPrincipal
from deskpilot_api.auth.dependencies import require_principal
from deskpilot_api.synthetic.control import OperatorContext,SyntheticControlService
from deskpilot_api.synthetic.control_schemas import ActivateRequest,CompareRequest,ResetRequest,RollbackRequest
router=APIRouter(prefix="/api/v1/synthetic-control",tags=["synthetic-control"])
def service(request:Request)->SyntheticControlService:
 value=getattr(request.app.state,"synthetic_control_service",None)
 if not isinstance(value,SyntheticControlService):raise DeskPilotError(ErrorCode.DEPENDENCY_UNAVAILABLE)
 return value
def operator(request:Request,principal:AuthenticatedPrincipal)->OperatorContext:return OperatorContext(principal.subject,principal.roles,str(getattr(request.app.state,"synthetic_tenant_ref","disabled")))
@router.get("")
def state(request:Request,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],control:Annotated[SyntheticControlService,Depends(service)]):return control.state(operator(request,principal))
@router.post("/snapshots")
def snapshot(request:Request,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],control:Annotated[SyntheticControlService,Depends(service)]):return {"snapshot_id":control.capture_snapshot(operator(request,principal))}
@router.post("/activate")
def activate(command:ActivateRequest,request:Request,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],control:Annotated[SyntheticControlService,Depends(service)]):return control.activate(operator(request,principal),command.scenario_id,expected_version=command.expected_version)
@router.post("/rollback")
def rollback(command:RollbackRequest,request:Request,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],control:Annotated[SyntheticControlService,Depends(service)]):return control.rollback(operator(request,principal),expected_version=command.expected_version)
@router.post("/reset")
def reset(command:ResetRequest,request:Request,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],control:Annotated[SyntheticControlService,Depends(service)]):return control.reset(operator(request,principal),command.confirmation)
@router.post("/compare")
def compare(command:CompareRequest,request:Request,principal:Annotated[AuthenticatedPrincipal,Depends(require_principal)],control:Annotated[SyntheticControlService,Depends(service)]):return control.compare(operator(request,principal),command.left_snapshot_id,command.right_snapshot_id)
