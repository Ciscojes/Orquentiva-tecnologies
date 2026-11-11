"""Run one durable WhatsApp worker: python -m app.whatsapp_worker [--once]."""
import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import HTTPException
from sqlalchemy import select, text

from app.database import SessionLocal, engine
from app.models import WhatsAppConversation, WhatsAppMessage
from app import llm
from app.schemas import Confirmation
from app.services.agenda import confirm_booking, public_business
from app.services.chat import Draft, Turn, normalized, run_chat
from app.services.whatsapp import setting


def utc(stamp):
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp.astimezone(timezone.utc)


def advance(session, message):
    public_business(session, message.business_id, lock=True)
    key = (message.business_id, message.sender)
    conversation = session.get(WhatsAppConversation, key)
    if conversation is None:
        conversation = WhatsAppConversation(business_id=key[0], sender=key[1], state={}, updated_at=message.received_at)
        session.add(conversation)
    state = dict(conversation.state)
    if utc(message.received_at) < utc(conversation.updated_at):
        return "Llegó un mensaje anterior fuera de orden. Repite tu solicitud para continuar."
    if utc(message.received_at) - utc(conversation.updated_at) > timedelta(hours=24):
        state = {}
    conversation.updated_at = message.received_at
    raw = message.body.strip()
    value = normalized(raw).strip(" .!¡¿?")
    if not raw or len(raw) > 350:
        return "Por ahora atiendo mensajes de texto de hasta 350 caracteres. Escribe el servicio que deseas reservar."
    if value in {"reiniciar", "nueva reserva", "cancelar", "no"}:
        conversation.state = {}
        return "Borrador descartado; ninguna cita existente fue cancelada. Escribe el servicio para comenzar otra reserva."
    if value in {"humano", "persona", "asesor"}:
        state["paused"] = True
        conversation.state = state
        return "Asistente pausado. Contacta directamente al negocio para atención personal; este piloto no tiene bandeja de operadores. Escribe REINICIAR para volver."
    if state.get("paused"):
        return "El asistente está pausado. Escribe REINICIAR para volver a las reservas."
    draft = Draft.model_validate(state.get("draft", {}))
    if value in {"confirmo", "confirmar", "si"} and state.get("proposal"):
        proposal_message = session.scalar(select(WhatsAppMessage).where(
            WhatsAppMessage.message_id == state.get("proposal_message_id")))
        if proposal_message is None or not proposal_message.sent:
            return "El resumen todavía está pendiente de envío. Espera a recibirlo y después responde CONFIRMO."
        try:
            with session.begin_nested():
                # El número del remitente lo da Meta: se guarda tal cual, sin pedirlo al cliente.
                confirmation = Confirmation(**state["proposal"], request_key=state["request_key"])
                confirmation = confirmation.model_copy(update={"customer_contact": "+" + message.sender})
                booking = confirm_booking(confirmation,
                                          message.business_id, session, commit=False)
        except HTTPException as exc:
            if exc.status_code != 409:
                raise
            conversation.state = {"draft": draft.model_copy(update={"clock": None, "step": "time"}).model_dump(mode="json")}
            return "Ese turno ya no está disponible. Escribe otra hora para consultar y confirmar de nuevo."
        conversation.state = {}
        return f"Tu reserva quedó registrada. Referencia: {booking['id']}. Para otra cita escribe el servicio."
    if value in {"confirmo", "confirmar", "si"}:
        return "No hay una propuesta pendiente. Escribe el servicio para preparar tu reserva."
    # En WhatsApp el contacto es el número del remitente: no se pregunta.
    result = run_chat(message.business_id, Turn(message=raw, draft=draft), session, llm.enabled(), ask_contact=False)
    reply = result["reply"]
    if result.get("kind") == "knowledge":
        for source in result["sources"]:
            reply += f"\n\n{source['quote']}\nFuente: {source['title']}, párrafo {source['paragraph']}."
        conversation.state = state
        return reply[:4000]
    proposal = result["proposal"]
    conversation.state = {"draft": result["draft"].model_dump(mode="json"), "proposal": proposal,
                          "proposal_message_id": message.message_id if proposal else None,
                          "request_key": str(uuid4()) if proposal else None}
    if result["options"]:
        reply += "\nOpciones: " + ", ".join(result["options"][:20]) + ". Escribe la opción elegida."
    if proposal:
        reply += "\nResponde CONFIRMO para reservar o REINICIAR para empezar de nuevo."
    return reply[:4000]


def process_next(factory=SessionLocal):
    """Persist reply and booking in the same transaction before any network call."""
    with factory.begin() as session:
        message = session.scalar(select(WhatsAppMessage).where(WhatsAppMessage.reply.is_(None))
                                 .order_by(WhatsAppMessage.id).limit(1).with_for_update())
        if message is None:
            return False
        if datetime.now(timezone.utc) - utc(message.received_at) >= timedelta(hours=24):
            message.reply = "Evento vencido; no se procesó ni se envió respuesta."
            message.sent = True
            return True
        try:
            with session.begin_nested():
                message.reply = advance(session, message)
        except HTTPException as exc:
            if exc.status_code >= 500:
                raise
            message.reply = "No pude completar la solicitud. La agenda o el servicio no están disponibles; contacta al negocio."
        return True


def deliver_next(factory=SessionLocal, post=httpx.post):
    with factory.begin() as session:
        message = session.scalar(select(WhatsAppMessage).where(WhatsAppMessage.reply.is_not(None),
                                 WhatsAppMessage.sent.is_(False)).order_by(WhatsAppMessage.id).limit(1))
        if message is None:
            return False
        if datetime.now(timezone.utc) - utc(message.received_at) >= timedelta(hours=24):
            message.sent = True
            return True
        mapping = json.loads(setting("PHONE_BUSINESSES"))
        if mapping.get(message.phone_id) != message.business_id:
            raise RuntimeError("La asociación del número cambió; revisar la cola antes de enviar")
        version = setting("API_VERSION")
        if not re.fullmatch(r"v\d+\.\d+", version) or not message.phone_id.isdigit():
            raise RuntimeError("Configuración de WhatsApp inválida")
        response = post(f"https://graph.facebook.com/{version}/{message.phone_id}/messages",
                        headers={"Authorization": "Bearer " + setting("ACCESS_TOKEN")},
                        json={"messaging_product": "whatsapp", "to": message.sender, "type": "text",
                              "text": {"body": message.reply}}, timeout=15)
        response.raise_for_status()
        if not response.json().get("messages"):
            raise RuntimeError("Meta no confirmó la aceptación del mensaje")
        message.sent = True
        return True


@contextmanager
def worker_lock():
    """One worker per database: Postgres advisory lock or local SQLite file lock."""
    if engine.dialect.name == "postgresql":
        with engine.connect() as connection:
            if not connection.scalar(text("SELECT pg_try_advisory_lock(130013)")):
                raise RuntimeError("Ya hay un trabajador WhatsApp activo")
            try:
                yield
            finally:
                connection.execute(text("SELECT pg_advisory_unlock(130013)"))
    elif engine.dialect.name == "sqlite":
        identity = hashlib.sha256(str(Path(engine.url.database).resolve()).encode()).hexdigest()
        with open(Path(tempfile.gettempdir()) / ("orqentiva-wa-" + identity + ".lock"), "a+b") as handle:
            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
    else:
        raise RuntimeError("Base de datos no compatible")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Procesar y enviar como máximo un mensaje")
    args = parser.parse_args()
    with worker_lock():
        while True:
            try:
                processed = process_next()
                delivered = deliver_next()
            except Exception:
                # Do not print customer messages, access tokens, or provider response bodies.
                print("WhatsApp: operación pendiente; revisar configuración/conectividad. No se borró la cola.", flush=True)
                if args.once:
                    raise SystemExit(1) from None
                time.sleep(10)
                continue
            if args.once:
                break
            if not processed and not delivered:
                time.sleep(1)


if __name__ == "__main__":
    main()
