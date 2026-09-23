# Preguntas para cerrar ambigüedad

Estas preguntas derivan de las siete clases de dato bloqueante de la actividad y contienen únicamente datos que
siguen bloqueando una corrida real después de la subasta.

1. `source.test_runner` — ¿Cuál es el comando/runner autoritativo del repositorio objetivo?
   - A) el comando documentado por el repositorio;
   - B) el comando usado por CI;
   - C) si no existe ninguno, detener la admisión.
   - Coste de adivinar mal: producir archivos con forma de test que el repositorio real no descubre ni ejecuta.

2. `source.authority` — Si el informe de defecto contradice el comportamiento observable del repositorio, ¿qué fuente manda?
   - A) repositorio;
   - B) informe de defecto;
   - C) conservar ambos y marcar la contradicción como bloqueante.
   - Coste de adivinar mal: convertir una descripción obsoleta en un test que congela un comportamiento incorrecto.

El presupuesto de USD 0,50 / 300 s dejó de ser dato bloqueante de esta versión porque AC-04 no fue comprado en R4 y
quedó registrado como no-objetivo con condición de reapertura.

**Estado:** `needs_user_input` para cualquier corrida real que no tenga resueltos los puntos 1 y 2.
