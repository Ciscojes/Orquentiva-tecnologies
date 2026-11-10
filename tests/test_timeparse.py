"""Reglas de día y hora con una fecha fija: martes 10 de noviembre de 2026."""
from datetime import date, datetime, timedelta

import pytest

from app.scheduling import LOCAL
from app.routes.booking_chat import normalized
from app.timeparse import find_clock, find_day

TODAY = date(2026, 11, 10)
OWNER = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}


def day(message):
    return find_day(normalized(message), TODAY)


@pytest.mark.parametrize("message, expected", [
    ("mañana", date(2026, 11, 11)),
    ("mañana a las 10", date(2026, 11, 11)),
    ("mañana por la mañana", date(2026, 11, 11)),
    ("pasado mañana por la mañana", date(2026, 11, 12)),
    ("hoy por la tarde", TODAY),
    ("tomorrow morning", date(2026, 11, 11)),
    ("el 2026-12-01 por la mañana", date(2026, 12, 1)),
    # Regresión: la franja del día no es "el día siguiente".
    ("por la mañana", None),
    ("a media mañana", None),
    ("a las 10 de la mañana", None),
    ("esta mañana", None),
    ("en las mañanas", None),
    ("el viernes por la mañana", date(2026, 11, 13)),
    ("el sábado a media mañana", date(2026, 11, 14)),
    # Regresión: el mismo día de la semana que hoy es el de la semana siguiente.
    ("el martes", date(2026, 11, 17)),
    ("on tuesday", date(2026, 11, 17)),
    ("el miércoles", date(2026, 11, 11)),
    ("el lunes", date(2026, 11, 16)),
    # "La semana que viene": con día concreto, ese día de la semana siguiente; sin día, se pregunta.
    ("el viernes de la semana que viene", date(2026, 11, 20)),
    ("la próxima semana el lunes", date(2026, 11, 16)),
    ("next week on wednesday", date(2026, 11, 18)),
    ("la otra semana, el martes", date(2026, 11, 17)),
    ("la semana que viene a media mañana con la chica de siempre", None),
    ("el viernes que viene", date(2026, 11, 13)),
    ("quiero un corte", None),
])
def test_day_rules(message, expected):
    assert day(message).value == expected


def test_next_week_without_day_is_reported_so_the_chat_asks():
    found = day("la semana que viene a media mañana")
    assert found.value is None and found.next_week and found.mentioned
    assert not day("a media mañana").mentioned


def test_only_unambiguous_days_are_sure():
    assert day("mañana").sure and day("hoy").sure and day("2026-12-01").sure
    assert not day("el viernes").sure and day("el viernes").weekday == 4


def test_invalid_iso_date_is_rejected():
    with pytest.raises(ValueError):
        day("el 2026-02-30")


@pytest.mark.parametrize("message, expected, sure", [
    ("a las 10", "10:00", True),
    ("a las 10:30", "10:30", True),
    ("10:30", "10:30", True),
    ("at 3pm", "15:00", True),
    ("a las 4 p.m.", "16:00", True),
    ("a las 9 am", "09:00", True),
    ("a las 12 am", "00:00", True),
    ("a las 4 de la tarde", "16:00", True),
    ("a las 8 de la noche", "20:00", True),
    ("a las 10 de la mañana", "10:00", True),
    ("at 4 in the afternoon", "16:00", True),
    ("a la 1 de la tarde", "13:00", True),
    ("a las 15", "15:00", True),
    # Sin "am/pm" ni franja, una hora de 1 a 7 queda marcada como dudosa.
    ("a las 4", "04:00", False),
    ("a las 25", None, False),
    ("por la mañana", None, False),
])
def test_clock_rules(message, expected, sure):
    found = find_clock(normalized(message))
    assert (found.value, found.sure) == (expected, sure)


def test_doubtful_hour_offers_the_afternoon_alternative():
    assert find_clock("a las 4").alternative == "16:00"
    assert find_clock("a las 4:30").alternative == "16:30"
    assert find_clock("a las 10").alternative is None


def test_chat_keeps_the_named_weekday_when_the_message_says_morning(client, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    service = client.post("/client/services", headers=OWNER,
                          json={"name": "Corte recto", "duration_minutes": 30, "price_crc": 5000}).json()
    days = [{"weekday": i, "is_closed": False, "opens_at": "09:00", "closes_at": "13:00"} for i in range(7)]
    client.put("/client/hours", headers=OWNER, json={"days": days}).raise_for_status()
    client.post("/client/team", headers=OWNER, json={"name": "Ana", "days": days, "service_ids": [service["id"]]})
    today = datetime.now(LOCAL).date()
    friday = today + timedelta(days=(4 - today.weekday()) % 7 or 7)

    reply = client.post("/book/alfa/chat", json={"message": "Quiero un corte con Ana el viernes por la mañana"}).json()
    assert reply["draft"]["day"] == friday.isoformat() and reply["draft"]["step"] == "time"

    reply = client.post("/book/alfa/chat", json={"message": "Quiero un corte con Ana a las 10 de la mañana"}).json()
    assert reply["draft"]["day"] is None and reply["draft"]["step"] == "day"
    assert reply["draft"]["clock"] == "10:00"

    # "La semana que viene" sin día concreto descarta el día anterior y vuelve a preguntarlo.
    reply = client.post("/book/alfa/chat", json={"message": "mejor la semana que viene", "draft": reply["draft"] | {"day": today.isoformat()}}).json()
    assert reply["draft"]["day"] is None and reply["draft"]["step"] == "day"
