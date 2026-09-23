# Diseño del arnés S04

La puerta única sigue el orden: política → presupuesto previo → filtrado de contexto → ejecución → validación de salida → traza final. La traza se abre antes de las comprobaciones y se cierra en \`finally\`.

El resolutor es el único componente que convierte una ruta lógica \`project:\`/\`factory:\` en una ruta física. La contención usa \`Path.resolve()\` y \`Path.relative_to()\`, evitando comparaciones de prefijo sobre cadenas.

Los cuatro presupuestos se representan como pasos, tokens, tiempo y dinero. \`BudgetManager.reserve()\` verifica los cuatro antes de ejecutar. Al agotarse cualquiera, el \`Harness\` devuelve \`AGOTADO\` con checkpoint reanudable y sin invocar el componente.

El detector de contenido externo es un aviso, no la frontera de seguridad. Los fragmentos marcados no entran al contexto; se registra únicamente fuente/localizador y la corrida continúa.
