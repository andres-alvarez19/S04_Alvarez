# Incidente: Gemini 3.8 Flash respondió 503 por alta demanda

## Identificación

- Workflow: `external-agent-review`
- Run fallido: `35804280136`
- Fecha UTC: 2026-09-23
- Paso: `Run external adversarial review`
- Resultado: la configuración del schema fue aceptada, pero el servicio respondió 503.

## Evidencia

El SDK llegó a realizar la solicitud HTTP y terminó con:

```text
google.genai.errors.ServerError: 503 UNAVAILABLE
This model is currently experiencing high demand.
Spikes in demand are usually temporary. Please try again later.
```

Esto confirma que la corrección de `response_json_schema` resolvió el error anterior de validación local.

## Causa raíz

No fue un defecto del schema ni de la API key. Fue indisponibilidad temporal de capacidad del modelo
`gemini-3.8-flash`.

El SDK `google-genai` ya reintenta automáticamente errores transitorios como 429/500/502/503/504.
El 503 persistió incluso después de esos reintentos internos.

## Corrección

Se agregó un fallback explícito, restringido exclusivamente a modelos con Free tier y structured output:

1. `gemini-3.8-flash`
2. `gemini-3.5-flash`
3. `gemini-3.5-flash-lite`

Sólo se avanza al siguiente modelo ante códigos transitorios 429/500/502/503/504. Errores de
autenticación, permisos o configuración no se ocultan ni provocan fallback.

El `manifest.json` de una corrida exitosa registrará:

- modelo solicitado;
- modelo que finalmente respondió;
- fallos transitorios de modelos anteriores.

## Impacto sobre la auditoría

El run `35804280136` no produjo una revisión válida y no cuenta como R3. Se conserva como evidencia
operacional del intento fallido.
