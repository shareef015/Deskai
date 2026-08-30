from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/error-handling-policy.json").read_text())
    expected = {
        "validation_failed": 422, "authentication_required": 401, "access_denied": 403,
        "resource_not_found": 404, "conflict": 409, "rate_limited": 429,
        "dependency_unavailable": 503, "deadline_exceeded": 504, "internal_error": 500,
    }
    if policy.get("error_codes") != expected:
        errors.append("error taxonomy or status mapping changed")
    controls = policy.get("response_controls", {})
    for key in ("validation_field_echo", "stack_trace_exposure", "exception_message_exposure", "secret_or_path_exposure"):
        if controls.get(key) is not False:
            errors.append(f"unsafe response control: {key}")
    required_files = [
        ROOT / "packages/python/deskpilot-core/src/deskpilot_core/errors.py",
        ROOT / "services/api/src/deskpilot_api/errors.py",
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"missing error implementation: {path.relative_to(ROOT)}")
    app_text = (ROOT / "services/api/src/deskpilot_api/app.py").read_text()
    if "register_error_handlers(app)" not in app_text:
        errors.append("global API handlers are not registered")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("global exception handling validation passed")
