## Ronda 3 · Auditoría cruzada (20 min)

**Procedimiento:** reconstruyo la corrida de mi compañero usando únicamente su hoja, como un auditor seis meses después y sin acceso al sistema. No corrijo sus decisiones: cada pregunta sin respuesta es un hallazgo con la fila concreta que lo impide.

**Hoja auditada de:** Andres Alvarez (hoja digital «Hoja de traza · Semana 4», derivada de `TRACE/portero.jsonl`; 15 filas, columnas seq, solicitud, tipo de acceso, veredicto, motivo/invariante, fichas, saldo y cuarentena).

**Resultado global:** no encontré veredictos ni saldos incorrectos; las 15 decisiones son correctas y el saldo cuadra en cada fila (12 → 11 → 10 → 8 → 4 → 3). Los hallazgos son de reconstruibilidad, no de decisiones.

| # | Pregunta | Respuesta sobre la hoja ajena / fila que lo impide |
|---|---|---|
| 1 | ¿Cuántas fichas se gastaron y en qué solicitudes? | **Reconstruible.** 9 fichas: S-01 (1), S-02 (1), S-08 (2), S-09 (4), S-12 (1). Saldo final 3. |
| 2 | ¿Qué se denegó y por qué invariante exacto? | **Reconstruible con reparos.** S-03 → I4, S-04 → I5, S-05 → I1/I3, S-06 → I2. S-07 y S-13 (`human_approval_required`), S-11 (`capability_not_allowlisted`) y S-15 (`default_deny_meta_change`) se deniegan sin invariante de aislamiento. Reparos: filas S-07, S-11, S-13 y S-15 (hallazgo 3). |
| 3 | ¿Apareció contenido envenenado? ¿Dónde y qué se hizo? | **Reconstruible, pero incompleta.** Tres fragmentos en cuarentena: V-03 en `S-01:INPUT/raw/fuente.pdf#pie`, V-02 en `S-08:repo_grep[0]`, V-01 en `S-12:adjunto`; la corrida continuó en los tres. No dice qué intentaba cada uno (hallazgo 4). |
| 4 | ¿En qué estado terminó la corrida y por qué? | **NO reconstruible.** El estado terminal no está escrito; solo se infiere AGOTADO por S-10 y que no hubo ABORTADO. Fila que lo impide: el bloque «Cierre de corrida» (hallazgo 1). |
| 5 | ¿Hay decisión correcta con motivo mal nombrado? | **Parcial.** Ninguna decisión es incorrecta, pero varios motivos son opacos o fuera del vocabulario de la política: S-01, S-02, S-12 y S-14 (`policy_allow`), S-07 (`human_approval_required` oculta el default-deny) y S-15 (hallazgos 2 y 3). |

### Hallazgos sobre la hoja ajena (de mayor a menor peso)

1. **Falta el estado terminal.** El cierre cuenta «6 permitidas, 8 denegadas y 1 agotada», pero nunca dice que la corrida terminó en AGOTADO (parcial reanudable). La regla de los tres terminales pide nombrarlo.
2. **`policy_allow` no dice qué regla permitió** (S-01, S-02, S-12, S-14). No distingue lectura de INPUT, sandbox WORK y escritura en TRACE.
3. **Motivos de S-07, S-11, S-13 y S-15 fuera del vocabulario de la política.**
4. **Las cuarentenas no dicen qué intentaba el fragmento.**
5. **El coste de S-09 y S-10 no es verificable.**
6. **Falta la fila de saldo inicial.**
7. **La hoja depende de otro archivo.**
8. **Menor:** ajustar los tipos de acceso a la clasificación de la guía.

**Puntos fuertes de la hoja ajena:** todos los veredictos correctos con I4, I5, I1/I3 e I2 bien nombrados; S-10 resuelta como AGOTADO y no como denegación, sin cobro; tres cuarentenas con localizador legible y corrida continuando; columna de cuarentena separada del veredicto.

---

## Resolución de los hallazgos

Los hallazgos de reconstruibilidad fueron atendidos en la versión corregida de `TRACE/portero.md`: se añadió el saldo inicial, el estado terminal explícito, motivos legibles según la política, explicación de los tres fragmentos envenenados, conversión de costes S-09/S-10 y clasificación de acceso ajustada. La hoja quedó autosuficiente para auditoría humana.

El comentario sobre claves de idempotencia se conserva como observación de la revisión, pero no se inventan claves ausentes de la traza: esas claves pertenecen al checkpoint del arnés y a sus pruebas, no a las columnas mínimas de la hoja de portero.
