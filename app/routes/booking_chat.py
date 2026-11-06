"""Conversación guiada; el grafo consulta la agenda, sin efectuar escrituras."""
import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Literal, TypedDict
from fastapi import APIRouter
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langsmith import tracing_context
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.routes.client import Database
from app.routes.public_booking import catalog
from app.routes.team import available
from app.scheduling import LOCAL

router = APIRouter(prefix="/book/{business_id}", tags=["chat"])


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_id: int | None = None
    professional_id: int | None = None
    day: date | None = None
    clock: str | None = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    name: str = Field("", max_length=100)
    step: Literal["request","service","professional","day","time","name","review"] = "request"


class Turn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(max_length=350)
    language: Literal["es","en"] = "es"
    draft: Draft = Field(default_factory=Draft)


class State(TypedDict, total=False):
    turn: Turn
    business: str
    menu: dict
    draft: Draft
    reply: str
    options: list[str]
    proposal: dict | None


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if not unicodedata.combining(c))


def has(text, phrase):
    return re.search(r"(?<!\w)" + re.escape(normalized(phrase)) + r"(?!\w)", text) is not None


def respond(draft, step, reply, options=(), proposal=None):
    return {"draft": draft.model_copy(update={"step":step}), "reply":reply,
            "options":list(options), "proposal":proposal}


def interpret(state: State):
    turn, menu = state["turn"], state["menu"]
    d = turn.draft.model_copy()
    raw = turn.message.strip()
    text = normalized(raw)
    es = turn.language == "es"
    if d.step == "name" and raw:
        name = re.sub(r"^(?:me llamo|soy|mi nombre es|my name is|i am|i'm)\s+", "", raw, flags=re.I).strip(" .")
        if 1 <= len(name) <= 100 and all(c.isalpha() or c in " -'’" for c in name) and text not in {"si","yes","no"}:
            d.name = name
        return {"draft":d}
    services = menu["services"]
    matches = [s for s in services if has(text,s["name"])]
    if not matches:
        matches = [s for s in services if any(len(w)>3 and has(text,w) for w in normalized(s["name"]).split())]
    if len(matches)==1:
        if d.service_id != matches[0]["id"]:
            d.professional_id = None
        d.service_id = matches[0]["id"]
    members = [p for p in menu["team"] if has(text,p["name"])]
    if len(members)==1:
        d.professional_id = members[0]["id"]
    elif has(text,"cualquiera") or has(text,"anyone"):
        d.professional_id = None
    today = datetime.now(LOCAL).date()
    iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b",text)
    if iso:
        try:
            d.day = date.fromisoformat(iso[0])
        except ValueError:
            return respond(d,"day","Escribe una fecha válida (AAAA-MM-DD)." if es else "Enter a valid date (YYYY-MM-DD).")
    elif has(text,"mañana") or has(text,"tomorrow"):
        d.day = today + timedelta(days=1)
    elif has(text,"hoy") or has(text,"today"):
        d.day = today
    else:
        for index,pair in enumerate(zip("lunes martes miercoles jueves viernes sabado domingo".split(),
                                        "monday tuesday wednesday thursday friday saturday sunday".split())):
            if any(has(text,w) for w in pair):
                d.day = today + timedelta(days=(index-today.weekday())%7)
                break
    clock = re.search(r"(?:\ba las?\s+|\bat\s+|^)(\d{1,2})(?::([0-5]\d))?\s*(am|pm)?(?![\w:-])",text)
    if clock:
        hour = int(clock[1])
        if clock[3] and 1 <= hour <= 12:
            hour = hour % 12 + (12 if clock[3]=="pm" else 0)
        if hour < 24:
            d.clock = f"{hour:02d}:{clock[2] or '00'}"
    if re.search(r"\b(con|with)\s+\w+",text) and not members and not any(has(text,w) for w in ["cualquiera","anyone"]):
        d.professional_id = None
        return respond(d,"professional","¿Con qué profesional?" if es else "Which professional?",
                       [p["name"] for p in menu["team"] if d.service_id is None or d.service_id in p["service_ids"]])
    return {"draft":d}


def lookup(state: State, runtime: Runtime[Session]):
    d, menu = state["draft"], state["menu"]
    es = state["turn"].language=="es"
    services = {s["id"]:s for s in menu["services"]}
    if d.service_id not in services:
        return respond(d,"service","¿Qué servicio quieres reservar?" if es else "Which service would you like?",[s["name"] for s in services.values()])
    team = {p["id"]:p for p in menu["team"] if d.service_id in p["service_ids"]}
    if d.professional_id is not None and d.professional_id not in team:
        return respond(d,"professional","Elige quién ofrece este servicio." if es else "Choose someone who offers this service.",[p["name"] for p in team.values()])
    if not d.day:
        return respond(d,"day","¿Qué día? Puedes escribir sábado o una fecha AAAA-MM-DD." if es else "Which day? Enter Saturday or a YYYY-MM-DD date.")
    slots = available(runtime.context,state["business"],d.day,d.service_id,d.professional_id)
    times = {k.astimezone(LOCAL).strftime("%H:%M"): (k,slots[k]) for k in sorted(slots)}
    if not times:
        d.clock = None
        return respond(d,"day",f"No hay turnos el {d.day}. ¿Qué otro día te sirve?" if es else f"No openings on {d.day}. Which other day works?")
    if d.clock not in times:
        d.clock = None
        return respond(d,"time",f"Para el {d.day}, elige una hora disponible (Costa Rica)." if es else f"Choose an available time for {d.day} (Costa Rica).",times.keys())
    if not d.name:
        return respond(d,"name","¿A qué nombre registro la cita?" if es else "What name should I put on the booking?")
    stamp, ids = times[d.clock]
    professional = team[ids[0]]
    details = f"{d.name} · {services[d.service_id]['name']} · {professional['name']} · {d.day} {d.clock} (Costa Rica)"
    return respond(d,"review",details+(". ¿Confirmas esta cita?" if es else ". Confirm this appointment?"),
                   proposal={"service_id":d.service_id,"professional_id":professional["id"],"customer_name":d.name,"starts_at":stamp.isoformat()})


builder = StateGraph(State, context_schema=Session)
builder.add_node("interpret",interpret)
builder.add_node("availability",lookup)
builder.add_edge(START,"interpret")
builder.add_conditional_edges("interpret",lambda state: END if state.get("reply") else "availability")
builder.add_edge("availability",END)
workflow = builder.compile()


@router.post("/chat")
def chat(business_id: str, turn: Turn, session: Database):
    menu = catalog(business_id, session)
    with tracing_context(enabled=False):
        result = workflow.invoke({"business":business_id,"turn":turn,"menu":menu},context=session)
    return {key:result[key] for key in ("draft","reply","options","proposal")}
