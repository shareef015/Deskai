from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.auth_personas")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/auth-persona-policy.json").read_text());config=json.loads((ROOT/"config/agents/auth-personas.json").read_text());ui=(ROOT/"apps/web/src/app/login/page.tsx").read_text();module()
 for key in ("oidc_issuer_audience_validation","tenant_bound_sessions","role_aware_authorization","expiry_and_revocation_checks","secure_logout","synthetic_personas_non_production_only","live_impersonation_denied","mode_isolation","hashed_audit_provenance"):
  if policy["requirements"].get(key) is not True:errors.append(f"authentication control disabled: {key}")
 if config["persona_switching"].get("live") is not False or config.get("demo_credentials_embedded") is not False:errors.append("unsafe persona or credential configuration")
 for marker in ("Sign in with your organization","Synthetic demonstration","Demo data only","Session expires","Secure logout","Role-aware navigation"):
  if marker not in ui:errors.append(f"login UI marker missing: {marker}")
 if 'type="password"' in ui:errors.append("embedded demo credential field found")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Authentication and persona validation passed")
