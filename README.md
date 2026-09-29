# S04 — El portero: arnés de ejecución

Implementación de Semana 4 sobre la fábrica T1 construida en Semana 3.

## Entregables principales

- `TRACE/portero.jsonl`: traza técnica reproducible de las 15 solicitudes.
- `TRACE/portero.md`: hoja autosuficiente y legible para auditoría humana.
- `bitacora.md`: evidencia R1–R5, incluida auditoría cruzada humana y revisión recibida.
- `harness/paths.py`: resolutor único de rutas.
- `harness/run.py`: puerta única de ejecución.
- `evals/test_paths.py`: seis casos oficiales del resolutor.
- `evals/test_arnes.py`: seis casos oficiales del arnés.
- `evidence/tests.txt`: salida literal de la batería en verde.
- `evidence/ablation.txt`: corrida con I5 retirado y corrida restaurada.
- `audits/human_peer_trace.md`: hoja recibida del compañero.
- `audits/human_peer_review.md`: mi auditoría de la hoja del compañero.
- `audits/human_peer_review_received.md`: auditoría que mi compañero realizó sobre mi hoja.
- `audits/`: conserva además la revisión automatizada de Google Gemini como evidencia complementaria.

## Decisiones de implementación

La traza técnica se conserva en **JSONL** por ser auditable y reproducible, y se deriva una hoja Markdown autosuficiente para la revisión humana. La revisión cruzada principal se realizó con un compañero; Gemini queda explícitamente como evidencia automatizada complementaria y no se presenta como participación humana.

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
