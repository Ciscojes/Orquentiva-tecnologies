# PROJECT CHARTER — ORQENTIVA AI

**Tipo:** Proyecto integrador académico (TFM propuesto) y base de SaaS comercial.
**Estado:** prototipo académico; sujeto a validación del tutor y de la marca.
**Problema:** pequeñas empresas pierden solicitudes de clientes y gestionan reservas manualmente.
**Hipótesis:** un sistema multiempresa con agente conectado a información y herramientas verificables puede aumentar la tasa de tareas completadas y reducir tiempo de respuesta frente a un chatbot sin herramientas.
**Alcance TFM:** dos empresas de prueba; catálogo; reservas; agente con estado; RAG por empresa; controles de seguridad; evaluaciones; trazabilidad; despliegue reproducible.
**Fuera de alcance inicial:** facturación real, WhatsApp oficial, pagos, campañas publicitarias y clientes reales.

## Métricas que se evaluarán
- Exactitud de respuestas sobre el catálogo de cada empresa.
- Porcentaje de reservas completadas sin dobles reservas.
- Tasa de filtración de datos entre empresas (objetivo: cero en suite de pruebas).
- Latencia mediana y percentil 95 de solicitudes.
- Coste estimado por conversación cuando exista LLM.

## Arquitectura incremental
1. **Sprint 01:** FastAPI + SQLite + datos de dos empresas + pruebas.
2. **Sprint 02:** modelos robustos, PostgreSQL, migraciones, autorización.
3. **Sprint 03:** LangGraph con flujo de reservas validado.
4. **Sprint 04 (alcance actualizado):** captación de leads; ver SPEC-004. RAG y sus evaluaciones quedan pendientes en el roadmap.
5. **Sprint 05:** React, métricas, observabilidad y despliegue.

## Incremento de consolidación posterior a Sprint 04

SPEC-005 unifica servicios y reservas con SQLAlchemy/PostgreSQL, mantiene
aislamiento y unicidad por empresa/instante y retira la inicialización automática
de SQLite. El traslado de datos históricos se ejecuta por separado y explícitamente.

## Reglas de ingeniería
Especificación antes de nuevas funcionalidades, pytest en CI, separación de datos por empresa, secretos fuera del repositorio, pruebas de regresión, documentación incremental.

## Estado de consolidación del MVP

El roadmap anterior describe la planificación histórica. El MVP actual incorpora paneles, agenda por profesional, chat con LangGraph y recuperación extractiva por negocio. El LLM es opcional: interpreta campos de reserva (SPEC-014/017) y genera respuestas documentales con citas verificadas (SPEC-015). Sin LLM, la recuperación es extractiva. La hipótesis comparativa y p95 siguen sin evaluarse. Los resultados están en docs/evaluation-012.
