# Incidente: fallo de structured output en primera revisión externa

## Identificación

- Workflow: `external-agent-review`
- Run fallido: `35804080176`
- Fecha UTC: 2026-09-23
- Paso: `Run external adversarial review`
- Resultado: fallo antes de enviar la solicitud al modelo.

## Síntoma

El SDK `google-genai` lanzó una excepción de Pydantic al procesar:

```text
properties.criteria_assessment.items.properties.suggested_rewrite.type
Input should be ... [input_value=['string', 'null']]
```

## Causa raíz

El cliente estaba enviando un JSON Schema estándar mediante la opción `response_schema`.

`response_schema` es interpretado por el SDK como el objeto OpenAPI/Gemini `Schema`, cuyo campo
`type` es un valor escalar del enum interno. Nuestro schema usa correctamente la forma JSON Schema:

```json
{
  "type": ["string", "null"]
}
```

por lo que la validación del cliente falló antes de realizar una llamada HTTP.

## Corrección

Se reemplazó:

```python
"response_schema": generation_schema
```

por:

```python
"response_json_schema": generation_schema
```

El SDK documenta `response_json_schema` como la alternativa destinada a JSON Schema estándar.
Además se agregó `scripts/test_external_review_config.py`, que comprueba en CI que:

- el schema puede asignarse a `GenerateContentConfig.response_json_schema`;
- `response_schema` queda sin uso;
- el ejecutor contiene el campo correcto.

## Impacto sobre la auditoría

No se generó una evaluación parcial ni evidencia de contenido del modelo, porque el fallo ocurrió antes
de enviar la solicitud. Por lo tanto, el run `35804080176` se conserva como evidencia de un intento
fallido, pero **no cuenta como revisión cruzada**.

La siguiente corrida exitosa será la primera revisión externa válida y deberá generar
`audits/latest.json` y `audits/runs/<run_id>/`.
