"""API multiempresa de ORQENTIVA Technologies con sesiones revocables."""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.routes.admin import router as admin_router
from app.routes.appointments import router as appointments_router
from app.routes.auth import router as auth_router
from app.routes.booking_chat import router as booking_chat_router
from app.routes.client import router as client_router
from app.routes.knowledge import router as knowledge_router
from app.routes.leads import router as leads_router
from app.routes.public_booking import router as public_booking_router
from app.routes.team import router as team_router
from app.routes.whatsapp import router as whatsapp_router

app = FastAPI(title="ORQENTIVA Technologies", version="0.2.0", description="API educativa multiempresa")

for router in (leads_router, auth_router, admin_router, client_router, team_router, public_booking_router,
               booking_chat_router, knowledge_router, whatsapp_router, appointments_router):
    app.include_router(router)

PRIVATE_PREFIXES = ("/auth/", "/admin/", "/client/", "/book/")


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    if request.url.path == "/leads" or request.url.path.startswith(PRIVATE_PREFIXES):
        return JSONResponse(status_code=422, content={"detail": "Datos inválidos"})
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Servicio temporalmente no disponible"})


@app.middleware("http")
async def private_cache_policy(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(PRIVATE_PREFIXES + ("/business/", "/services", "/appointments")):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    return {"status": "ok", "project": "ORQENTIVA Technologies", "version": app.version}


# Despliegue en un solo servicio: si existe la compilación del frontend, FastAPI la sirve
# en el mismo origen que la API. En desarrollo Vite sirve la interfaz y esto no se activa.
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).resolve().parents[1] / "frontend" / "dist"))
if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    API_ROOTS = {"leads", "auth", "admin", "client", "book", "business", "services", "appointments",
                 "integrations", "health", "docs", "redoc", "openapi.json"}

    @app.get("/{name}", include_in_schema=False)
    def frontend_file(name: str):
        if name in API_ROOTS:
            raise HTTPException(404, "No encontrado")
        candidate = (FRONTEND_DIST / name).resolve()
        if candidate.parent == FRONTEND_DIST.resolve() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
