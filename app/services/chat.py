"""Conversación guiada; el grafo consulta la agenda, sin efectuar escrituras.

Flujo: understand (LLM opcional) -> interpret (reglas) -> availability (agenda).
"""
import re
import unicodedata
from datetime import date, datetime
from typing import Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langsmith import tracing_context
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app import llm
from app.contact import normalize_contact
from app.scheduling import LOCAL
from app.services.agenda import available, public_catalog
from app.services.knowledge import answer, policy_question
from app.timeparse import choose_clock, choose_day, find_clock, find_day


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_id: int | None = None
    professional_id: int | None = None
    day: date | None = None
    clock: str | None = Field(None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    name: str = Field("", max_length=100)
    contact: str = Field("", max_length=254)
    step: Literal["request","service","professional","day","time","name","contact","review"] = "request"


class Turn(BaseModel):
    mode: Literal['booking','knowledge'] = 'booking'
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
    use_llm: bool
    hints: dict
    today: date
    ask_contact: bool


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if not unicodedata.combining(c))


def has(text, phrase):
    return re.search(r"(?<!\w)" + re.escape(normalized(phrase)) + r"(?!\w)", text) is not None


def respond(draft, step, reply, options=(), proposal=None):
    return {"draft": draft.model_copy(update={"step":step}), "reply":reply,
            "options":list(options), "proposal":proposal}


def current_day(state: State) -> date:
    """Hoy en la zona del negocio; el estado puede fijarlo para pruebas y evaluaciones."""
    return state.get("today") or datetime.now(LOCAL).date()


def understand(state: State):
    """Propuesta opcional del LLM; vacía si no está activo o si falla."""
    if not state.get("use_llm"):
        return {"hints": {}}
    turn = state["turn"]
    return {"hints": llm.extract(turn.message, state["menu"], current_day(state), turn.language)}


def interpret(state: State):
    turn, menu = state["turn"], state["menu"]
    hints = state.get("hints") or {}
    d = turn.draft.model_copy()
    raw = turn.message.strip()
    text = normalized(raw)
    es = turn.language == "es"
    if d.step == "name" and raw:
        name = re.sub(r"^(?:me llamo|soy|mi nombre es|my name is|i am|i'm)\s+", "", raw, flags=re.I).strip(" .")
        if 1 <= len(name) <= 100 and all(c.isalpha() or c in " -'’" for c in name) and text not in {"si","yes","no"}:
            d.name = name
        elif hints.get("name"):
            d.name = hints["name"]
        return {"draft":d}
    if d.step == "contact" and raw:
        try:
            d.contact = normalize_contact(raw)
        except ValueError:
            return respond(d,"contact","Escribe un teléfono (por ejemplo 8888 1234) o un correo válido."
                           if es else "Enter a phone number (for example 8888 1234) or a valid email.")
        return {"draft":d}
    # Servicio: el nombre completo manda, salvo que el mensaje nombre además algo propio de otro
    # servicio ("corte con barba"). En ese caso, o si solo coincide una palabra, decide el LLM:
    # su propuesta ya está validada contra el catálogo.
    services = menu["services"]
    words = {s["id"]: {w for w in normalized(s["name"]).split() if len(w)>3 and has(text,w)} for s in services}
    exact = [s for s in services if has(text,s["name"])]
    matches = exact or [s for s in services if words[s["id"]]]
    service_id = matches[0]["id"] if len(matches)==1 else None
    sure = len(exact)==1 and not any(words[s["id"]] - words[service_id] for s in services)
    if service_id is not None and not sure:
        service_id = hints.get("service_id", service_id)
    if service_id is not None:
        if d.service_id != service_id:
            d.professional_id = None
        d.service_id = service_id
    members = [p for p in menu["team"] if has(text,p["name"])]
    if len(members)==1:
        d.professional_id = members[0]["id"]
    elif has(text,"cualquiera") or has(text,"anyone"):
        d.professional_id = None
    # Día y hora: las reglas inequívocas mandan; en las dudosas el LLM precisa dentro de sus límites.
    today = current_day(state)
    try:
        day = find_day(text, today)
    except ValueError:
        return respond(d,"day","Escribe una fecha válida (AAAA-MM-DD)." if es else "Enter a valid date (YYYY-MM-DD).")
    if day.mentioned:
        # "La semana que viene" sin día concreto borra el día anterior: el chat lo preguntará.
        d.day = choose_day(day, hints.get("day"), today)
    clock = find_clock(text)
    if clock.value:
        d.clock = choose_clock(clock, hints.get("clock"))
    # En lo que las reglas no reconocieron, el LLM completa los campos que sigan vacíos.
    fill = ("service_id", "professional_id", "clock", "name") + (() if day.mentioned else ("day",))
    for field in fill:
        if getattr(d, field) in (None, "") and field in hints:
            setattr(d, field, hints[field])
    if (re.search(r"\b(con|with)\s+\w+",text) and not members and "professional_id" not in hints
            and not any(has(text,w) for w in ["cualquiera","anyone"])):
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
    if state.get("ask_contact", True) and not d.contact:
        return respond(d,"contact","¿A qué teléfono o correo te avisamos si hay cambios?" if es
                       else "Which phone number or email should we use if anything changes?")
    stamp, ids = times[d.clock]
    professional = team[ids[0]]
    details = f"{d.name} · {services[d.service_id]['name']} · {professional['name']} · {d.day} {d.clock} (Costa Rica)"
    if d.contact:
        details += f" · {d.contact}"
    proposal = {"service_id":d.service_id,"professional_id":professional["id"],"customer_name":d.name,"starts_at":stamp.isoformat()}
    if d.contact:
        proposal["customer_contact"] = d.contact
    return respond(d,"review",details+(". ¿Confirmas esta cita?" if es else ". Confirm this appointment?"), proposal=proposal)


builder = StateGraph(State, context_schema=Session)
builder.add_node("understand",understand)
builder.add_node("interpret",interpret)
builder.add_node("availability",lookup)
builder.add_edge(START,"understand")
builder.add_edge("understand","interpret")
builder.add_conditional_edges("interpret",lambda state: END if state.get("reply") else "availability")
builder.add_edge("availability",END)
workflow = builder.compile()


def run_chat(business_id: str, turn: Turn, session, use_llm: bool = False, ask_contact: bool = True):
    menu = public_catalog(session, business_id)
    if turn.mode == 'knowledge' or policy_question(turn.message):
        return answer(session, business_id, turn.message, turn.language, menu['name'], use_llm)
    with tracing_context(enabled=False):
        result = workflow.invoke({"business":business_id,"turn":turn,"menu":menu,"use_llm":use_llm,
                                  "ask_contact":ask_contact},context=session)
    return {key:result[key] for key in ("draft","reply","options","proposal")}
