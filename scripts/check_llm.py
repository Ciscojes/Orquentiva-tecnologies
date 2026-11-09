"""Comprueba la configuración del LLM sin arrancar la API: python scripts/check_llm.py"""
import logging
import os

import httpx
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.basicConfig(level=logging.INFO, format="%(message)s")

from app import llm  # noqa: E402
from app.scheduling import LOCAL  # noqa: E402

MENU = {"services": [{"id": 1, "name": "Corte demo"}], "team": [{"id": 1, "name": "Ana"}]}
MESSAGE = "me urge un recorte pasado mañana a las diez y media con Ana"

if not llm.enabled():
    raise SystemExit("Faltan LLM_API_KEY o LLM_MODEL en esta terminal.")
print(f"Proveedor: {os.getenv('LLM_BASE_URL', llm.DEFAULT_BASE_URL)} · modelo: {os.environ['LLM_MODEL']}")
print(f"Mensaje de prueba: {MESSAGE}")
result = llm.extract(MESSAGE, MENU, datetime.now(LOCAL).date(), "es")
print("Resultado:", result or "vacío (revisa el aviso de arriba)")

if result:
    print("\nPrueba de RAG")
    paragraphs = [{"id": "p1", "title": "Cancelaciones", "paragraph": 1, "quote": "Para cancelar, avisa con 24 horas de anticipación."},
                  {"id": "p2", "title": "Pagos", "paragraph": 1, "quote": "Aceptamos efectivo y tarjeta."}]
    question = "Si al final no puedo ir, ¿qué tengo que hacer?"
    print(f"Pregunta: {question}")
    print("Respuesta:", llm.answer_from_sources(question, paragraphs, "es") or "rechazada o vacía (revisa el aviso de arriba)")

if not result:
    # Lista los modelos que tu clave puede usar, para elegir un LLM_MODEL válido.
    base = os.getenv("LLM_BASE_URL", llm.DEFAULT_BASE_URL).rstrip("/")
    try:
        response = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"}, timeout=10)
        response.raise_for_status()
        names = sorted(m["id"] for m in response.json().get("data", []))
        print("Modelos disponibles para tu clave:")
        for name in names:
            print("  -", name)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        print("No se pudo listar los modelos:", type(exc).__name__)
