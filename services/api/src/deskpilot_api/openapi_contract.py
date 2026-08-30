from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

SCHEMA_DIGEST_EXTENSION = "x-deskpilot-schema-sha256"

def canonical_json(schema: dict[str, Any]) -> str:
    return json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def install_governed_openapi(app: FastAPI) -> None:
    """Install deterministic OpenAPI generation with a verifiable schema digest."""
    def governed_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        schema["servers"] = [{"url": "/api/v1"}]
        schema["info"]["x-api-major-version"] = 1
        unsigned = canonical_json(schema)
        schema[SCHEMA_DIGEST_EXTENSION] = hashlib.sha256(unsigned.encode()).hexdigest()
        app.openapi_schema = schema
        return schema
    app.openapi = governed_openapi
