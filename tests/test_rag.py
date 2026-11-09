"""RAG: recuperación léxica + generación con el LLM simulado (nunca se llama a la red)."""
import json

import pytest

from app import llm
from app.routes import knowledge
from app.routes.booking_chat import llm_limiter

ALFA = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}
BETA = {"Cookie": "orqentiva_session=test-beta", "Origin": "http://testserver"}
POLICY = "Aceptamos efectivo y tarjeta.\n\nPara cancelar, avisa con 24 horas de anticipación.\n\nSi no te presentas, el anticipo no se devuelve."


@pytest.fixture
def docs(client):
    client.post("/client/documents", headers=ALFA, json={"title": "Condiciones", "body": POLICY, "published": True}).raise_for_status()
    client.post("/client/documents", headers=BETA, json={"title": "Normas Beta", "body": "Cancelar con 48 horas.", "published": True}).raise_for_status()


@pytest.fixture
def llm_on(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-only")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    llm_limiter.buckets.clear()


def fake(monkeypatch, reply):
    """Simula el modelo y guarda el contexto recibido."""
    seen = {}
    def model(payload):
        seen["context"] = json.loads(payload["messages"][1]["content"])
        return json.dumps(reply(seen["context"]) if callable(reply) else reply)
    monkeypatch.setattr(llm, "call_model", model)
    return seen


def ask(client, message, tenant="alfa"):
    response = client.post(f"/book/{tenant}/chat", json={"message": message, "mode": "knowledge"})
    response.raise_for_status()
    return response.json()


def test_generates_answer_citing_retrieved_paragraph(client, docs, llm_on, monkeypatch):
    seen = fake(monkeypatch, lambda ctx: {"answer": "Puedes cancelar avisando con 24 horas de anticipación.",
                                          "source_ids": [ctx["paragraphs"][0]["id"]]})
    result = ask(client, "¿Con cuánta anticipación puedo cancelar?")
    assert result["generated"] is True
    assert result["reply"] == "Puedes cancelar avisando con 24 horas de anticipación."
    assert result["sources"] == [{"title": "Condiciones", "paragraph": 2, "quote": "Para cancelar, avisa con 24 horas de anticipación."}]
    # La recuperación filtra antes de generar: solo llega el párrafo relevante.
    assert [p["text"] for p in seen["context"]["paragraphs"]] == ["Para cancelar, avisa con 24 horas de anticipación."]


def test_synonym_question_uses_all_paragraphs_of_the_business_only(client, docs, llm_on, monkeypatch):
    seen = fake(monkeypatch, lambda ctx: {"answer": "Si no te presentas, el anticipo no se devuelve.",
                                          "source_ids": [p["id"] for p in ctx["paragraphs"] if "presentas" in p["text"]]})
    # La búsqueda léxica no encuentra esta frase; el LLM la entiende leyendo los párrafos.
    result = ask(client, "¿Me regresan la plata si falto?")
    assert result["generated"] is True and result["sources"][0]["paragraph"] == 3
    texts = " ".join(p["text"] for p in seen["context"]["paragraphs"])
    assert "48 horas" not in texts and "Beta" not in texts


def test_invented_number_is_rejected_and_falls_back_to_literal(client, docs, llm_on, monkeypatch):
    fake(monkeypatch, lambda ctx: {"answer": "Debes avisar con 12 horas.", "source_ids": [ctx["paragraphs"][0]["id"]]})
    result = ask(client, "¿Con cuánta anticipación puedo cancelar?")
    assert result["generated"] is False
    assert result["sources"][0]["quote"] == "Para cancelar, avisa con 24 horas de anticipación."


def test_unknown_citation_is_rejected(client, docs, llm_on, monkeypatch):
    fake(monkeypatch, {"answer": "Avisa con 24 horas.", "source_ids": ["p99"]})
    assert ask(client, "¿Con cuánta anticipación puedo cancelar?")["generated"] is False


def test_no_answer_in_documents(client, docs, llm_on, monkeypatch):
    fake(monkeypatch, {"answer": None, "source_ids": []})
    result = ask(client, "¿Aceptan mascotas?")
    assert result["sources"] == [] and "Consulta directamente" in result["reply"]


def test_llm_doubt_keeps_literal_match(client, docs, llm_on, monkeypatch):
    fake(monkeypatch, {"answer": None, "source_ids": []})
    result = ask(client, "¿Con cuánta anticipación puedo cancelar?")
    assert result["generated"] is False and result["sources"]


def test_large_documents_are_not_sent_whole(client, llm_on, monkeypatch):
    big = "\n\n".join(f"Norma {i}: " + "texto " * 60 for i in range(12))
    for title in ("Reglamento A", "Reglamento B"):
        client.post("/client/documents", headers=ALFA, json={"title": title, "body": big, "published": True}).raise_for_status()
    calls = []
    monkeypatch.setattr(llm, "call_model", lambda payload: calls.append(1) or "{}")
    assert ask(client, "¿Me regresan la plata si falto?")["sources"] == []
    assert calls == []
    assert knowledge.MAX_CONTEXT_CHARS < 2 * len(big)


def test_without_llm_behaviour_is_unchanged(client, docs, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = ask(client, "¿Con cuánta anticipación puedo cancelar?")
    assert result["generated"] is False
    assert result["reply"] == "Esto indica el negocio en su documentación:"
