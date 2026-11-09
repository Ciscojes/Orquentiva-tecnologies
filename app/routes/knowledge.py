"""Documentos por empresa y consulta con RAG.

Recuperación: búsqueda léxica de párrafos publicados del negocio (sin costo ni red).
Generación: si el LLM está activo, redacta la respuesta solo con esos párrafos y cita
cuáles usó (app/llm.py). Sin LLM, o si su respuesta no es válida, se devuelve el
párrafo literal como antes.
"""
import re
import unicodedata
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import select, func
from app import llm
from app.models import Business, KnowledgeDocument
from app.routes.client import Database, Tenant

router = APIRouter(prefix="/client/documents", tags=["knowledge"])


class DocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=6000)
    published: StrictBool = False


def view(doc):
    return {"id":doc.id,"title":doc.title,"body":doc.body,"published":doc.published}


@router.get("")
def documents(business_id: Tenant, session: Database):
    return [view(d) for d in session.scalars(select(KnowledgeDocument).where(
        KnowledgeDocument.business_id==business_id).order_by(KnowledgeDocument.id))]


@router.post("", status_code=201)
def create(payload: DocumentIn, business_id: Tenant, session: Database):
    session.scalar(select(Business.id).where(Business.id==business_id).with_for_update())
    count = session.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.business_id==business_id))
    if count >= 50:
        raise HTTPException(409,"Límite de documentos alcanzado")
    doc = KnowledgeDocument(business_id=business_id, **payload.model_dump())
    session.add(doc)
    session.commit()
    return view(doc)


@router.put("/{document_id}")
def update(document_id: int, payload: DocumentIn, business_id: Tenant, session: Database):
    doc = session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.business_id==business_id,
                                                         KnowledgeDocument.id==document_id))
    if doc is None:
        raise HTTPException(404,"Documento no encontrado")
    for key,value in payload.model_dump().items():
        setattr(doc,key,value)
    session.commit()
    return view(doc)


STOP = set("que cual cuales cuanto cuanta puedo puedo pueden tiene tienen tiene con sin una uno los las para por como este esta del hay sobre cita citas negocio negocios politica politicas reserva reservas policy policies booking appointment appointments what when how much the can with your are you and about does have their this business".split())
GROUPS = {
    "cancel": "cancelar cancelacion cancelaciones cancelo cancela cancelar cancelan cancel cancellation cancellations cancelling canceled",
    "notice": "anticipacion antelacion aviso preaviso anticipada antes beforehand advance notice",
    "payment": "pago pagos pagar payment payments pay",
    "refund": "reembolso reembolsos devolucion devoluciones refund refunds",
    "late": "tarde tardanza retraso retrasos late lateness",
    "change": "reprogramar reprogramacion reagendar reschedule rescheduling",
    "card": "tarjeta tarjetas card cards",
    "cash": "efectivo cash",
    "deposit": "anticipo anticipos deposito deposit deposits",
}
ALIASES = {word:key for key,words in GROUPS.items() for word in words.split()}


def tokens(text):
    plain = "".join(c for c in unicodedata.normalize("NFD",text.lower()) if not unicodedata.combining(c))
    return {ALIASES.get(w,w) for w in re.findall(r"[a-z0-9]+",plain) if len(w)>2 and w not in STOP}


def policy_question(message):
    return bool(tokens(message) & set(GROUPS)) or bool(re.search(r"\b(pol[ií]ticas?|polic(?:y|ies))\b",message,re.I))


# Si la búsqueda léxica no encuentra nada, el LLM puede leer todos los párrafos del negocio
# cuando caben en este tamaño; así entiende sinónimos sin embeddings ni costos extra.
MAX_CONTEXT_CHARS = 6000
MAX_CANDIDATES = 4


def answer(session, business_id, question, language, business_name, use_llm=False):
    terms = tokens(question) - tokens(business_name)
    docs = session.scalars(select(KnowledgeDocument).where(KnowledgeDocument.business_id==business_id,
                           KnowledgeDocument.published.is_(True)).order_by(KnowledgeDocument.id))
    hits = []
    every = []
    for doc in docs:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n",doc.body) if p.strip()]
        for number,paragraph in enumerate(paragraphs,1):
            every.append({"title":doc.title,"paragraph":number,"quote":paragraph})
            words = tokens(paragraph)
            common = terms & words
            title = terms & tokens(doc.title)
            topics = terms & set(GROUPS)
            evidence = words | (tokens(doc.title) if len(paragraphs)==1 else set())
            if not terms or not topics.issubset(evidence):
                continue
            if not common and not (len(paragraphs)==1 and title):
                continue
            coverage = len(terms & evidence)/len(terms)
            if coverage < 0.5:
                continue
            score = (coverage,len(common),len(title))
            hits.append((score,{"title":doc.title,"paragraph":number,"quote":paragraph}))
    hits.sort(key=lambda pair:pair[0],reverse=True)
    sources = [source for score,source in hits if score==hits[0][0]][:3]
    if use_llm:
        generated = generate(question, language, [source for _,source in hits][:MAX_CANDIDATES] or fit(every), bool(sources))
        if generated is not None:
            return generated
    if sources:
        reply = "Esto indica el negocio en su documentación:" if language=="es" else "The business gives the following information:"
    else:
        reply = ("No encontré una respuesta documentada. Consulta directamente con el negocio."
                 if language=="es" else "I couldn't find a documented answer. Please ask the business directly.")
    return {"kind":"knowledge","reply":reply,"sources":sources,"generated":False}


def fit(paragraphs):
    """Todos los párrafos publicados si caben en el contexto; si no, ninguno."""
    return paragraphs if sum(len(p["quote"]) for p in paragraphs) <= MAX_CONTEXT_CHARS else []


def generate(question, language, candidates, has_extractive):
    """Paso de generación del RAG; None para volver al modo extractivo."""
    numbered = [{**c, "id": f"p{i}"} for i, c in enumerate(candidates, 1)]
    result = llm.answer_from_sources(question, numbered, language)
    if result is None:
        return None
    if result["answer"] is None:
        # El LLM no ve respuesta: si la búsqueda léxica sí encontró algo, se muestra literal.
        if has_extractive:
            return None
        reply = ("No encontré una respuesta documentada. Consulta directamente con el negocio."
                 if language=="es" else "I couldn't find a documented answer. Please ask the business directly.")
        return {"kind":"knowledge","reply":reply,"sources":[],"generated":False}
    by_id = {c["id"]: c for c in numbered}
    sources = [{k: by_id[i][k] for k in ("title","paragraph","quote")} for i in result["source_ids"]]
    return {"kind":"knowledge","reply":result["answer"],"sources":sources,"generated":True}
