"""Configuración del canal WhatsApp, compartida por el webhook y el worker."""
import os

from fastapi import HTTPException


def setting(name):
    value = os.getenv("WHATSAPP_" + name, "")
    if not value:
        raise HTTPException(503, "Canal WhatsApp sin configurar")
    return value
