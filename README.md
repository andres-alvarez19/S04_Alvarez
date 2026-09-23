# S03 — Cumplimiento malicioso y subasta de criterios

Entrega final para el encargo **E-6: convertir informes de defecto en casos de prueba ejecutables**.

## Artefactos principales

- `work_order.json`: orden final **después** de R3 y de la subasta.
- `bitacora.md`: cinco criterios iniciales, autoataques, revisión externa, respuestas, reescrituras y decisión de alcance.
- `blocking_questions.md`: datos que siguen bloqueando una corrida real.
- `evals/`: banco mínimo obligatorio de abstención, adversario y agotamiento.
- `auction.json`: subasta machine-readable, 90/100 fichas.
- `schemas/work_order.json`: schema local reconstruido desde la plantilla del apunte.
- `audits/`: evidencia inmutable de la revisión externa y su resolución.
- `scripts/validate_submission.py`: validación integral de la entrega.

## Alcance final

La revisión adversarial obligó a endurecer AC-01, AC-02 y AC-03. AC-03 dejó de ser una comprobación superficial de
10 fichas y pasó a un test de repositorio en aislamiento de 25 fichas.

La subasta final queda:

| Criterio | Coste | Estado |
|---|---:|---|
| AC-01 | 40 | comprado |
| AC-02 | 25 | comprado |
| AC-03 | 25 | comprado |
| AC-04 | 15 | no comprado → no-objetivo |
| AC-05 | 25 | no comprado → no-objetivo |

**Gastado: 90/100.**

El `work_order.json` contiene únicamente los criterios comprados; los no comprados se conservan como no-objetivos con
condición explícita de reapertura.

## Revisión cruzada externa

La revisión se ejecutó y quedó auditada:

- Run: `gha-35804447917-1`
- Commit evaluado: `d96fbedc22f124a88ace251d9a4dcb91be92ffab`
- Proveedor: Google Gemini
- Modelo efectivo: `gemini-3.5-flash-lite`
- Evidencia: `audits/runs/gha-35804447917-1/`
- Resolución de ataques: `audits/resolutions/gha-35804447917-1.json`

Los ataques válidos sobre AC-01, AC-02 y AC-03 fueron aceptados y cerrados mediante reescritura. AC-04 resistió. La objeción
a AC-05 no se aceptó como ataque R3 porque no incluyó una salida concreta y dependía de una decisión posterior de la subasta;
AC-05 igualmente quedó fuera del alcance por presupuesto.

## Validación

```bash
python -m pip install -r requirements.txt
python scripts/test_external_review_config.py
python scripts/validate_submission.py
```

El validador comprueba esquema, correspondencia entre subasta y orden final, banco mínimo, trazabilidad de R3, integridad
de hashes de la auditoría y resolución explícita de los cambios posteriores al ataque.

## Nota metodológica

`schemas/work_order.json` es una reconstrucción local basada en el material entregado, porque no se encontró el schema oficial
del repositorio de la asignatura.

La revisión cruzada se realizó con un **agente externo**, no con otro estudiante humano. La evidencia no oculta esa diferencia.
Si el docente exige literalmente participación humana, esa condición administrativa queda fuera de lo que puede demostrar
este repositorio.
