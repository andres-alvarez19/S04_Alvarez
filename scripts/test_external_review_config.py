#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from google.genai import types

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    schema = json.loads((ROOT / "schemas" / "trace_review.json").read_text(encoding="utf-8"))
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema,
    )
    assert config.response_json_schema is not None
    assert config.response_schema is None
    source = (ROOT / "scripts" / "run_external_review.py").read_text(encoding="utf-8")
    assert '"response_json_schema"' in source
    print("EXTERNAL_REVIEW_CONFIG_OK response_json_schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
