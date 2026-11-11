"""Authenticated Meta webhook; persist first and process with a separate worker."""
import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Business, WhatsAppMessage
from app.deps import Database
from app.services.whatsapp import setting

router = APIRouter(prefix="/integrations/whatsapp", tags=["whatsapp"])


@router.get("/webhook", response_class=PlainTextResponse)
def verify(request: Request):
    token = setting("VERIFY_TOKEN")
    if request.query_params.get("hub.mode") != "subscribe" or not hmac.compare_digest(
        request.query_params.get("hub.verify_token", ""), token
    ):
        raise HTTPException(403, "Verificación inválida")
    return request.query_params.get("hub.challenge", "")


@router.post("/webhook")
async def receive(request: Request, session: Database):
    secret = setting("APP_SECRET")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 1_000_000:
            raise HTTPException(413, "Evento demasiado grande")
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, request.headers.get("x-hub-signature-256", "")):
        raise HTTPException(403, "Firma inválida")
    try:
        event = json.loads(body)
        mapping = json.loads(setting("PHONE_BUSINESSES"))
        if event.get("object") != "whatsapp_business_account":
            return {"status": "ignored"}
        for entry in event.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue
                value = change.get("value", {})
                phone = value.get("metadata", {}).get("phone_number_id")
                business = mapping.get(phone)
                if not business or session.get(Business, business) is None:
                    continue
                for message in value.get("messages", []):
                    mid, sender = message["id"], message["from"]
                    if not isinstance(mid, str) or not isinstance(sender, str) or len(mid) > 256 or len(sender) > 128:
                        raise ValueError()
                    stamp = datetime.fromtimestamp(int(message["timestamp"]), timezone.utc)
                    content = message.get("text", {}).get("body", "") if message.get("type") == "text" else ""
                    if not isinstance(content, str):
                        raise ValueError()
                    if session.scalar(select(WhatsAppMessage.id).where(WhatsAppMessage.message_id == mid)):
                        continue
                    try:
                        with session.begin_nested():
                            session.add(WhatsAppMessage(message_id=mid, business_id=business, phone_id=phone,
                                sender=sender, body=content[:351], received_at=stamp, sent=False))
                            session.flush()
                    except IntegrityError:
                        # A concurrent delivery of the same Meta message already persisted it.
                        if not session.scalar(select(WhatsAppMessage.id).where(WhatsAppMessage.message_id == mid)):
                            raise
        session.commit()
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
        session.rollback()
        raise HTTPException(400, "Evento inválido") from None
    return {"status": "accepted"}
