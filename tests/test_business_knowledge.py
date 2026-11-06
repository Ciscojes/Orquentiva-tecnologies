def auth(name):
    return {"Cookie":f"orqentiva_session=test-{name}", "Origin":"http://testserver"}

ALFA, BETA, ADMIN=map(auth,("alfa","beta","admin"))


def ask(client, tenant, message, **extra):
    response=client.post(f"/book/{tenant}/chat",json={"message":message,**extra})
    response.raise_for_status()
    return response.json()


def test_only_current_published_evidence_can_be_quoted(client):
    url="/client/documents"
    text="Aceptamos efectivo.\n\nPara cancelar, avisa con 24 horas de anticipación."
    draft={"title":"Condiciones","body":text}
    assert client.post(url,json=draft).status_code==401
    assert client.post(url,headers=ADMIN,json=draft).status_code==403
    assert client.post(url,headers=ALFA,json={**draft,"business_id":"beta"}).status_code==422
    doc=client.post(url,headers=ALFA,json=draft).json()
    path=f"{url}/{doc['id']}"
    q="¿Con cuánta anticipación puedo cancelar una cita en Barbería Alfa?"
    assert not ask(client,"alfa",q)["sources"]
    assert client.get(url,headers=BETA).json()==[]
    assert client.put(path,headers=BETA,json=draft).status_code==404
    assert client.put(path,headers=ALFA,json={**draft,"published":True}).status_code==200
    result=ask(client,"alfa",q)
    assert result["sources"]==[{"title":"Condiciones","paragraph":2,"quote":text.split("\n\n")[1]}]
    assert not ask(client,"beta",q)["sources"]
    assert not ask(client,"alfa","¿Cuánto cuesta el depósito?")["sources"]
    assert not ask(client,"alfa","Are pets allowed?",mode="knowledge",language="en")["sources"]
    assert ask(client,"alfa","How much notice to cancel?",language="en")["sources"]
    assert not client.get("/client/dashboard",headers=ALFA).json()["appointments"]
    assert client.put(path,headers=ALFA,json={**draft,"body":"Para cancelar, avisa con 48 horas de anticipación.","published":True}).status_code==200
    assert "48" in ask(client,"alfa",q)["sources"][0]["quote"]
    assert client.put(path,headers=ALFA,json=draft).status_code==200
    assert not ask(client,"alfa",q)["sources"]
