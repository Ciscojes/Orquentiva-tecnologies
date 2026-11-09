"""Contacto del cliente: teléfono o correo, normalizado para guardarlo y mostrarlo."""
import re

from email_validator import EmailNotValidError, validate_email


def normalize_contact(value: str) -> str:
    """Devuelve el correo en minúsculas o el teléfono como +dígitos; ValueError si no es válido."""
    text = value.strip()
    if "@" in text:
        try:
            return validate_email(text, check_deliverability=False).normalized.lower()
        except EmailNotValidError:
            raise ValueError("Correo no válido") from None
    if not re.fullmatch(r"\+?[\d\s().-]+", text):
        raise ValueError("Escribe un teléfono o un correo")
    digits = re.sub(r"\D", "", text)
    if not 7 <= len(digits) <= 15:
        raise ValueError("El teléfono debe tener entre 7 y 15 dígitos")
    return ("+" if text.startswith("+") else "") + digits
