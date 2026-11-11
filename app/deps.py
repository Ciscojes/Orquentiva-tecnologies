"""Dependencias de FastAPI que comparten las rutas."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import current_business
from app.database import get_db

Tenant = Annotated[str, Depends(current_business)]
Database = Annotated[Session, Depends(get_db)]
