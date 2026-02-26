#!/usr/bin/env sh
# Generate TypeScript API types from the exported OpenAPI spec.
# Requires: Node.js + npx
#
# Usage (from project root):
#   sh docs/generate_types.sh

set -e

SPEC="docs/openapi.json"
OUT="frontend/src/types/api.d.ts"

if [ ! -f "$SPEC" ]; then
  echo "❌  $SPEC not found. Run: python backend/scripts/export_openapi.py"
  exit 1
fi

echo "Generating TypeScript types from $SPEC → $OUT"
npx openapi-typescript "$SPEC" -o "$OUT"
echo "✅  Types written to $OUT"
