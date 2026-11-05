# ORQENTIVA AI — MVP TFM con panel administrativo (SPEC-008)

## Captación de leads

`POST /leads` acepta nombre, correo, empresa opcional, servicio y mensaje.
Los servicios permitidos son `agents`, `automation`, `growth` y `saas`.
No requiere claves de las empresas ni ofrece listado público.
Devuelve HTTP 201 al guardar; 422 ante datos inválidos; 429 ante exceso de envíos;
503 si no puede guardar. El formulario React permite enviar en español e inglés.

Para el desarrollo, ejecutar la API en `127.0.0.1:8001` y, desde `frontend`,
`npm install` y `npm run dev`. Vite reenvía `/leads` a la API.
En producción debe configurarse una ruta del mismo origen hacia el backend;
`vite preview` no sustituye esa configuración.

La conexión PostgreSQL usa la configuración local existente y `POSTGRES_PASSWORD`
en `.env`. `DATABASE_URL` permite seleccionar explícitamente otra base de datos.
No colocar credenciales en React ni registrar estas variables.
Los tests fuerzan bases SQLite temporales y no necesitan `.env`.

`/business/me`, `/services`, `/appointments` y `/leads` utilizan la misma base
SQLAlchemy/PostgreSQL configurada. El arranque no crea tablas ni datos demo.
SQLite se utiliza únicamente en pruebas aisladas y como fuente histórica explícita.
El límite de leads es básico, en memoria y por proceso (5 envíos/IP/minuto).
Para varias instancias se necesita un contador compartido y proxies de confianza configurados.

Ver `docs/PERSISTENCIA_UNIFICADA.md` y `specs/005-unified-persistence/`.

Las reservas se guardan con fecha UTC. La restricción única de PostgreSQL impide
duplicados por empresa e instante, incluso con solicitudes simultáneas y offsets diferentes.
El listado se ordena por instante y los nombres se validan después de quitar espacios.

Los registros del antiguo `orqentiva.db` no se copian automáticamente. Para revisar
un traslado sin escribir en la base de destino:

```powershell
python scripts/import_legacy_sqlite.py --source .\orqentiva.db
```

El script muestra solo cantidades y detecta conflictos. `--apply` realiza un traslado
explícito en una transacción; requiere revisar previamente la base de destino y la simulación.
No borra el archivo fuente ni reemplaza datos existentes.

Para repetir la integración en una instancia PostgreSQL temporal independiente:

```powershell
python scripts/verify_postgres.py --postgres-bin "C:\Program Files\PostgreSQL\17\bin"
```

El script no lee `.env`, inicia un servidor limitado a 127.0.0.1 con un puerto
temporal, prueba migraciones y persistencia y lo detiene al terminar.

Prototipo educativo del TFM y futuro SaaS de ORQENTIVA Technologies.

## Qué funciona hoy
- FastAPI con OpenAPI interactivo (`/docs`).
- Dos negocios independientes (Alfa y Beta), datos iniciales y catálogo de servicios.
- Reservas con bloqueo de mismo horario dentro de cada negocio.
- Aislamiento por empresa en las consultas.
- Pruebas automatizadas.

> SPEC-007 sustituye las claves demo por cuentas y sesiones revocables. La publicación pública sigue pendiente de configuración HTTPS, revisión del proxy y límites de uso. Ver [Autenticación](docs/AUTENTICACION.md).

## Cómo ejecutarlo (Windows PowerShell)
```powershell
cd orqentiva-ai-v0
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En una base nueva de desarrollo configurada para este proyecto, preparar explícitamente
el esquema y los datos demo antes de iniciar la API:

```powershell
python -m alembic upgrade head
python seed.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```
Abrir http://127.0.0.1:8001/docs

Para probar recursos privados, crea una cuenta e inicia sesión siguiendo [Autenticación](docs/AUTENTICACION.md). Las antiguas claves `X-API-Key` ya no conceden acceso.

## Tests
```powershell
python -m pytest -q
```

## Acceso y siguiente incremento

Ver [Autenticación](docs/AUTENTICACION.md) para migrar explícitamente la base de
desarrollo, crear cuentas sin exponer contraseñas y configurar el origen local.
La página corporativa, servicios comerciales ES/EN y POST /leads siguen públicos.

El acceso de Super Admin incluye gestión de negocios, estado y creación de cuentas.
Ver [Panel administrativo](docs/PANEL_ADMINISTRADOR.md). El panel de cliente, LangGraph y RAG están pendientes; consultar [Alcance del MVP del TFM](docs/MVP_TFM.md).

Las lecciones anteriores que usen claves demo describen versiones históricas.
El contrato actual de autenticación es SPEC-007.
