"""Interpretación opcional con LLM: el modelo se simula, nunca se llama a la red."""
import json
from datetime import datetime, timedelta

import httpx
import pytest

from app import llm
from app.routes.booking_chat import llm_limiter
from app.scheduling import LOCAL

OWNER = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}
MENU = {"services": [{"id": 1, "name": "Corte recto"}], "team": [{"id": 7, "name": "Ana"}]}


@pytest.fixture
def llm_on(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-only")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    llm_limiter.buckets.clear()


def setup_agenda(client):
    service = client.post("/client/services", headers=OWNER,
                          json={"name": "Corte recto", "duration_minutes": 30, "price_crc": 5000}).json()
    days = [{"weekday": i, "is_closed": False, "opens_at": "09:00", "closes_at": "13:00"} for i in range(7)]
    client.put("/client/hours", headers=OWNER, json={"days": days}).raise_for_status()
    ana = client.post("/client/team", headers=OWNER, json={"name": "Ana", "days": days, "service_ids": [service["id"]]}).json()
    return service, ana


def test_disabled_without_configuration(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert not llm.enabled()
    assert llm.extract("Quiero un corte", MENU, datetime.now(LOCAL).date(), "es") == {}


def test_validate_discards_invented_or_invalid_fields():
    today = datetime.now(LOCAL).date()
    data = {"service_id": 99, "professional_id": 7, "day": (today - timedelta(days=1)).isoformat(),
            "clock": "25:00", "name": "Robert'); DROP TABLE"}
    assert llm.validate(data, MENU, today) == {"professional_id": 7}
    assert llm.validate({"service_id": "uno"}, MENU, today) == {}


def test_model_failure_falls_back_to_rules(llm_on, monkeypatch):
    def broken(payload):
        raise httpx.ConnectError("sin red")
    monkeypatch.setattr(llm, "call_model", broken)
    assert llm.extract("Quiero un corte", MENU, datetime.now(LOCAL).date(), "es") == {}
    monkeypatch.setattr(llm, "call_model", lambda payload: "esto no es JSON")
    assert llm.extract("Quiero un corte", MENU, datetime.now(LOCAL).date(), "es") == {}


def test_llm_understands_free_language(client, llm_on, monkeypatch):
    service, ana = setup_agenda(client)
    day = (datetime.now(LOCAL) + timedelta(days=7)).date()
    seen = {}

    def fake_model(payload):
        seen["payload"] = payload
        return "```json\n" + json.dumps({"service_id": service["id"], "professional_id": ana["id"],
                                         "day": day.isoformat(), "clock": "10:00", "name": None}) + "\n```"
    monkeypatch.setattr(llm, "call_model", fake_model)
    # Las reglas no reconocen esta frase: sin LLM pediría el servicio.
    reply = client.post("/book/alfa/chat", json={"message": "me urge un recorte la semana que viene a media mañana, que me atienda la chica de siempre"}).json()
    assert reply["draft"]["service_id"] == service["id"]
    assert reply["draft"]["professional_id"] == ana["id"]
    assert reply["draft"]["step"] == "name" and reply["proposal"] is None
    context = json.loads(seen["payload"]["messages"][1]["content"])
    assert context["services"] == [{"id": service["id"], "name": "Corte recto"}]
    # El LLM no puede confirmar: la reserva sigue necesitando propuesta y confirmación.
    assert not client.get("/client/dashboard", headers=OWNER).json()["appointments"]


def test_rules_take_priority_over_llm(client, llm_on, monkeypatch):
    service, ana = setup_agenda(client)
    day = (datetime.now(LOCAL) + timedelta(days=7)).date()
    monkeypatch.setattr(llm, "call_model", lambda payload: json.dumps({"clock": "12:00"}))
    reply = client.post("/book/alfa/chat", json={"message": f"Quiero un corte con Ana el {day} a las 10"}).json()
    assert reply["draft"]["clock"] == "10:00"


def test_llm_rate_limit_keeps_chat_working(client, llm_on, monkeypatch):
    setup_agenda(client)
    calls = []
    monkeypatch.setattr(llm, "call_model", lambda payload: calls.append(1) or "{}")
    for _ in range(25):
        assert client.post("/book/alfa/chat", json={"message": "hola"}).status_code == 200
    assert len(calls) == 20


def test_provider_error_is_logged_without_key(llm_on, monkeypatch, caplog):
    request = httpx.Request("POST", "https://example.test/chat/completions")
    response = httpx.Response(401, request=request, text='{"error":"Invalid API Key"}')
    def rejected(payload):
        raise httpx.HTTPStatusError("401", request=request, response=response)
    monkeypatch.setattr(llm, "call_model", rejected)
    with caplog.at_level("WARNING", logger="uvicorn.error.llm"):
        assert llm.extract("Quiero un corte", MENU, datetime.now(LOCAL).date(), "es") == {}
    assert "401" in caplog.text and "Invalid API Key" in caplog.text and "test-only" not in caplog.text


def test_prompt_includes_weekday_for_relative_dates(llm_on, monkeypatch):
    seen = {}
    monkeypatch.setattr(llm, "call_model", lambda payload: seen.setdefault("p", payload) and "{}")
    llm.extract("pasado mañana", MENU, datetime.now(LOCAL).date(), "es")
    context = json.loads(seen["p"]["messages"][1]["content"])
    assert context["today_weekday"] in llm.WEEKDAYS


def test_rules_understand_day_after_tomorrow(client, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    setup_agenda(client)
    reply = client.post("/book/alfa/chat", json={"message": "Quiero un corte con Ana pasado mañana"}).json()
    expected = (datetime.now(LOCAL) + timedelta(days=2)).date().isoformat()
    assert reply["draft"]["day"] == expected
