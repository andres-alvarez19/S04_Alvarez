#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def fail(msg):
    print(f"[FAIL] {msg}")
    return False


def ok(msg):
    print(f"[OK] {msg}")
    return True


def warn(msg):
    print(f"[WARN] {msg}")
    return True


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def sha256_path(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_schema(instance, schema):
    try:
        import jsonschema
    except ImportError:
        return fail("Falta dependencia: pip install jsonschema")

    try:
        jsonschema.Draft202012Validator(schema).validate(instance)
        return ok("work_order.json cumple el schema local")
    except jsonschema.ValidationError as e:
        route = "/".join(map(str, e.path)) or "<root>"
        return fail(f"Schema local: {e.message} (ruta: {route})")


def validate_semantics(wo, auction):
    valid = True
    purchased_ids = {
        item["criterion_id"]
        for item in auction["items"]
        if item["status"] == "purchased"
    }
    final_ids = {item["id"] for item in wo["acceptance"]}

    if final_ids != purchased_ids:
        valid &= fail(
            "work_order.json debe contener exactamente los criterios comprados en la subasta: "
            f"esperados={sorted(purchased_ids)}, actuales={sorted(final_ids)}"
        )
    else:
        valid &= ok("work_order.json contiene exactamente los criterios comprados")

    if not any(x["verification"].startswith("validator:") for x in wo["acceptance"]):
        valid &= fail("El alcance final no conserva ningún validador con umbral")
    else:
        valid &= ok("El alcance final conserva un validador con umbral")

    if not any(x["verification"].startswith("test:") for x in wo["acceptance"]):
        valid &= fail("El alcance final no conserva ningún test nombrado")
    else:
        valid &= ok("El alcance final conserva tests nombrados")

    negative_tokens = ("ningún", "ninguna", " no ", "prohib")
    if not any(
        any(tok in (" " + item["criterion"].lower() + " ") for tok in negative_tokens)
        for item in wo["acceptance"]
    ):
        valid &= fail("No se detectó una restricción negativa en el alcance final")
    else:
        valid &= ok("El alcance final conserva una restricción negativa")

    if len(wo["no_objectives"]) < 3:
        valid &= fail("Se requieren al menos tres no-objetivos")
    else:
        valid &= ok("Hay al menos tres no-objetivos")

    qb = wo["question_budget"]
    if qb["max_blocking_questions"] > 6 or qb["max_rounds"] > 2:
        valid &= fail("El presupuesto de preguntas excede 6 bloqueantes / 2 rondas")
    else:
        valid &= ok("Presupuesto de preguntas dentro del límite de la guía")

    return bool(valid)


def validate_auction(wo, auction):
    valid = True
    purchased = sum(
        item["cost"] for item in auction["items"] if item["status"] == "purchased"
    )

    if purchased != auction["spent"]:
        valid &= fail("auction.json: spent no coincide con la suma comprada")
    else:
        valid &= ok(f"Subasta consistente: {purchased}/{auction['budget_total']} fichas")

    if purchased > auction["budget_total"]:
        valid &= fail("La subasta excede 100 fichas")

    if auction["remaining"] != auction["budget_total"] - auction["spent"]:
        valid &= fail("auction.json: remaining no coincide con budget_total - spent")
    else:
        valid &= ok(f"Saldo de subasta consistente: {auction['remaining']} fichas")

    not_purchased = [
        item for item in auction["items"] if item["status"] == "not_purchased"
    ]
    if not not_purchased:
        valid &= fail("No hay criterios movidos fuera de alcance")
    elif not all(item.get("reopen_condition") for item in not_purchased):
        valid &= fail("Falta condición de reapertura en algún criterio no comprado")
    else:
        valid &= ok("Todos los criterios no comprados tienen condición de reapertura")

    no_objectives = " ".join(wo["no_objectives"]).lower()
    for item in not_purchased:
        condition = item["reopen_condition"].lower()
        key_tokens = [
            token for token in ("15 fichas", "25 fichas", "ledger", "traceability")
            if token in condition
        ]
        if key_tokens and not any(token in no_objectives for token in key_tokens):
            valid &= fail(
                f"No se encuentra en no-objetivos evidencia de reapertura para {item['criterion_id']}"
            )

    if valid:
        valid &= ok("Los criterios no comprados quedaron fuera de alcance con reapertura")

    return bool(valid)


def load_jsonl(path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path.name}:{n}: {e}") from e
    return rows


def validate_evals():
    valid = True
    required = {
        "caso_abstencion.jsonl": "abstention",
        "caso_adversario.jsonl": "adversary",
        "caso_agotamiento.jsonl": "budget_exhaustion",
    }

    for fn, typ in required.items():
        path = ROOT / "evals" / fn
        if not path.exists():
            valid &= fail(f"Falta {fn}")
            continue

        try:
            rows = load_jsonl(path)
        except ValueError as e:
            valid &= fail(str(e))
            continue

        if not rows:
            valid &= fail(f"{fn} está vacío")
            continue

        row = rows[0]
        if row.get("case_type") != typ:
            valid &= fail(f"{fn}: case_type incorrecto")
            continue

        if not all(k in row for k in ("input", "initial_state", "expected_verdict")):
            valid &= fail(f"{fn}: faltan input/initial_state/expected_verdict")
            continue

        verdict = row["expected_verdict"]
        if typ == "abstention" and not verdict.get("missing_evidence"):
            valid &= fail("Abstención: debe nombrar la evidencia que cierra la brecha")
            continue
        if typ == "adversary" and not verdict.get("quarantined_fragment"):
            valid &= fail("Adversario: debe contener fragmento puesto en cuarentena")
            continue
        if typ == "budget_exhaustion" and not verdict.get("resume_trace"):
            valid &= fail("Agotamiento: debe contener traza de reanudación")
            continue

        valid &= ok(f"{fn} cumple controles mínimos")

    return bool(valid)


def validate_bitacora():
    path = ROOT / "bitacora.md"
    if not path.exists():
        return fail("Falta bitacora.md")

    text = path.read_text(encoding="utf-8")
    valid = True

    for cid in [f"AC-0{i}" for i in range(1, 6)]:
        if cid not in text:
            valid &= fail(f"bitacora.md no documenta {cid}")

    for flavor in ("validator:", "test:", "ledger:"):
        if flavor not in text:
            valid &= fail(f"bitacora.md no conserva el sabor inicial {flavor}")

    if "gha-35804447917-1" not in text:
        valid &= fail("bitacora.md no referencia la corrida de revisión externa")

    if "aceptado" not in text.lower() or "rechazada" not in text.lower():
        valid &= fail("bitacora.md no documenta respuestas a ataques recibidos")

    if "Total gastado: 90" not in text:
        valid &= fail("bitacora.md no documenta la subasta final de 90 fichas")

    if valid:
        valid &= ok(
            "bitacora.md conserva 5 criterios iniciales, tres sabores, ataques y respuestas R3"
        )

    return bool(valid)


def validate_external_review_setup():
    required = [
        "prompts/external_review.md",
        "schemas/external_review.json",
        "scripts/run_external_review.py",
        ".github/workflows/external-review.yml",
        ".env.example",
        ".gitignore",
        "docs/external-review.md",
    ]
    missing = [relative for relative in required if not (ROOT / relative).exists()]
    if missing:
        return fail(
            "Configuración de revisión externa incompleta: faltan "
            + ", ".join(missing)
        )

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    if "google-genai" not in requirements:
        return fail("requirements.txt no incluye google-genai")

    prompt = (ROOT / "prompts" / "external_review.md").read_text(encoding="utf-8")
    if "datos no confiables" not in prompt.lower():
        return fail("El prompt externo no declara los artefactos como datos no confiables")

    return ok("Configuración de revisión externa Gemini completa")


def validate_external_audit(wo, auction):
    latest_path = ROOT / "audits" / "latest.json"
    if not latest_path.exists():
        return fail("No existe audits/latest.json: falta la revisión externa ejecutada")

    try:
        import jsonschema
    except ImportError:
        return fail("Falta dependencia jsonschema para verificar la auditoría externa")

    latest = load_json(latest_path)
    run_id = latest["run_id"]
    run_dir = ROOT / latest["run_directory"]
    required = ["request.md", "review.json", "review.md", "manifest.json"]
    missing = [name for name in required if not (run_dir / name).exists()]
    if missing:
        return fail(f"Auditoría externa incompleta: faltan {', '.join(missing)}")

    schema = load_json(ROOT / "schemas" / "external_review.json")
    review = load_json(run_dir / "review.json")
    manifest = load_json(run_dir / "manifest.json")

    try:
        jsonschema.Draft202012Validator(schema).validate(review)
    except jsonschema.ValidationError as e:
        route = "/".join(map(str, e.path)) or "<root>"
        return fail(f"review.json no cumple schema externo: {e.message} ({route})")

    valid = True
    attacks = review["attacks"]
    attacked_ids = {item["criterion_id"] for item in attacks}
    if len(attacks) < 3 or len(attacked_ids) < 3:
        valid &= fail("La auditoría externa no contiene tres ataques sobre criterios distintos")
    else:
        valid &= ok("Auditoría externa contiene al menos tres ataques sobre criterios distintos")

    if not any(item["is_original"] for item in attacks):
        valid &= fail("La auditoría externa no contiene ataque original")
    else:
        valid &= ok("Auditoría externa contiene al menos un ataque original")

    expected = {f"AC-0{i}" for i in range(1, 6)}
    assessed = {item["criterion_id"] for item in review["criteria_assessment"]}
    if assessed != expected:
        valid &= fail("La auditoría externa no evalúa exactamente AC-01...AC-05")
    else:
        valid &= ok("Auditoría externa evalúa exactamente AC-01...AC-05")

    review_hash = sha256_path(run_dir / "review.json")
    request_hash = sha256_path(run_dir / "request.md")
    if review_hash != manifest.get("review_sha256"):
        valid &= fail("Hash de review.json no coincide con manifest.json")
    elif review_hash != latest.get("review_sha256"):
        valid &= fail("Hash de review.json no coincide con audits/latest.json")
    else:
        valid &= ok("Hash de review.json verificado")

    if request_hash != manifest.get("request_sha256"):
        valid &= fail("Hash de request.md no coincide con manifest.json")
    else:
        valid &= ok("Hash de request.md verificado")

    changed_inputs = []
    for relative, expected_hash in manifest.get("input_sha256", {}).items():
        path = ROOT / relative
        if not path.exists():
            valid &= fail(f"Entrada auditada ya no existe: {relative}")
            continue
        if sha256_path(path) != expected_hash:
            changed_inputs.append(relative)

    if changed_inputs:
        resolution_path = ROOT / "audits" / "resolutions" / f"{run_id}.json"
        if not resolution_path.exists():
            valid &= fail(
                "La auditoría es histórica porque cambiaron entradas, pero falta su resolución R3"
            )
        else:
            resolution = load_json(resolution_path)
            expected_changed = sorted(resolution.get("changed_inputs", []))
            if sorted(changed_inputs) != expected_changed:
                valid &= fail(
                    "Los archivos modificados tras R3 no coinciden con la resolución auditada: "
                    f"detectados={sorted(changed_inputs)}, declarados={expected_changed}"
                )
            elif resolution.get("status") != "resolved":
                valid &= fail("La resolución R3 no está marcada como resolved")
            elif resolution.get("audit_run_id") != run_id:
                valid &= fail("La resolución R3 apunta a otra corrida")
            else:
                purchased_ids = sorted(
                    item["criterion_id"]
                    for item in auction["items"]
                    if item["status"] == "purchased"
                )
                final_ids = sorted(item["id"] for item in wo["acceptance"])
                if resolution.get("final_purchased_ids") != purchased_ids:
                    valid &= fail("La resolución R3 no coincide con la subasta final")
                elif final_ids != purchased_ids:
                    valid &= fail("La orden final no coincide con la resolución R3")
                else:
                    valid &= ok(
                        "Auditoría histórica resuelta: cambios posteriores a R3 están trazados"
                    )
    else:
        valid &= ok("Auditoría externa corresponde exactamente a los artefactos actuales")

    if valid:
        valid &= ok(
            f"Auditoría externa íntegra: {run_id} / modelo {latest.get('model')}"
        )

    return bool(valid)


def main():
    wo = load_json(ROOT / "work_order.json")
    schema = load_json(ROOT / "schemas" / "work_order.json")
    auction = load_json(ROOT / "auction.json")

    checks = [
        validate_schema(wo, schema),
        validate_semantics(wo, auction),
        validate_auction(wo, auction),
        validate_evals(),
        validate_bitacora(),
        validate_external_review_setup(),
        validate_external_audit(wo, auction),
    ]

    print()
    if all(checks):
        print("VALIDACIÓN LOCAL SUPERADA")
        return 0

    print("VALIDACIÓN LOCAL FALLIDA")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
