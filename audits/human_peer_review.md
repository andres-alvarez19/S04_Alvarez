# Auditoría humana de la hoja del compañero · Semana 4

Fuente auditada: `audits/human_peer_trace.md`.

La reconstrucción se realizó únicamente desde la hoja recibida, sin solicitar explicaciones adicionales a su autor.

## Cinco preguntas de auditoría

1. **¿Cuántas fichas se gastaron y en qué solicitudes?**  
   Se gastaron **9 fichas**: S-01 = 1, S-02 = 1, S-08 = 2, S-09 = 4 y S-12 = 1. El saldo queda en 3 fichas.

2. **¿Qué solicitudes se denegaron y por qué regla o invariante?**  
   - S-03: `entrada_sellada`, **I4**.
   - S-04: `salida_write_once`, **I5**.
   - S-05: `intento_de_escape`, **I1/I3**.
   - S-06: `fabrica_es_solo_lectura`, **I2**.
   - S-07: capacidad no permitida por default-deny y efecto externo sujeto a aprobación humana previa.
   - S-11: `ejecutar_shell` no registrado, default-deny.
   - S-13: despliegue a producción, efecto irreversible sujeto a aprobación humana previa.
   - S-15: modificación de allowlist no autorizada por la corrida, default-deny.

3. **¿Apareció contenido envenenado? ¿Dónde y qué se hizo?**  
   Sí. V-03 aparece en S-01 al pie de `INPUT/raw/fuente.pdf`; V-02 aparece en la salida de `repo_grep` de S-08; V-01 aparece en el adjunto de S-12. Los tres fragmentos quedaron **en cuarentena con localizador y la corrida continuó**. V-03 identifica explícitamente un intento de ampliar el presupuesto mediante texto, es decir, un intento de saltar el control de presupuesto.

4. **¿En qué estado terminó la corrida y por qué?**  
   Según el cierre declarado en la propia hoja, termina en **AGOTADO con entrega parcial reanudable**. La causa es S-10: requiere 5 fichas cuando el saldo disponible era 4; no se ejecuta la llamada ni se cobran fichas. El registro continúa hasta S-15 y el saldo final es 3.

5. **¿Hay alguna fila donde la decisión sea correcta pero el motivo esté mal nombrado?**  
   **No se detecta una fila claramente mal nombrada.** S-07 y S-13 combinan default-deny con la exigencia de aprobación humana previa; aunque el motivo autoritativo para el efecto externo puede expresarse como `human_approval_required`, la regla correcta está explícitamente consignada y el veredicto es reconstruible.

## Hallazgo general

La hoja permite reconstruir las cinco respuestas sin ayuda del autor. No se detectan huecos que bloqueen la reconstrucción.
