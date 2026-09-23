# Configuración de revisión externa con Google Gemini

## Objetivo

Ejecutar una revisión adversarial independiente de los cinco criterios iniciales AC-01...AC-05 y dejar
un rastro auditable en el repositorio.

## Credencial

El código usa la variable de entorno `GEMINI_API_KEY`. **No se debe escribir la clave en el código,
README, archivos .env versionados ni logs.**

Para GitHub Actions:

1. Crear una clave para Gemini en Google AI Studio usando un proyecto del nivel gratuito.
2. En este repositorio abrir **Settings → Secrets and variables → Actions**.
3. Crear el repository secret **`GEMINI_API_KEY`** con el valor de la clave.
4. No crear un secret llamado distinto: el workflow sólo lee `GEMINI_API_KEY`.

En septiembre de 2026 Google exige claves compatibles con su esquema actual de autenticación; una
clave estándar antigua puede ser rechazada. Generar/administrar la clave desde Google AI Studio.

## Capa gratuita

El workflow solicita primero `gemini-3.8-flash`. Si Google devuelve un error transitorio persistente (429/500/502/503/504), el script usa como fallback `gemini-3.5-flash` y luego `gemini-3.5-flash-lite`. Los tres pertenecen al diseño de Free tier y admiten salida estructurada. Cada modelo aprovecha primero los reintentos internos del SDK. La intención es
trabajar con un proyecto Gemini en Free tier. El código no puede imponer el nivel de facturación de la
cuenta: si la clave pertenece a un proyecto con facturación habilitada, las condiciones de ese proyecto
prevalecen.

Para mantener el experimento en la capa gratuita:

- usar una clave asociada a un proyecto en nivel Free;
- no habilitar herramientas de búsqueda, Maps, batch ni otros servicios;
- mantener una sola ejecución manual por revisión;
- verificar los límites vigentes del proyecto en Google AI Studio.

En el nivel gratuito, Google indica que el contenido enviado puede utilizarse para mejorar sus productos. En esta entrega sólo se envían artefactos académicos/sintéticos versionados en un repositorio público; no deben incorporarse datos personales, secretos ni material confidencial al prompt de revisión.

## Ejecutar

En GitHub:

1. Abrir **Actions**.
2. Seleccionar **external-agent-review**.
3. Pulsar **Run workflow**.
4. El workflow parte con `gemini-3.8-flash` y sólo puede hacer fallback a la lista Free tier documentada; no acepta modelos arbitrarios.

El workflow:

1. valida la entrega local;
2. comprueba que el secret exista;
3. ejecuta `scripts/run_external_review.py`;
4. valida la respuesta estructurada;
5. guarda `request.md`, `review.json`, `review.md` y `manifest.json`;
6. hace commit de la auditoría generada.

## Reproducibilidad y seguridad frente a prompt injection

El prompt declara expresamente que los artefactos evaluados son datos no confiables. Esto es importante
porque el caso adversarial de la actividad contiene una instrucción incrustada que, de otro modo, podría
intentar redirigir al propio revisor.

La revisión usa salida JSON restringida por `schemas/external_review.json` y luego vuelve a validarla
localmente. También se exige:

- al menos tres ataques;
- ataques sobre al menos tres criterios distintos;
- al menos un ataque original;
- evaluación de exactamente AC-01...AC-05.

## Evidencia

Cada corrida queda en:

```text
audits/runs/<run_id>/
├── request.md
├── review.json
├── review.md
└── manifest.json
```

`manifest.json` contiene hashes SHA-256 de todas las entradas, del prompt y de la respuesta. No contiene
la clave ni un hash de la clave.
