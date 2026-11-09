import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import func, select

from app.models import Appointment, KnowledgeDocument, WhatsAppConversation, WhatsAppMessage
from app.scheduling import LOCAL
from app.whatsapp_worker import deliver_next, process_next

OWNER = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}


@pytest.fixture
def wa(monkeypatch):
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "test-secret")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify")
    monkeypatch.setenv("WHATSAPP_PHONE_BUSINESSES", '{"123":"alfa","456":"beta"}')
    monkeypatch.setenv("WHATSAPP_API_VERSION", "v99.0")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "test-only")


def incoming(client, mid, body, phone="123", sender="50600000000", age=0, valid=True):
    payload = {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {
        "metadata": {"phone_number_id": phone}, "messages": [{"id": mid, "from": sender,
        "timestamp": str(int(datetime.now(timezone.utc).timestamp()) - age), "type": "text", "text": {"body": body}}]}}]}]}
    data = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(b"test-secret", data, hashlib.sha256).hexdigest() if valid else "invalid"
    return client.post("/integrations/whatsapp/webhook", content=data, headers={"x-hub-signature-256": signature})


def prepare(client):
    service = client.post("/client/services", headers=OWNER,
        json={"name": "Corte recto", "duration_minutes": 30, "price_crc": 5000}).json()
    days = [{"weekday": i, "is_closed": False, "opens_at": "09:00", "closes_at": "13:00"} for i in range(7)]
    client.put("/client/hours", headers=OWNER, json={"days": days}).raise_for_status()
    client.post("/client/team", headers=OWNER, json={"name": "Ana", "days": days, "service_ids": [service["id"]]}).raise_for_status()
    return (datetime.now(LOCAL) + timedelta(days=7)).date().isoformat()


def turn(client, factory, mid, body, **kwargs):
    incoming(client, mid, body, **kwargs).raise_for_status()
    assert process_next(factory)
    while deliver_next(factory, post=accepted):
        pass
    with factory() as session:
        return session.scalar(select(WhatsAppMessage).where(WhatsAppMessage.message_id == mid)).reply


def accepted(url, **kwargs):
    return httpx.Response(200, json={"messages": [{"id": "outbound"}]}, request=httpx.Request("POST", url))


def test_verify_and_reject_forged_events(client, wa, session_factory):
    path = "/integrations/whatsapp/webhook"
    assert client.get(path, params={"hub.mode": "subscribe", "hub.verify_token": "test-verify", "hub.challenge": "123"}).text == "123"
    assert client.get(path, params={"hub.mode": "subscribe", "hub.verify_token": "wrong"}).status_code == 403
    assert incoming(client, "bad", "hola", valid=False).status_code == 403
    incoming(client, "unknown", "hola", phone="999").raise_for_status()
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(WhatsAppMessage)) == 0


def test_booking_persists_and_duplicate_confirmations_do_not_duplicate(client, wa, session_factory):
    day = prepare(client)
    assert "nombre" in turn(client, session_factory, "one", f"Corte con Ana el {day} a las 10")
    assert "CONFIRMO" in turn(client, session_factory, "two", "Pedro")
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Appointment)) == 0
    assert "registrada" in turn(client, session_factory, "three", "confirmo")
    incoming(client, "three", "confirmo").raise_for_status()
    assert not process_next(session_factory)
    assert "No hay" in turn(client, session_factory, "four", "confirmo")
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Appointment)) == 1
    # WhatsApp no pregunta el contacto: guarda el número del remitente.
    [booking] = client.get("/client/dashboard", headers=OWNER).json()["appointments"]
    assert booking["customer_contact"] == "+50600000000"


def test_knowledge_preserves_draft_and_isolates_business(client, wa, session_factory):
    day = prepare(client)
    with session_factory.begin() as session:
        session.add(KnowledgeDocument(business_id="alfa", title="Cancelaciones", body="Cancelaciones con 24 horas de anticipación.", published=True))
    turn(client, session_factory, "a", f"Corte con Ana el {day} a las 10")
    answer = turn(client, session_factory, "b", "¿Cuál es la política de cancelaciones?")
    assert "24 horas" in answer and "Fuente:" in answer
    assert "24 horas" not in turn(client, session_factory, "c", "¿Cuál es la política de cancelaciones?", phone="456")
    assert "CONFIRMO" in turn(client, session_factory, "d", "Pedro")


def test_delivery_failure_keeps_reply_and_booking_for_retry(client, wa, session_factory):
    prepare(client)
    incoming(client, "out", "hola").raise_for_status()
    assert process_next(session_factory)
    calls = []
    def failure(*args, **kwargs):
        raise httpx.ConnectError("offline")
    with pytest.raises(httpx.ConnectError):
        deliver_next(session_factory, post=failure)
    def success(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json={"messages": [{"id": "outbound"}]}, request=httpx.Request("POST", url))
    assert deliver_next(session_factory, post=success)
    assert not deliver_next(session_factory, post=success)
    assert len(calls) == 1 and calls[0][1]["json"]["to"] == "50600000000"


def test_expired_messages_never_book_or_send(client, wa, session_factory):
    incoming(client, "old", "confirmo", age=86401).raise_for_status()
    assert process_next(session_factory)
    assert not deliver_next(session_factory, post=lambda *a, **k: pytest.fail("No network allowed"))
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Appointment)) == 0


def test_conflict_requires_new_proposal(client, wa, session_factory):
    day = prepare(client)
    for sender in ("111", "222"):
        turn(client, session_factory, sender + "a", f"Corte con Ana el {day} a las 10", sender=sender)
        turn(client, session_factory, sender + "b", "Pedro", sender=sender)
    turn(client, session_factory, "c1", "confirmo", sender="111")
    assert "ya no está disponible" in turn(client, session_factory, "c2", "confirmo", sender="222")
    assert "No hay" in turn(client, session_factory, "c3", "confirmo", sender="222")
    assert "CONFIRMO" in turn(client, session_factory, "c4", "10:30", sender="222")
    assert "registrada" in turn(client, session_factory, "c5", "confirmo", sender="222")


def test_reset_and_pause_do_not_cancel_existing_appointments(client, wa, session_factory):
    prepare(client)
    assert "pausado" in turn(client, session_factory, "h1", "humano")
    assert "pausado" in turn(client, session_factory, "h2", "corte")
    assert "Borrador descartado" in turn(client, session_factory, "h3", "reiniciar")
    with session_factory() as session:
        assert session.get(WhatsAppConversation, ("alfa", "50600000000")).state == {}


def test_unconfigured_webhook_is_disabled(client, monkeypatch):
    monkeypatch.delenv("WHATSAPP_APP_SECRET", raising=False)
    assert client.post("/integrations/whatsapp/webhook", json={}).status_code == 503


def test_confirmation_waits_for_summary_to_be_sent(client, wa, session_factory):
    day = prepare(client)
    turn(client, session_factory, "s1", f"Corte con Ana el {day} a las 10")
    incoming(client, "s2", "Pedro").raise_for_status()
    assert process_next(session_factory)
    incoming(client, "s3", "confirmo").raise_for_status()
    assert process_next(session_factory)
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Appointment)) == 0
        assert "pendiente de envío" in session.scalar(select(WhatsAppMessage).where(WhatsAppMessage.message_id == "s3")).reply
    while deliver_next(session_factory, post=accepted):
        pass
    assert "registrada" in turn(client, session_factory, "s4", "confirmo")


def test_out_of_order_message_does_not_replace_draft(client, wa, session_factory):
    day = prepare(client)
    turn(client, session_factory, "o1", f"Corte con Ana el {day} a las 10")
    reply = turn(client, session_factory, "o2", "reiniciar", age=60)
    assert "fuera de orden" in reply
    assert "CONFIRMO" in turn(client, session_factory, "o3", "Pedro")
