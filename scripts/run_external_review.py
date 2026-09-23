#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
from google import genai
from google.genai import errors

ROOT = Path(__file__).resolve().parents[1]
FREE_TIER_MODELS = (
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
)
DEFAULT_MODEL = FREE_TIER_MODELS[0]
RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}

ARTIFACTS = [
    "work_order.json",
    "bitacora.md",
    "auction.json",
    "blocking_questions.md",
    "evals/caso_abstencion.jsonl",
    "evals/caso_adversario.jsonl",
    "evals/caso_agotamiento.jsonl",
    "schemas/work_order.json",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sanitize_schema_for_gemini(value):
    """Reduce el schema al subconjunto aceptado por structured output de Gemini."""
    unsupported = {"$schema", "$id", "pattern", "minLength", "maxLength", "uniqueItems"}
    if isinstance(value, dict):
        return {
            key: sanitize_schema_for_gemini(item)
            for key, item in value.items()
            if key not in unsupported
        }
    if isinstance(value, list):
        return [sanitize_schema_for_gemini(item) for item in value]
    return value


def git_sha() -> str | None:
    if os.getenv("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def build_request() -> tuple[str, dict[str, str]]:
    base_prompt = read_text(ROOT / "prompts" / "external_review.md")
    hashes: dict[str, str] = {}
    parts = [base_prompt, "", "## ARTEFACTOS NO CONFIABLES"]

    for relative in ARTIFACTS:
        path = ROOT / relative
        raw = read_bytes(path)
        hashes[relative] = sha256_bytes(raw)
        content = raw.decode("utf-8")
        parts.extend(
            [
                "",
                f'<artifact path="{relative}">',
                content,
                "</artifact>",
            ]
        )

    return "\n".join(parts), hashes


def validate_review(review: dict, schema: dict) -> None:
    jsonschema.Draft202012Validator(schema).validate(review)

    attacks = review["attacks"]
    attacked_ids = {item["criterion_id"] for item in attacks}
    if len(attacked_ids) < 3:
        raise ValueError("La revisión externa debe atacar al menos tres criterios distintos.")

    if not any(item["is_original"] for item in attacks):
        raise ValueError("La revisión externa debe contener al menos un ataque original.")

    expected = {f"AC-0{i}" for i in range(1, 6)}
    assessed = {item["criterion_id"] for item in review["criteria_assessment"]}
    if assessed != expected:
        raise ValueError(
            "criteria_assessment debe cubrir exactamente AC-01, AC-02, AC-03, AC-04 y AC-05."
        )


def render_markdown(review: dict, model: str, run_id: str) -> str:
    lines = [
        "# Revisión adversarial externa",
        "",
        "- **Proveedor:** Google Gemini",
        f"- **Modelo:** `{model}`",
        f"- **Run ID:** `{run_id}`",
        "- **Rol:** agente externo; no revisión humana",
        "",
        "## Ataques",
        "",
    ]

    for idx, attack in enumerate(review["attacks"], 1):
        lines.extend(
            [
                f"### {idx}. {attack['criterion_id']} — {attack['attack_name']}",
                "",
                f"- **Familia:** {attack['attack_family']}",
                f"- **Original:** {'sí' if attack['is_original'] else 'no'}",
                f"- **Criterio objetivo:** {attack['criterion_literal']}",
                "",
                "**Salida concreta engañosa**",
                "",
                "```text",
                attack["exploit_output"],
                "```",
                "",
                f"**Por qué el validador la aceptaría:** {attack['why_validator_accepts']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Evaluación por criterio",
            "",
            "| Criterio | Estado | Razón | Reescritura sugerida |",
            "|---|---|---|---|",
        ]
    )

    for item in review["criteria_assessment"]:
        rewrite = item["suggested_rewrite"] or "No requerida"
        reason = item["reason"].replace("|", "\\|").replace("\n", " ")
        rewrite = rewrite.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {item['criterion_id']} | {item['status']} | {reason} | {rewrite} |"
        )

    lines.extend(["", "## Notas generales", "", review["overall_notes"], ""])
    return "\n".join(lines)


def serializable_usage(response):
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return None
    if hasattr(usage, "model_dump"):
        return usage.model_dump(exclude_none=True)
    try:
        return dict(usage)
    except Exception:
        return str(usage)



def generate_with_free_tier_fallback(client, request_text, generation_schema, primary_model):
    if primary_model not in FREE_TIER_MODELS:
        raise SystemExit(
            f"Modelo rechazado: {primary_model}. Permitidos en esta automatización: "
            + ", ".join(FREE_TIER_MODELS)
        )

    model_order = [primary_model] + [
        model for model in FREE_TIER_MODELS if model != primary_model
    ]
    failures = []
    last_error = None

    for model in model_order:
        try:
            response = client.models.generate_content(
                model=model,
                contents=request_text,
                config={
                    "temperature": 0.2,
                    "max_output_tokens": 5000,
                    "response_mime_type": "application/json",
                    "response_json_schema": generation_schema,
                },
            )
            return response, model, failures
        except errors.APIError as exc:
            last_error = exc
            failure = {
                "model": model,
                "code": exc.code,
                "message": exc.message,
            }
            failures.append(failure)
            print(
                f"[WARN] Gemini {model} falló con HTTP {exc.code}: {exc.message}",
                flush=True,
            )
            if exc.code not in RETRIABLE_STATUS_CODES:
                raise
            print(
                "[WARN] Error transitorio tras los reintentos internos del SDK; "
                "se probará el siguiente modelo Free tier.",
                flush=True,
            )

    raise RuntimeError(
        "Todos los modelos Free tier configurados fallaron con errores transitorios."
    ) from last_error

def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Falta GEMINI_API_KEY. Configúrala como variable de entorno o GitHub Actions secret."
        )

    requested_model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    run_id = os.getenv("AUDIT_RUN_ID")
    if not run_id:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    started = datetime.now(timezone.utc)
    request_text, input_hashes = build_request()
    prompt_hash = sha256_bytes(request_text.encode("utf-8"))

    response_schema = json.loads(read_text(ROOT / "schemas" / "external_review.json"))
    generation_schema = sanitize_schema_for_gemini(response_schema)

    client = genai.Client(api_key=api_key)
    response, model, fallback_failures = generate_with_free_tier_fallback(
        client,
        request_text,
        generation_schema,
        requested_model,
    )

    if not response.text:
        raise RuntimeError("Gemini no devolvió contenido textual.")

    review = json.loads(response.text)
    validate_review(review, response_schema)

    canonical_review = json.dumps(
        review, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    review_hash = sha256_bytes(canonical_review.encode("utf-8"))

    run_dir = ROOT / "audits" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    (run_dir / "request.md").write_text(request_text, encoding="utf-8")
    (run_dir / "review.json").write_text(canonical_review, encoding="utf-8")
    (run_dir / "review.md").write_text(
        render_markdown(review, model, run_id), encoding="utf-8"
    )

    completed = datetime.now(timezone.utc)
    manifest = {
        "audit_version": 1,
        "run_id": run_id,
        "provider": "Google Gemini Developer API",
        "model": model,
        "requested_model": requested_model,
        "free_tier_fallback_failures": fallback_failures,
        "sdk": {
            "package": "google-genai",
            "version": importlib.metadata.version("google-genai"),
        },
        "credential_source": "GEMINI_API_KEY environment variable / GitHub Actions secret",
        "credential_value_recorded": False,
        "free_tier_expected": True,
        "free_tier_model_enforced": True,
        "free_tier_billing_enforced_by_code": False,
        "structured_output_mode": "response_json_schema",
        "git_commit_evaluated": git_sha(),
        "github": {
            "workflow": os.getenv("GITHUB_WORKFLOW"),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
            "repository": os.getenv("GITHUB_REPOSITORY"),
        },
        "started_at_utc": started.isoformat(),
        "completed_at_utc": completed.isoformat(),
        "input_sha256": input_hashes,
        "request_sha256": prompt_hash,
        "review_sha256": review_hash,
        "response_id": getattr(response, "response_id", None),
        "usage_metadata": serializable_usage(response),
        "output_files": {
            "request": str((run_dir / "request.md").relative_to(ROOT)),
            "review_json": str((run_dir / "review.json").relative_to(ROOT)),
            "review_markdown": str((run_dir / "review.md").relative_to(ROOT)),
        },
    }

    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    latest = {
        "run_id": run_id,
        "run_directory": str(run_dir.relative_to(ROOT)),
        "model": model,
        "git_commit_evaluated": manifest["git_commit_evaluated"],
        "review_sha256": review_hash,
    }
    (ROOT / "audits" / "latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Revisión externa completada: {run_dir.relative_to(ROOT)}")
    print(f"Modelo: {model}")
    print(f"SHA-256 review.json: {review_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
