# Persistencia unificada — SPEC-005

## Punto de partida

Commit confirmado: 184dac2, creado por el usuario para cerrar el avance del
Sprint 04. El repositorio estaba limpio antes de este incremento.

## Cambio

Empresas, servicios, reservas y leads utilizan get_db y la misma configuración
SQLAlchemy/PostgreSQL. Se retiraron sqlite3, DB_PATH, init_db y los datos demo
automáticos del arranque. Alembic prepara el esquema; seed.py sigue siendo explícito.
Las tablas y la restricción única ya existían: no se necesita otra migración de esquema.

POST /appointments normaliza a UTC y se apoya en la restricción única por empresa
e instante. Mantiene los errores 422/409 y añade 404 para empresa inexistente y
503 ante fallo al guardar sin detalles SQL. Los listados están filtrados por
empresa y ordenados por instante. Se mantienen los contratos del frontend.

## Verificación

- 42 pruebas backend: regresiones existentes, persistencia mediante sesiones
  inyectadas, ausencia de escritura al arrancar, importación histórica en solo
  lectura, conflictos, idempotencia y transacción con empresas/servicios nuevos.
- PostgreSQL temporal: migraciones y ORM coinciden, seed repetible, aislamiento,
  reservas simultáneas (una 201 y una 409), offsets equivalentes, UTC,
  microsegundos, leads e importación histórica simulada y repetible.
- El servidor temporal se detiene al terminar y sus archivos se eliminan.
- No se modificaron las dependencias ni el frontend en este incremento.

## Reserva histórica y cambio de entorno

La inspección del SQLite habitual se hizo en modo lectura y mostró dos empresas,
dos servicios y una reserva. El usuario confirmó que orqentiva_db es de desarrollo
y autorizó trasladar la reserva. La simulación confirmó cero conflictos: solo
faltaba insertar una reserva; las empresas y los servicios ya existían.

La reserva ya fue trasladada y su contenido fue comprobado desde la API unificada.
Se verificó una sola inserción, ningún cambio en registros previos de PostgreSQL,
archivo SQLite intacto mediante SHA-256 y una segunda simulación sin datos pendientes.
Se conservó una copia local del SQLite anterior al traslado. No se imprimieron
nombres ni fechas de la reserva.
`scripts/import_legacy_sqlite.py` permite revisarlo sin escribir por defecto.
En PostgreSQL la simulación utiliza una transacción READ ONLY.

El modo --apply se ejecutó después de confirmar con el usuario la base de desarrollo
y el traslado concreto, respetando la exclusión de producción. Inserta únicamente registros faltantes y aborta ante
conflictos; no sobrescribe ni borra registros y puede repetirse sin duplicados.
Las pruebas automatizadas de importación se ejecutaron sobre bases temporales.
La importación de esta única reserva se verificó además en la base de desarrollo
autorizada. Docker y PostgreSQL local volvieron a estar disponibles; no queda
pendiente el traslado histórico. No se modificó ninguna base de producción.

## Uso

Simulación con la base configurada:

```powershell
python scripts/import_legacy_sqlite.py --source .\orqentiva.db
```

Repetir la integración aislada:

```powershell
python scripts/verify_postgres.py --postgres-bin "C:\Program Files\PostgreSQL\17\bin"
```

## Límites conservados

Las claves de empresas siguen siendo demo y el límite de leads sigue siendo
por proceso. Autenticación real y protección distribuida son incrementos
posteriores. La advertencia de deprecación TestClient/httpx del entorno no
bloquea las pruebas. No se creó ningún commit automáticamente.
