from __future__ import annotations
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT_SPEC = importlib.util.spec_from_file_location("openapi_compatibility", ROOT / "scripts/openapi_compatibility.py")
assert COMPAT_SPEC and COMPAT_SPEC.loader
COMPAT = importlib.util.module_from_spec(COMPAT_SPEC)
COMPAT_SPEC.loader.exec_module(COMPAT)

def validate() -> list[str]:
    policy = json.loads((ROOT / "contracts/api-versioning-policy.json").read_text())
    schema = json.loads((ROOT / policy["canonical_artifact"]).read_text())
    errors: list[str] = []
    if schema.get("openapi") != policy["openapi_version"]: errors.append("OpenAPI version mismatch")
    if schema.get("info", {}).get("version") != policy["contract_version"]: errors.append("contract version mismatch")
    if schema.get("servers") != [{"url": policy["public_api_prefix"]}]: errors.append("public server prefix mismatch")
    methods = {"get", "post", "put", "patch", "delete"}
    ids = [op.get("operationId") for item in schema.get("paths", {}).values() for method, op in item.items() if method in methods]
    if None in ids or len(ids) != len(set(ids)): errors.append("operation IDs must be present and unique")
    if not policy["generation"]["deterministic"]: errors.append("deterministic generation required")
    if COMPAT.breaking_changes(schema, schema): errors.append("canonical schema is not self-compatible")
    if "install_governed_openapi(app)" not in (ROOT / "services/api/src/deskpilot_api/app.py").read_text(): errors.append("governed generator is not installed")
    return errors

if __name__ == "__main__":
    failures = validate()
    if failures: raise SystemExit("\n".join(failures))
    print("API versioning and OpenAPI contracts: valid")
