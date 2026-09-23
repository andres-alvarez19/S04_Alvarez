# Auditoría de revisión cruzada con agente externo

Esta carpeta conserva evidencia reproducible de la revisión adversarial ejecutada mediante Google Gemini y de las decisiones
tomadas después del ataque.

## Corridas

Cada corrida en `audits/runs/<run_id>/` contiene:

- `request.md`: prompt exacto enviado;
- `review.json`: respuesta estructurada sin editar;
- `review.md`: representación legible;
- `manifest.json`: proveedor, modelo, SDK, commit evaluado, timestamps, uso y hashes SHA-256.

**Nunca se registra la API key.**

## Resoluciones

Cuando una revisión obliga a cambiar los artefactos evaluados, el expediente original no se sobrescribe. La respuesta del
autor queda en `audits/resolutions/<run_id>.json`, donde se registra:

- qué ataques se aceptaron o rechazaron;
- cómo se cerró cada explotación;
- qué criterios se compraron después de recalcular la subasta;
- qué entradas cambiaron respecto del commit auditado.

Esto permite conservar simultáneamente el estado **antes del ataque** y la versión **después de la defensa**.

## Corrida vigente

La revisión utilizada para esta entrega es `gha-35804447917-1`, identificada también por `audits/latest.json`.

## Alcance académico

La revisión fue realizada por un **agente externo** y no se presenta como revisión humana. Esto produce evidencia técnica
independiente y reproducible, pero no afirma sustituir una exigencia administrativa de participación de otro estudiante.
