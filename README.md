# S04 — El portero: arnés de ejecución

Implementación de Semana 4 sobre la fábrica T1 construida en Semana 3.

## Entregables principales

- `TRACE/portero.jsonl`: hoja de traza digital de las 15 solicitudes.
- `bitacora.md`: evidencia R1–R5, incluida auditoría cruzada con Gemini.
- `harness/paths.py`: resolutor único de rutas.
- `harness/run.py`: puerta única de ejecución.
- `evals/test_paths.py`: seis casos oficiales del resolutor.
- `evals/test_arnes.py`: seis casos oficiales del arnés.
- `evidence/tests.txt`: salida literal de la batería en verde.
- `evidence/ablation.txt`: corrida con I5 retirado y corrida restaurada.
- `audits/`: revisión cruzada reproducible con Google Gemini.

## Decisiones de implementación

La hoja física de la actividad se reemplaza por **JSONL**, porque conserva una fila/evento por línea, es auditable, versionable y procesable por el agente externo. La revisión cruzada usa Gemini explícitamente como agente externo; no se presenta como participación humana.

La fábrica sigue declarada como **T1** desde `work_order.json`. El `PathResolver` implementa I1/I4/I5 y, además, I2/I3 porque la política de la actividad y la batería oficial incluyen esos casos.

## Validación

```bash
python -m pip install -r requirements.txt
python scripts/build_portero_trace.py
pytest -q
python scripts/run_ablation.py
python scripts/validate_submission.py
```

Antes de la corrida externa de Gemini puede usarse:

```bash
python scripts/validate_submission.py --pre-review
```

## Automatización

- `.github/workflows/validate.yml`: valida la entrega en cada push/PR.
- `.github/workflows/external-review.yml`: ejecuta la revisión cruzada con `GEMINI_API_KEY`, guarda la evidencia y actualiza la sección R3 de `bitacora.md`.

El workflow de revisión se dispara automáticamente cuando cambian la traza, política, solicitudes, prompt, schema o ejecutor de la auditoría.
