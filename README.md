# ORQENTIVA AI — Sprint 04

## Captación de leads

`POST /leads` acepta nombre, correo, empresa opcional, servicio y mensaje.
Los servicios permitidos son `agents`, `automation`, `growth` y `saas`.
No requiere claves de las empresas ni ofrece listado público.
Devuelve HTTP 201 al guardar; 422 ante datos inválidos; 429 ante exceso de envíos;
503 si no puede guardar. El formulario React permite enviar en español e inglés.

Para el desarrollo, ejecutar la API en `127.0.0.1:8000` y, desde `frontend`,
`npm install` y `npm run dev`. Vite reenvía `/leads` a la API.
En producción debe configurarse una ruta del mismo origen hacia el backend;
`vite preview` no sustituye esa configuración.

La conexión PostgreSQL usa la configuración local existente y `POSTGRES_PASSWORD`
en `.env`. `DATABASE_URL` permite seleccionar explícitamente otra base de datos.
No colocar credenciales en React ni registrar estas variables.
Los tests fuerzan bases SQLite temporales y no necesitan `.env`.

Estado de la transición: `/business/me` y `/leads` usan SQLAlchemy/PostgreSQL;
`/services` y `/appointments` conservan SQLite de demostración.
El arranque todavía inicializa los datos demo en SQLite. No asumir una migración completa.
El límite de leads es básico, en memoria y por proceso (5 envíos/IP/minuto).
Para varias instancias se necesita un contador compartido y proxies de confianza configurados.

Ver `docs/AUDITORIA_SPRINT_04.md` y `specs/004-lead-capture/task.md`.

Las nuevas reservas se guardan con fecha UTC. Las reservas anteriores conservan
su representación y se comparan por instante para impedir duplicados, incluso
cuando dos solicitudes llegan simultáneamente con distintas zonas horarias.
El listado se ordena por instante y los nombres se validan después de quitar espacios.

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

> Seguridad: las API keys incluidas son **solo ejemplos**, están en el código para simplificar el aprendizaje. **NO exponer este servidor a Internet**. Falta autenticación real, autorización por roles, cifrado y auditoría. SQLite se usa como etapa de aprendizaje; producción irá sobre PostgreSQL.

## Cómo ejecutarlo (Windows PowerShell)
```powershell
cd orqentiva-ai-v0
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Abrir http://127.0.0.1:8000/docs

Para probar `/services`, en el encabezado `X-API-Key` utiliza `demo-barberia-alfa` o `demo-barberia-beta`. La documentación interactiva solicita el encabezado al probar los endpoints.

## Tests
```powershell
python -m pytest -q
```

## Primer experimento
1. Ejecuta `GET /services` con `demo-barberia-alfa`.
2. Repite con `demo-barberia-beta`.
3. Crea una cita usando `POST /appointments` con el cuerpo:
```json
{"customer_name":"Ana Demo","starts_at":"2030-11-02T15:00:00-06:00"}
```
4. Consulta `GET /appointments` con cada clave y explica por qué no ven los mismos datos.
5. Repite la reserva a la misma hora y observa el error HTTP 409.

Consulta `docs/LECCION_01.md` y `docs/PROJECT_CHARTER.md`.
