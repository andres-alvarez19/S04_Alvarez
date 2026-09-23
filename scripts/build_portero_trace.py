#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.paths import PathResolver, Violation
from harness.taint import TaintFilter
from harness.types import Fragment


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    policy = load_json(ROOT / "activity" / "policy.json")
    requests = load_json(ROOT / "activity" / "requests.json")
    balance = int(policy["initial_tokens"])
    rows = []

    with tempfile.TemporaryDirectory(prefix="s04-portero-") as tmp:
        tmp_path = Path(tmp)
        project = tmp_path / "project"
        factory = tmp_path / "factory"
        for rel in ("INPUT/raw", "WORK", "OUTPUT/v0.1", "TRACE", "EVIDENCE", "SPEC"):
            (project / rel).mkdir(parents=True, exist_ok=True)
        (factory / "manifests").mkdir(parents=True, exist_ok=True)
        (project / "INPUT/raw/fuente.pdf").write_text("sealed", encoding="utf-8")
        (project / "INPUT/raw/ticket_4471.txt").write_text("sealed", encoding="utf-8")
        (project / "OUTPUT/v0.1/informe.md").write_text("existing", encoding="utf-8")
        resolver = PathResolver(project, factory)

        for seq, req in enumerate(requests, 1):
            before = balance
            verdict = "denegada"
            reason = "default_deny"
            invariant = None
            permitted = False

            if req["kind"] == "path":
                result = resolver.resolve(req["target"], write=req["operation"] == "write")
                if isinstance(result, Violation):
                    reason = result.code
                    invariant = result.invariant
                else:
                    permitted = True
                    reason = "policy_allow"
            elif req["kind"] == "tool":
                if req["capability"] in policy["tool_allowlist"]:
                    permitted = True
                    reason = "tool_allowlist"
                else:
                    reason = "capability_not_allowlisted"
            elif req["kind"] == "model":
                permitted = True
                reason = "budgeted_model_call"
            elif req["kind"] == "external_effect":
                reason = "human_approval_required"
            elif req["kind"] == "meta":
                reason = "default_deny_meta_change"

            charged = 0
            partial = None
            if permitted:
                cost = int(req["cost"])
                if cost > balance:
                    verdict = "agotado"
                    reason = "insufficient_budget"
                    partial = {
                        "incomplete": True,
                        "resumable": True,
                        "resume_from": req["id"],
                    }
                else:
                    charged = cost
                    balance -= charged
                    verdict = "permitida"

            poison = None
            if req.get("poison"):
                p = req["poison"]
                taint = TaintFilter.review(Fragment(req["id"], p["locator"], p["text"]))
                poison = {
                    "id": p["id"],
                    "taint": taint.taint,
                    "action": taint.action,
                    "locator": taint.locator,
                    "run_continues": True,
                }

            rows.append(
                {
                    "seq": seq,
                    "request_id": req["id"],
                    "request": req["description"],
                    "access_type": req["kind"],
                    "verdict": verdict,
                    "reason": reason,
                    "invariant": invariant,
                    "tokens_charged": charged,
                    "balance_before": before,
                    "balance_after": balance,
                    "poison": poison,
                    "partial": partial,
                }
            )

    out = ROOT / "TRACE" / "portero.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"TRACE_GENERATED rows={len(rows)} balance_final={balance} path={out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
