#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ok(message: str) -> bool:
    print(f"[OK] {message}")
    return True


def fail(message: str) -> bool:
    print(f"[FAIL] {message}")
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_required_files() -> bool:
    required = [
        "harness/__init__.py",
        "harness/paths.py",
        "harness/run.py",
        "harness/budget.py",
        "harness/taint.py",
        "harness/trace.py",
        "evals/test_paths.py",
        "evals/test_arnes.py",
        "TRACE/portero.jsonl",
        "activity/policy.json",
        "activity/requests.json",
        "evidence/tests.txt",
        "evidence/ablation.txt",
        "bitacora.md",
        ".github/workflows/validate.yml",
        ".github/workflows/external-review.yml",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    return fail("Faltan: " + ", ".join(missing)) if missing else ok("Estructura obligatoria S04 presente")


def validate_trace() -> bool:
    trace = ROOT / "TRACE" / "portero.jsonl"
    before = sha256(trace)
    build = subprocess.run([sys.executable, "scripts/build_portero_trace.py"], cwd=ROOT, text=True, capture_output=True)
    if build.returncode != 0:
        return fail("No se pudo regenerar la traza: " + build.stderr.strip())
    after = sha256(trace)
    valid = True
    if before != after:
        valid &= fail("TRACE/portero.jsonl no coincide con el generador reproducible")
    else:
        valid &= ok("Traza digital reproducible")

    rows = load_jsonl(trace)
    if len(rows) != 15 or [r["request_id"] for r in rows] != [f"S-{i:02d}" for i in range(1, 16)]:
        valid &= fail("La traza debe contener exactamente S-01..S-15")
    else:
        valid &= ok("Traza contiene las 15 solicitudes")

    balance = 12
    for row in rows:
        if row["balance_before"] != balance:
            valid &= fail(f"Saldo previo inconsistente en {row['request_id']}")
            break
        balance -= row["tokens_charged"]
        if row["balance_after"] != balance:
            valid &= fail(f"Saldo posterior inconsistente en {row['request_id']}")
            break
    else:
        valid &= ok(f"Saldo encadenado consistente: 12 -> {balance}")

    poisons = {r["poison"]["id"] for r in rows if r.get("poison")}
    if poisons != {"V-01", "V-02", "V-03"}:
        valid &= fail(f"Cuarentenas incorrectas: {sorted(poisons)}")
    elif not all(r["poison"]["action"] == "cuarentena" and r["poison"]["run_continues"] for r in rows if r.get("poison")):
        valid &= fail("Alguna cuarentena no conserva continuidad")
    else:
        valid &= ok("Tres contenidos envenenados en cuarentena con continuidad")

    s10 = next(r for r in rows if r["request_id"] == "S-10")
    if s10["verdict"] != "agotado" or not s10["partial"] or not s10["partial"]["resumable"]:
        valid &= fail("S-10 debe ser AGOTADO con entrega parcial reanudable")
    else:
        valid &= ok("Agotamiento diferenciado de denegación")
    return bool(valid)


def validate_path_resolver_source() -> bool:
    text = (ROOT / "harness" / "paths.py").read_text(encoding="utf-8")
    valid = True
    if "relative_to(base)" not in text or ".resolve()" not in text:
        valid &= fail("PathResolver no demuestra comparación sobre rutas resueltas")
    else:
        valid &= ok("PathResolver compara rutas resueltas")
    if "raise Violation" in text:
        valid &= fail("Las violaciones no deben propagarse como excepción")
    else:
        valid &= ok("Violaciones de ruta vuelven como datos")
    return bool(valid)


def validate_tests() -> bool:
    run = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, text=True, capture_output=True)
    print(run.stdout.rstrip())
    if run.returncode != 0:
        print(run.stderr.rstrip())
        return fail("La batería S04 no está en verde")
    if "12 passed" not in run.stdout:
        return fail("Se esperaban 12 pruebas: 6 rutas oficiales + 6 pruebas del arnés")
    return ok("Batería completa en verde: 12 pruebas")


def validate_ablation() -> bool:
    text = (ROOT / "evidence" / "ablation.txt").read_text(encoding="utf-8")
    required = ["1 failed, 11 passed", "12 passed", "removed=I5", "overwrite_existing_output"]
    if not all(token in text for token in required):
        return fail("Evidencia de ablación/restauración incompleta")
    return ok("Ablación I5 muestra fallo y restauración vuelve a verde")


def validate_bitacora() -> bool:
    text = (ROOT / "bitacora.md").read_text(encoding="utf-8")
    required = ["R1 · Política y saldo", "R2 · Turno de portero", "R3 · Auditoría cruzada", "R4 · Implementación", "R5 · Ablación", "12 passed", "1 failed, 11 passed"]
    missing = [token for token in required if token not in text]
    return fail("Bitácora incompleta: " + ", ".join(missing)) if missing else ok("Bitácora cubre R1-R5 con evidencia literal")


def validate_cross_review(pre_review: bool) -> bool:
    if pre_review:
        return ok("Auditoría Gemini omitida en validación previa a R3")
    latest = ROOT / "audits" / "latest.json"
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail(f"audits/latest.json inválido: {exc}")
    if data.get("status") != "complete":
        return fail("La revisión cruzada Gemini aún no está completada")
    run_dir = ROOT / data["run_directory"]
    required = ["request.md", "peer_exchange.json", "peer_trace.jsonl", "our_audit_of_peer.json", "review.md", "manifest.json"]
    missing = [name for name in required if not (run_dir / name).exists()]
    if missing:
        return fail("Auditoría Gemini incompleta: " + ", ".join(missing))
    peer_rows = load_jsonl(run_dir / "peer_trace.jsonl")
    if len(peer_rows) != 15:
        return fail("La hoja digital de Gemini no contiene 15 filas")
    bitacora = (ROOT / "bitacora.md").read_text(encoding="utf-8")
    between = bitacora.split("<!-- CROSS_AUDIT_START -->", 1)[1].split("<!-- CROSS_AUDIT_END -->", 1)[0]
    if "Google Gemini" not in between or "Mi auditoría de la hoja producida por Gemini" not in between:
        return fail("La bitácora no incorpora las cinco respuestas de la hoja ajena")
    return ok(f"Revisión cruzada Gemini completa: {data['run_id']}")


def validate_no_secret() -> bool:
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    if "replace_with" not in env:
        return fail(".env.example parece contener una credencial real")
    return ok("La API key no se registra en los artefactos versionados")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-review", action="store_true", help="No exige todavía la corrida externa de Gemini")
    args = parser.parse_args()
    checks = [
        validate_required_files(),
        validate_trace(),
        validate_path_resolver_source(),
        validate_tests(),
        validate_ablation(),
        validate_bitacora(),
        validate_cross_review(args.pre_review),
        validate_no_secret(),
    ]
    print()
    if all(checks):
        print("VALIDACIÓN S04 SUPERADA" + (" (PRE-REVIEW)" if args.pre_review else ""))
        return 0
    print("VALIDACIÓN S04 FALLIDA")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
