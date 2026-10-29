# ORQENTIVA AI — Sprint 01

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
