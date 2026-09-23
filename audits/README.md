# Auditorías de Semana 4

La revisión cruzada usa **Google Gemini como contraparte externa** y se declara expresamente como agente, no como persona humana.

Cada corrida nueva queda en \`audits/runs/<run_id>/\` con:

- \`request.md\`: solicitud exacta enviada al agente;
- \`peer_exchange.json\`: salida estructurada completa;
- \`peer_trace.jsonl\`: hoja digital producida por Gemini para que el autor la audite;
- \`our_audit_of_peer.json\`: respuestas reconstruidas desde esa hoja;
- \`review.md\`: ambas direcciones de la revisión cruzada;
- \`manifest.json\`: modelo, commit, timestamps y hashes.

\`audits/cross_audit.md\` y \`audits/latest.json\` apuntan a la corrida utilizada en la entrega.
