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


# --- Prioridad entre reglas y LLM (fecha fija: martes 10 de noviembre de 2026) ---

CATALOG = {"services": [{"id": 1, "name": "Corte"}, {"id": 2, "name": "Corte y barba"}, {"id": 3, "name": "Tinte de cabello"}],
           "team": [{"id": 7, "name": "Ana", "service_ids": [1, 2, 3]}]}


def merged(message, hints):
    """Borrador tras aplicar las reglas a un mensaje con una propuesta del LLM ya validada."""
    from datetime import date
    from app.services.chat import Turn, interpret
    state = {"turn": Turn(message=message), "menu": CATALOG, "hints": hints, "today": date(2026, 11, 10)}
    return interpret(state)["draft"]


def test_unambiguous_rules_beat_the_llm():
    from datetime import date
    draft = merged("mañana a las 10", {"day": date(2026, 11, 20), "clock": "12:00"})
    assert (draft.day, draft.clock) == (date(2026, 11, 11), "10:00")
    assert merged("hoy a las 3 pm", {"day": date(2026, 11, 12), "clock": "03:00"}).clock == "15:00"


def test_llm_may_move_the_week_but_not_the_weekday():
    from datetime import date
    # "viernes 20": las reglas solo ven "viernes" (13); el LLM lee el número y sigue siendo viernes.
    assert merged("el viernes 20", {"day": date(2026, 11, 20)}).day == date(2026, 11, 20)
    # Un jueves, o un viernes pasado, contradice el día nombrado: mandan las reglas.
    assert merged("el viernes", {"day": date(2026, 11, 19)}).day == date(2026, 11, 13)
    assert merged("el viernes", {"day": date(2026, 11, 6)}).day == date(2026, 11, 13)
    assert merged("el viernes", {}).day == date(2026, 11, 13)
    # Hoy es martes: "el martes" es el siguiente, aunque el LLM proponga hoy.
    assert merged("el martes", {"day": date(2026, 11, 10)}).day == date(2026, 11, 17)
    assert merged("dentro de dos semanas, el martes", {"day": date(2026, 11, 24)}).day == date(2026, 11, 24)


def test_next_week_accepts_only_llm_days_inside_that_week():
    from datetime import date
    message = "la semana que viene a media mañana"
    assert merged(message, {"day": date(2026, 11, 18), "clock": "10:00"}).day == date(2026, 11, 18)
    assert merged(message, {"day": date(2026, 11, 18), "clock": "10:00"}).clock == "10:00"
    assert merged(message, {"day": date(2026, 11, 11)}).day is None
    assert merged(message, {"day": date(2026, 11, 25)}).day is None
    assert merged(message, {}).day is None


def test_llm_only_resolves_morning_or_afternoon_for_a_doubtful_hour():
    assert merged("a las 4", {"clock": "16:00"}).clock == "16:00"
    assert merged("a las 4", {"clock": "17:00"}).clock == "04:00"
    assert merged("a las 4", {}).clock == "04:00"
    assert merged("a las 4 de la tarde", {"clock": "04:00"}).clock == "16:00"


def test_llm_decides_the_service_when_the_rule_match_is_partial():
    # Nombre completo y único: mandan las reglas.
    assert merged("quiero un tinte de cabello", {"service_id": 1}).service_id == 3
    # Solo coincide una palabra ("cabello"): decide el LLM si propone algo.
    assert merged("arreglarme el cabello", {"service_id": 1}).service_id == 1
    assert merged("arreglarme el cabello", {}).service_id == 3
    # "Corte" es exacto, pero el mensaje también apunta a "Corte y barba".
    assert merged("un corte con barba", {"service_id": 2, "professional_id": 7}).service_id == 2
    # "Corte" a secas es un nombre completo aunque otro servicio comparta la palabra.
    assert merged("un corte", {"service_id": 2}).service_id == 1


# --- Activación desde el archivo .env ---

def test_env_file_activates_the_llm(tmp_path, monkeypatch):
    for key in ("LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    env = tmp_path / ".env"
    env.write_text("POSTGRES_PASSWORD=secreta\nOTRA=1\nLLM_API_KEY=clave-de-prueba\nLLM_MODEL=modelo\n"
                   "LLM_BASE_URL=https://ejemplo.test/v1\n", encoding="utf-8")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    assert "LLM inactivo" in llm.status() and "LLM_API_KEY y LLM_MODEL" in llm.status()
    llm.load_env_file(env)
    assert llm.enabled()
    assert llm.status() == "LLM activo: modelo modelo en https://ejemplo.test/v1"
    assert "clave-de-prueba" not in llm.status()
    # Solo se copian las variables del LLM; la base de datos sigue con su propia configuración.
    import os
    assert "POSTGRES_PASSWORD" not in os.environ and "OTRA" not in os.environ
    for key in ("LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(key)


def test_terminal_takes_priority_over_env_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LLM_API_KEY=del-archivo\nLLM_MODEL=del-archivo\n", encoding="utf-8")
    monkeypatch.setenv("LLM_API_KEY", "de-la-terminal")
    monkeypatch.setenv("LLM_MODEL", "de-la-terminal")
    llm.load_env_file(env)
    import os
    assert os.environ["LLM_MODEL"] == "de-la-terminal"


def test_env_file_without_key_or_missing_keeps_rules_only(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_MODEL", "modelo")
    env = tmp_path / ".env"
    env.write_text("LLM_API_KEY=\n", encoding="utf-8")
    llm.load_env_file(env)
    llm.load_env_file(tmp_path / "no-existe.env")
    assert not llm.enabled()
    assert llm.status() == "LLM inactivo: el chat usa solo reglas (falta LLM_API_KEY en el archivo .env)"


def test_startup_reports_llm_status(client, llm_on, caplog):
    import logging
    from fastapi.testclient import TestClient
    from app.main import app
    with caplog.at_level(logging.INFO, logger=llm.logger.name), TestClient(app):
        pass
    assert "LLM activo: modelo test-model" in caplog.text
