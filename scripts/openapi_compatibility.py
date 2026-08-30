from __future__ import annotations
from typing import Any

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

def breaking_changes(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    old_paths, new_paths = baseline.get("paths", {}), candidate.get("paths", {})
    for path, old_item in old_paths.items():
        if path not in new_paths:
            errors.append(f"removed path: {path}"); continue
        for method, old_operation in old_item.items():
            if method not in HTTP_METHODS: continue
            new_operation = new_paths[path].get(method)
            if new_operation is None:
                errors.append(f"removed operation: {method.upper()} {path}"); continue
            for status in sorted(set(old_operation.get("responses", {})) - set(new_operation.get("responses", {}))):
                errors.append(f"removed response {status}: {method.upper()} {path}")
    old_schemas = baseline.get("components", {}).get("schemas", {})
    new_schemas = candidate.get("components", {}).get("schemas", {})
    for name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(name)
        if new_schema is None:
            errors.append(f"removed schema: {name}"); continue
        added = set(new_schema.get("required", [])) - set(old_schema.get("required", []))
        if added: errors.append(f"new required fields in {name}: {','.join(sorted(added))}")
        for field, old_property in old_schema.get("properties", {}).items():
            new_property = new_schema.get("properties", {}).get(field)
            if new_property is None: errors.append(f"removed property: {name}.{field}")
            elif set(old_property.get("enum", [])) - set(new_property.get("enum", [])):
                errors.append(f"narrowed enum: {name}.{field}")
    return sorted(errors)
