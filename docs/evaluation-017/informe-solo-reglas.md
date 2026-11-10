# Evaluación de extracción del chat de reservas

Casos: 40 · modelo: ninguno (solo reglas) · fecha fija de los casos: ver evals/extraction_cases.json

| Campo | Solo reglas |
| --- | ---: |
| Servicio | 29/40 (72 %) |
| Profesional | 40/40 (100 %) |
| Día | 37/40 (92 %) |
| Hora | 34/38 (89 %) |
| Nombre | 37/40 (92 %) |
| **Caso completo** | 21/40 (52 %) |

## Fallos de solo reglas

| Caso | Campo | Esperado | Obtenido |
| --- | --- | --- | --- |
| es-03 | Servicio | 1 | vacío |
| es-03 | Hora | 10:30 | vacío |
| es-04 | Servicio | 2 | vacío |
| es-10 | Día | 2026-11-20 | 2026-11-13 |
| es-11 | Nombre | Pedro | vacío |
| es-12 | Nombre | Laura Gómez | vacío |
| es-14 | Servicio | 1 | vacío |
| es-19 | Servicio | 3 | vacío |
| es-20 | Día | 2026-11-25 | vacío |
| es-27 | Día | 2026-11-24 | 2026-11-17 |
| es-28 | Hora | 10:15 | vacío |
| es-29 | Hora | 12:00 | vacío |
| en-01 | Servicio | 1 | vacío |
| en-02 | Servicio | 2 | vacío |
| en-03 | Servicio | 3 | vacío |
| en-04 | Servicio | 4 | vacío |
| en-05 | Servicio | 1 | vacío |
| en-05 | Nombre | John Smith | vacío |
| en-07 | Servicio | 1 | vacío |
| en-08 | Hora | 10:30 | vacío |
| en-09 | Servicio | 4 | vacío |
