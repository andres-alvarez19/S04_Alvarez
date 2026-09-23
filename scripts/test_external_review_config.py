#!/usr/bin/env python3
import json
from pathlib import Path

from google.genai import types

ROOT = Path(__file__).resolve().parents[1]

schema = json.loads((ROOT / "schemas" / "external_review.json").read_text(encoding="utf-8"))

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_json_schema=schema,
)

assert config.response_json_schema is not None
assert config.response_schema is None

source = (ROOT / "scripts" / "run_external_review.py").read_text(encoding="utf-8")
assert '"response_json_schema": generation_schema' in source
assert '"response_schema": generation_schema' not in source

print("[OK] Gemini structured output usa response_json_schema y acepta el JSON Schema de auditoría.")
