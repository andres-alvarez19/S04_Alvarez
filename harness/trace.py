from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_FORBIDDEN_KEYS = ("secret", "password", "chain_of_thought", "reasoning_content")


def _sanitize(value: Any):
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            low = str(key).lower()
            if any(token in low for token in _FORBIDDEN_KEYS):
                continue
            clean[key] = _sanitize(item)
        return clean
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    return value


class TraceWriter:
    """Traza JSONL: una línea por evento, también en fallo."""

    def __init__(self, path: Path, run_id: str):
        self.path = path
        self.run_id = run_id
        self.seq = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("w", encoding="utf-8")

    def record(self, event: str, **fields: Any) -> None:
        self.seq += 1
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "seq": self.seq,
            "event": event,
            **_sanitize(fields),
        }
        self._fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self._fh.flush()

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
