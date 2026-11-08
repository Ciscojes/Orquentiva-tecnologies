ALFA = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}
BETA = {"Cookie": "orqentiva_session=test-beta", "Origin": "http://testserver"}


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_requires_key(client):
    assert client.get("/services").status_code == 401


def test_each_business_sees_own_services(client):
    assert client.get("/services", headers=ALFA).json()[0]["name"] == "Corte clásico"
    assert client.get("/services", headers=BETA).json()[0]["name"] == "Corte premium"


def test_book_and_isolate_tenants(client):
    payload = {"customer_name": "Cliente Demo", "starts_at": "2030-11-02T15:00:00-06:00"}
    assert client.post("/appointments", headers=ALFA, json=payload).status_code == 201
    assert len(client.get("/appointments", headers=ALFA).json()) == 1
    assert client.get("/appointments", headers=BETA).json() == []
    assert client.post("/appointments", headers=ALFA, json=payload).status_code == 409
    assert client.post("/appointments", headers=BETA, json=payload).status_code == 201


def test_requires_timezone(client):
    payload = {"customer_name": "Cliente Demo", "starts_at": "2030-11-02T15:00:00"}
    assert client.post("/appointments", headers=ALFA, json=payload).status_code == 422
