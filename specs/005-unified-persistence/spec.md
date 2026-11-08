# SPEC-005 — Persistencia unificada

## Objetivo

Que empresas, servicios, reservas y leads utilicen la misma base configurada
mediante SQLAlchemy; PostgreSQL para el entorno de ejecución normal.

## Criterios de aceptación

1. GET /services y GET/POST /appointments utilizan get_db y los modelos ORM existentes.
2. Se conservan los campos de respuesta, claves demo y aislamiento por empresa.
3. Nombre recortado de 1–100 caracteres; fecha con zona horaria; respuesta en UTC.
4. Un mismo instante por empresa genera una sola reserva, incluso concurrentemente;
   la otra solicitud devuelve 409. Empresas distintas pueden reservar ese instante.
5. Las reservas se listan por instante, manteniendo precisión de microsegundos.
6. Empresa inexistente al reservar devuelve 404; un fallo al guardar devuelve 503 sin detalles SQL.
7. Arrancar o importar la API no crea tablas, no introduce datos demo ni abre el SQLite anterior.
8. Alembic y seed explícito siguen siendo los mecanismos de preparación; no se
   ejecutan sobre la base habitual durante este incremento.
9. Pruebas SQLite temporales por caso y una integración PostgreSQL temporal verifican
   servicios, reservas, concurrencia, aislamiento y leads.

## Datos anteriores

Este cambio traslada las operaciones de la API; no copia automáticamente los datos
del antiguo orqentiva.db a PostgreSQL. El archivo antiguo se conserva. Cualquier
traslado de registros históricos requiere un procedimiento explícito y revisado.
Se incluye un script de simulación (predeterminado) y aplicación opcional:
abre la fuente solo en lectura, normaliza fechas UTC, rechaza conflictos,
inserta de forma transaccional y permite repetirlo sin duplicar filas.

## Fuera de alcance

Autenticación real, paneles, LangGraph/RAG, agentes de voz y migración automática
de datos históricos. No se cambia el contrato del formulario de leads.
