#!/usr/bin/env python
"""
Export the FastAPI OpenAPI schema to docs/openapi.json.
Run from the backend/ directory:
    python scripts/export_openapi.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://bharatai:bharatai_pass@localhost:5432/bharatai_db",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "export-script-dummy-secret-key-32-chars")

from app.main import create_application  # noqa: E402

app = create_application()
schema = app.openapi()

out_path = Path(__file__).parent.parent.parent / "docs" / "openapi.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"✅ OpenAPI spec written to: {out_path}")
print(f"   Paths: {len(schema.get('paths', {}))}")
print(f"   Schemas: {len(schema.get('components', {}).get('schemas', {}))}")
