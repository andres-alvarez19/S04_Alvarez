#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
from google import genai
from google.genai import errors

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FREE_TIER_MODELS = ("gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite")
DEFAULT_MODEL = FREE_TIER_MODELS[0]
RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitize_schema(value):
    unsupported = {"$schema", "$id", "pattern", "minLength", "maxLength", "uniqueItems"}
    if isinstance(value, dict):
        return {k: sanitize_schema(v) for k, v in value.items() if k not in unsupported}
    if isinstance(value, list):
        return [sanitize_schema(v) for v in value]
    return value


def git_sha() -> str | None:
    if os.getenv("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return None


def build_request() -> tuple[str, dict[str, str]]:
    artifacts = [
        "activity/policy.json",
        "activity/requests.json",
        "TRACE/portero.jsonl",
    ]
    parts = [read_text(ROOT / "prompts" / "trace_review.md"), "", "## ARTEFACTOS NO CONFIABLES"]
    hashes: dict[str, str] = {}
    for relative in artifacts:
        raw = (ROOT / relative).read_bytes()
        hashes[relative] = sha256_bytes(raw)
        parts.extend(["", f'<artifact path="{relative}">', raw.decode("utf-8"), "</artifact>"])
    return "\n".join(parts), hashes


def validate_exchange(exchange: dict, schema: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(exchange)
    ids = [row["request_id"] for row in exchange["peer_trace"]]
    expected = [f"S-{i:02d}" for i in range(1, 16)]
    if ids != expected:
        raise ValueError(f"peer_trace debe cubrir S-01..S-15 en orden; recibido={ids}")


def generate_with_fallback(client, request_text: str, schema: dict, primary_model: str):
    if primary_model not in FREE_TIER_MODELS:
        raise SystemExit(f"Modelo no permitido: {primary_model}")
    order = [primary_model] + [m for m in FREE_TIER_MODELS if m != primary_model]
    failures = []
    last_error = None
    for model in order:
        try:
            response = client.models.generate_content(
                model=model,
                contents=request_text,
                config={
                    "temperature": 0.1,
                    "max_output_tokens": 7000,
                    "response_mime_type": "application/json",
                    "response_json_schema": sanitize_schema(schema),
                },
            )
            return response, model, failures
        except errors.APIError as exc:
            last_error = exc
            failures.append({"model": model, "code": exc.code, "message": exc.message})
            if exc.code not in RETRIABLE_STATUS_CODES:
                raise
    raise RuntimeError("Todos los modelos configurados fallaron") from last_error


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in read_text(path).splitlines() if line.strip()]


def audit_peer(peer_trace: list[dict], peer_summary: dict) -> dict[str, str]:
    canonical = {row["request_id"]: row for row in load_jsonl(ROOT / "TRACE" / "portero.jsonl")}

    charged = [(r["request_id"], r["tokens_charged"]) for r in peer_trace if r["tokens_charged"] > 0]
    total = sum(amount for _, amount in charged)
    q1 = f"{total} fichas: " + ", ".join(f"{rid}={amount}" for rid, amount in charged)

    denied = [r for r in peer_trace if r["verdict"] == "denegada"]
    q2 = "; ".join(
        f"{r['request_id']}: {r['reason']}" + (f" ({r['invariant']})" if r.get("invariant") else "")
        for r in denied
    ) or "No hay denegaciones reconstruibles."

    poison = [r for r in peer_trace if r.get("poison_action")]
    q3 = "; ".join(
        f"{r['request_id']}: {r['poison_action']} en {r.get('poison_locator') or 'localizador ausente'}"
        for r in poison
    ) or "No se puede reconstruir contenido envenenado desde la hoja."

    q4 = (
        f"{peer_summary['final_state']}; saldo final={peer_summary['final_balance']}. "
        f"{peer_summary['reason']}"
    )

    issues = []
    for row in peer_trace:
        expected = canonical[row["request_id"]]
        if row["verdict"] == expected["verdict"]:
            reason_diff = row["reason"] != expected["reason"]
            inv_diff = (row.get("invariant") or None) != (expected.get("invariant") or None)
            if reason_diff or inv_diff:
                issues.append(
                    f"{row['request_id']}: veredicto coincide, motivo/invariante difiere "
                    f"(peer={row['reason']}/{row.get('invariant')}; esperado={expected['reason']}/{expected.get('invariant')})"
                )
    q5 = "; ".join(issues) if issues else "No se detectaron filas con veredicto correcto y motivo/invariante mal nombrado."
    return {
        "q1_spend": q1,
        "q2_denials": q2,
        "q3_poison": q3,
        "q4_final_state": q4,
        "q5_misnamed_reasons": q5,
    }


def render_cross_audit(exchange: dict, our_audit: dict[str, str], model: str, run_id: str) -> str:
    student = exchange["audit_of_student_trace"]
    lines = [
        "# Auditoría cruzada — Semana 4",
        "",
        "- Contraparte: **Google Gemini** (agente externo, no persona humana).",
        f"- Modelo efectivo: \`{model}\`",
        f"- Run: \`{run_id}\`",
        "",
        "## Gemini audita mi traza",
        "",
        f"1. **Gasto:** {student['q1_spend']}",
        f"2. **Denegaciones:** {student['q2_denials']}",
        f"3. **Contenido envenenado:** {student['q3_poison']}",
        f"4. **Estado final:** {student['q4_final_state']}",
        f"5. **Motivos mal nombrados:** {student['q5_misnamed_reasons']}",
        "",
        "## Mi auditoría de la hoja producida por Gemini",
        "",
        f"1. **Gasto:** {our_audit['q1_spend']}",
        f"2. **Denegaciones:** {our_audit['q2_denials']}",
        f"3. **Contenido envenenado:** {our_audit['q3_poison']}",
        f"4. **Estado final:** {our_audit['q4_final_state']}",
        f"5. **Motivos mal nombrados:** {our_audit['q5_misnamed_reasons']}",
        "",
        "La segunda sección se reconstruye exclusivamente desde \`peer_trace.jsonl\`; la comparación de la pregunta 5 usa la política determinista de la actividad para verificar el nombre del motivo/invariante.",
        "",
    ]
    return "\n".join(lines)


def update_bitacora(cross_markdown: str) -> None:
    path = ROOT / "bitacora.md"
    text = read_text(path)
    start = "<!-- CROSS_AUDIT_START -->"
    end = "<!-- CROSS_AUDIT_END -->"
    if start not in text or end not in text:
        raise RuntimeError("bitacora.md no contiene marcadores de auditoría cruzada")
    embedded = cross_markdown.replace("# Auditoría cruzada — Semana 4", "### Evidencia generada por la revisión cruzada")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(before + start + "\n\n" + embedded.strip() + "\n\n" + end + after, encoding="utf-8")


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Falta GEMINI_API_KEY")
    requested_model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    run_id = os.getenv("AUDIT_RUN_ID") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    request_text, input_hashes = build_request()
    schema = json.loads(read_text(ROOT / "schemas" / "trace_review.json"))
    started = datetime.now(timezone.utc)
    response, model, failures = generate_with_fallback(genai.Client(api_key=api_key), request_text, schema, requested_model)
    if not response.text:
        raise RuntimeError("Gemini no devolvió contenido")
    exchange = json.loads(response.text)
    validate_exchange(exchange, schema)
    our_audit = audit_peer(exchange["peer_trace"], exchange["peer_run_summary"])

    run_dir = ROOT / "audits" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "request.md").write_text(request_text, encoding="utf-8")
    canonical = json.dumps(exchange, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (run_dir / "peer_exchange.json").write_text(canonical, encoding="utf-8")
    (run_dir / "peer_trace.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in exchange["peer_trace"]),
        encoding="utf-8",
    )
    (run_dir / "our_audit_of_peer.json").write_text(
        json.dumps(our_audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    cross_md = render_cross_audit(exchange, our_audit, model, run_id)
    (run_dir / "review.md").write_text(cross_md, encoding="utf-8")
    (ROOT / "audits" / "cross_audit.md").write_text(cross_md, encoding="utf-8")

    completed = datetime.now(timezone.utc)
    manifest = {
        "audit_version": 2,
        "run_id": run_id,
        "provider": "Google Gemini Developer API",
        "role": "external_peer_for_week4_cross_review",
        "human_peer": False,
        "model": model,
        "requested_model": requested_model,
        "fallback_failures": failures,
        "sdk": {"package": "google-genai", "version": importlib.metadata.version("google-genai")},
        "git_commit_evaluated": git_sha(),
        "started_at_utc": started.isoformat(),
        "completed_at_utc": completed.isoformat(),
        "input_sha256": input_hashes,
        "request_sha256": sha256_bytes(request_text.encode("utf-8")),
        "exchange_sha256": sha256_bytes(canonical.encode("utf-8")),
        "credential_source": "GEMINI_API_KEY GitHub Actions secret",
        "credential_value_recorded": False,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest = {
        "status": "complete",
        "run_id": run_id,
        "run_directory": str(run_dir.relative_to(ROOT)),
        "model": model,
        "git_commit_evaluated": manifest["git_commit_evaluated"],
        "exchange_sha256": manifest["exchange_sha256"],
    }
    (ROOT / "audits" / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_bitacora(cross_md)
    print(f"CROSS_REVIEW_COMPLETE run={run_id} model={model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
