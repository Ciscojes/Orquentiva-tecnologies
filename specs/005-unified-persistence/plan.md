# PLAN-005

1. Reutilizar Business, Service y Appointment; la migración inicial ya incluye
   tablas y unicidad (business_id, starts_at). No hace falta otra migración de esquema.
2. Sustituir sqlite3 y el arranque con init_db por sesiones inyectadas con get_db.
3. Normalizar la fecha a UTC antes de insertar. La restricción única de la base
   resuelve la carrera entre solicitudes; no usar comprobación previa como garantía.
4. SQLAlchemy convierte las fechas en UTC para SQLite de pruebas; al serializar
   sus fechas sin tzinfo se interpretan como UTC. PostgreSQL mantiene zona horaria.
5. Hacer inyectable la fábrica de sesiones del seed para reutilizar los mismos
   datos demo en pruebas sin alterar la configuración normal.
6. Crear fixtures por prueba con tablas y seed en SQLite temporal. Ejecutar en
   PostgreSQL temporal la concurrencia real y comparación de metadatos Alembic/ORM.
7. Documentar la separación entre cambio de código y traslado de datos históricos.
