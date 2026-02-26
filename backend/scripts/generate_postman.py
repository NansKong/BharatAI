#!/usr/bin/env python
"""
Generate a Postman Collection v2.1 from the exported OpenAPI spec.
Run from the backend/ directory:
    python scripts/generate_postman.py
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
OPENAPI_PATH = DOCS_DIR / "openapi.json"
OUTPUT_PATH = DOCS_DIR / "postman_collection.json"

BASE_URL = "{{base_url}}"


def _method_item(path: str, method: str, operation: dict) -> dict:
    """Convert a single OpenAPI operation to a Postman item."""
    name = operation.get("summary") or f"{method.upper()} {path}"
    tags = operation.get("tags", ["General"])

    # Build URL
    url_parts = path.lstrip("/").split("/")
    raw_url = f"{BASE_URL}/{path.lstrip('/')}"
    variables = [
        {
            "key": part[1:-1],
            "value": f":{part[1:-1]}",
            "description": f"Path parameter: {part[1:-1]}",
        }
        for part in url_parts
        if part.startswith("{") and part.endswith("}")
    ]

    # Query params
    query = []
    for param in operation.get("parameters", []):
        if param.get("in") == "query":
            query.append(
                {
                    "key": param["name"],
                    "value": "",
                    "description": param.get("description", ""),
                    "disabled": not param.get("required", False),
                }
            )

    # Request body
    body = {"mode": "none"}
    if "requestBody" in operation:
        content = operation["requestBody"].get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            example = content["application/json"].get("example", {})
            body = {
                "mode": "raw",
                "raw": json.dumps(example or _schema_example(schema), indent=2),
                "options": {"raw": {"language": "json"}},
            }

    return {
        "name": name,
        "_postman_id": str(uuid.uuid4()),
        "request": {
            "method": method.upper(),
            "header": [
                {"key": "Content-Type", "value": "application/json"},
                {"key": "Authorization", "value": "Bearer {{access_token}}"},
            ],
            "url": {
                "raw": raw_url,
                "host": ["{{base_url}}"],
                "path": url_parts,
                "variable": variables,
                "query": query,
            },
            "body": body,
            "description": operation.get("description", ""),
        },
        "response": [],
    }


def _schema_example(schema: dict) -> dict:
    """Generate a minimal example from a JSON Schema."""
    if not schema:
        return {}
    props = schema.get("properties", {})
    example = {}
    for key, val in props.items():
        t = val.get("type", "string")
        if t == "string":
            example[key] = val.get("example", f"<{key}>")
        elif t == "integer":
            example[key] = val.get("example", 0)
        elif t == "boolean":
            example[key] = False
        elif t == "array":
            example[key] = []
        elif t == "object":
            example[key] = {}
    return example


def build_collection(spec: dict) -> dict:
    info = spec.get("info", {})
    folders: dict[str, list] = {}

    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            tags = operation.get("tags", ["General"])
            folder = tags[0] if tags else "General"
            folders.setdefault(folder, [])
            folders[folder].append(_method_item(path, method, operation))

    items = [
        {"name": folder, "item": endpoints, "_postman_id": str(uuid.uuid4())}
        for folder, endpoints in sorted(folders.items())
    ]

    return {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": info.get("title", "BharatAI API"),
            "description": info.get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": info.get("version", "0.1.0"),
        },
        "item": items,
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000", "type": "string"},
            {"key": "access_token", "value": "", "type": "string"},
        ],
    }


if not OPENAPI_PATH.exists():
    print(f"❌  {OPENAPI_PATH} not found. Run export_openapi.py first.")
    raise SystemExit(1)

spec = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
collection = build_collection(spec)
OUTPUT_PATH.write_text(
    json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8"
)

endpoint_count = sum(len(f["item"]) for f in collection["item"])
print(f"✅ Postman collection written to: {OUTPUT_PATH}")
print(f"   Folders: {len(collection['item'])}  |  Endpoints: {endpoint_count}")
