# Informe de defecto de ejemplo

ID: DEF-001
Título: El conversor rechaza una entrada válida con campo opcional ausente.

Pasos mínimos:
1. Preparar una entrada válida sin el campo opcional `comment`.
2. Ejecutar el componente bajo prueba.
3. Observar el resultado.

Resultado esperado:
La entrada es aceptada y el componente continúa.

Resultado observado:
La ejecución termina con error de validación.
