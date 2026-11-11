# Evaluación de extracción del chat de reservas

Casos: 40 · modelo: openai/gpt-oss-20b · fecha fija de los casos: ver evals/extraction_cases.json

| Campo | Solo reglas | Solo propuesta del LLM | Reglas + LLM |
| --- | ---: | ---: | ---: |
| Servicio | 29/40 (72 %) | 39/40 (98 %) | 40/40 (100 %) |
| Profesional | 40/40 (100 %) | 40/40 (100 %) | 40/40 (100 %) |
| Día | 37/40 (92 %) | 36/40 (90 %) | 40/40 (100 %) |
| Hora | 34/38 (89 %) | 38/38 (100 %) | 38/38 (100 %) |
| Nombre | 37/40 (92 %) | 39/40 (98 %) | 39/40 (98 %) |
| **Caso completo** | 21/40 (52 %) | 34/40 (85 %) | 39/40 (98 %) |

Llamadas fallidas (el chat siguió solo con reglas): 0/40.
Latencia de la llamada al LLM: mediana 1.46 s · p95 1.95 s · máxima 2.06 s.

## Fallos de reglas + LLM

| Caso | Campo | Esperado | Obtenido |
| --- | --- | --- | --- |
| es-01 | Nombre | vacío | Ana |

## Condiciones y límites

Ejecución real: 10 de noviembre de 2026 (Costa Rica). Proveedor: Groq, modelo
openai/gpt-oss-20b. Se utilizaron los 40 casos ficticios del repositorio, temperatura
0 y pausa de 3 segundos entre llamadas. La pausa no está incluida en la latencia
indicada. No se crearon reservas ni se enviaron datos de clientes reales.

Una ejecución sobre este conjunto conocido no mide generalización, carga concurrente,
calidad del RAG ni satisfacción de usuarios. No se recogieron tokens ni coste de
facturación. Los porcentajes de la tabla están redondeados: 39/40 equivale a 97,5 %.
El caso es-01 confunde el nombre de la profesional con el del cliente. La reserva
sigue necesitando revisión del resumen y confirmación explícita.
