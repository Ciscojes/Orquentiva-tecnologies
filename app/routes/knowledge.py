"""Documentos del negocio autenticado. La consulta con RAG está en app/services/knowledge.py."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import select, func
from app.deps import Database, Tenant
from app.models import Business, KnowledgeDocument
from app.services.knowledge import MAX_CONTEXT_CHARS  # noqa: F401  (límite documentado; lo consulta tests/test_rag.py)

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
