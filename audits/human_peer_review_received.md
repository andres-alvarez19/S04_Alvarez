## Ronda 3 · Auditoría cruzada (20 min)

**Procedimiento:** reconstruyo la corrida de mi compañero usando únicamente su hoja, como un auditor seis meses después y sin acceso al sistema. No corrijo sus decisiones: cada pregunta sin respuesta es un hallazgo con la fila concreta que lo impide.

**Hoja auditada de:**  Andres Alvarez (hoja digital «Hoja de traza · Semana 4», derivada de `TRACE/portero.jsonl`; 15 filas, columnas seq, solicitud, tipo de acceso, veredicto, motivo/invariante, fichas, saldo y cuarentena).

**Resultado global:** no encontré veredictos ni saldos incorrectos; las 15 decisiones son correctas y el saldo cuadra en cada fila (12 → 11 → 10 → 8 → 4 → 3). Los hallazgos son de reconstruibilidad, no de decisiones.

| # | Pregunta | Respuesta sobre la hoja ajena / fila que lo impide |
|---|---|---|
| 1 | ¿Cuántas fichas se gastaron y en qué solicitudes? | **Reconstruible.** 9 fichas: S-01 (1), S-02 (1), S-08 (2), S-09 (4), S-12 (1). Saldo final 3. |
| 2 | ¿Qué se denegó y por qué invariante exacto? | **Reconstruible con reparos.** S-03 → I4, S-04 → I5, S-05 → I1/I3, S-06 → I2. S-07 y S-13 (`human_approval_required`), S-11 (`capability_not_allowlisted`) y S-15 (`default_deny_meta_change`) se deniegan sin invariante de aislamiento. Reparos: filas S-07, S-11, S-13 y S-15 (hallazgo 3). |
| 3 | ¿Apareció contenido envenenado? ¿Dónde y qué se hizo? | **Reconstruible, pero incompleta.** Tres fragmentos en cuarentena: V-03 en `S-01:INPUT/raw/fuente.pdf#pie`, V-02 en `S-08:repo_grep[0]`, V-01 en `S-12:adjunto`; la corrida continuó en los tres. No dice qué intentaba cada uno (hallazgo 4). |
| 4 | ¿En qué estado terminó la corrida y por qué? | **NO reconstruible.** El estado terminal no está escrito; solo se infiere AGOTADO por S-10 y que no hubo ABORTADO. Fila que lo impide: el bloque «Cierre de corrida» (hallazgo 1). |
| 5 | ¿Hay decisión correcta con motivo mal nombrado? | **Parcial.** Ninguna decisión es incorrecta, pero varios motivos son opacos o fuera del vocabulario de la política: S-01, S-02, S-12 y S-14 (`policy_allow`), S-07 (`human_approval_required` oculta el default-deny) y S-15 (hallazgos 2 y 3). |

### Hallazgos sobre la hoja ajena (de mayor a menor peso)

1. **Falta el estado terminal.** El cierre cuenta «6 permitidas, 8 denegadas y 1 agotada», pero nunca dice que la corrida terminó en AGOTADO (parcial reanudable). La regla de los tres terminales pide nombrarlo. El cierre además afirma que se pueden responder las cinco preguntas «sin consultar al autor», y la pregunta 4 lo contradice. *Fila: «Cierre de corrida».*
2. **`policy_allow` no dice qué regla permitió** (S-01, S-02, S-12, S-14). No distingue lectura de INPUT, sandbox WORK y escritura en TRACE, así que un auditor no puede verificar que la zona admitía la operación. *Corrección: «INPUT admite lectura», «WORK sandbox», «TRACE escribible».*
3. **Motivos de S-07, S-11, S-13 y S-15 fuera del vocabulario de la política.** `human_approval_required` en S-07 oculta que `enviar_correo` tampoco está en la allowlist (primera razón: default-deny). S-15 no dice que la allowlist no la amplía la corrida ni el modelo. Los códigos en inglés y snake_case no coinciden con los términos de la carpeta de política (`entrada_sellada`, `default-deny`…).
4. **Las cuarentenas no dicen qué intentaba el fragmento.** Solo constan localizador y «la corrida continúa». La rúbrica C2 pide identificar V-03 como intento de saltar un control (ampliar el presupuesto por texto); aquí no se distingue de V-01 ni de V-02. *Corrección: añadir una frase, p. ej. «intenta ampliar el presupuesto por texto».*
5. **El coste de S-09 y S-10 no es verificable.** No aparece la conversión (0,18 USD = 3,6 fichas → 4) ni que S-10 necesitaba 5 con saldo 4. «Reanudable desde S-10» no dice qué efectos ya aplicados (S-02, S-14) quedan registrados con su clave de idempotencia.
6. **Falta la fila de saldo inicial.** Las 12 fichas solo aparecen en el cierre, no en la primera fila de la hoja como pide la guía.
7. **La hoja depende de otro archivo.** El encabezado declara `TRACE/portero.jsonl` como fuente de verdad, pero la ronda 3 exige reconstruir la corrida usando únicamente la hoja; además la entrega pide la hoja en papel y fotografiada, y esta versión es digital.
8. **Menor:** el tipo de acceso dice «escritura» en S-03, S-04 y S-06, donde la clasificación de la guía distingue «escritura fuera»; S-14 debería decir «escritura sandbox».

**Puntos fuertes de la hoja ajena:** todos los veredictos correctos con I4, I5, I1/I3 e I2 bien nombrados; S-10 resuelta como AGOTADO y no como denegación, sin cobro; tres cuarentenas con localizador legible y corrida continuando; columna de cuarentena separada del veredicto.

---

## Resolución de los hallazgos

Los hallazgos de reconstruibilidad fueron atendidos en la versión corregida de `TRACE/portero.md`: se añadió la fila de saldo inicial, el estado terminal explícito, motivos legibles según la política, explicación de los tres fragmentos envenenados, conversión de costes S-09/S-10 y clasificación de acceso ajustada. La hoja quedó autosuficiente para auditoría humana.

El comentario sobre claves de idempotencia se conserva como observación de la revisión, pero no se inventan claves ausentes de la traza: esas claves pertenecen al checkpoint del arnés y a sus pruebas, no a las columnas mínimas de la hoja de portero.
