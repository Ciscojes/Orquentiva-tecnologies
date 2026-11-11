"""Chat público de reservas. El grafo y las reglas están en app/services/chat.py."""
from fastapi import APIRouter, Request

from app import llm
from app.deps import Database
from app.services.chat import Turn, run_chat
from app.services.rate_limit import RateLimiter

router = APIRouter(prefix="/book/{business_id}", tags=["chat"])
# Limita las llamadas al LLM por IP; al superarlo el chat sigue solo con reglas.
llm_limiter = RateLimiter(per_minute=20)


@router.post("/chat")
def chat(business_id: str, turn: Turn, session: Database, request: Request):
    use_llm = llm.enabled() and llm_limiter.allow(request)
    return run_chat(business_id, turn, session, use_llm)
