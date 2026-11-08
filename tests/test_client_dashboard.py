"""Panel de cliente: persistencia, horario atómico y aislamiento."""
import pytest
from sqlalchemy import select
from app.models import Service, BusinessHours

ALFA = {"Cookie":"orqentiva_session=test-alfa", "Origin":"http://testserver"}
BETA = {"Cookie":"orqentiva_session=test-beta", "Origin":"http://testserver"}
ADMIN = {"Cookie":"orqentiva_session=test-admin", "Origin":"http://testserver"}
SERVICE = {"name":"Corte QA", "price_crc":7000, "duration_minutes":45, "is_active":True}

def week():
    return {"days":[{"weekday":day,"is_closed":day>=5,"opens_at":"09:00" if day<5 else None,"closes_at":"17:30" if day<5 else None} for day in range(7)]}


@pytest.mark.parametrize("method,path,payload",[("GET","/client/dashboard",None),("POST","/client/services",SERVICE),("PUT","/client/services/1",SERVICE),("PUT","/client/hours",week())])
def test_client_routes_require_business_session(client,method,path,payload):
    assert client.request(method,path,json=payload).status_code == 401
    assert client.request(method,path,json=payload,headers=ADMIN).status_code == 403


def test_dashboard_isolation_and_undefined_legacy_duration(client):
    client.post("/appointments",headers=ALFA,json={"customer_name":"Solo Alfa", "starts_at":"2036-01-01T18:00:00Z"})
    response=client.get("/client/dashboard?business_id=beta",headers=ALFA)
    assert response.headers["cache-control"] == "no-store"
    data=response.json()
    assert data["business"] == {"id":"alfa","name":"Barbería Alfa","time_zone":"America/Costa_Rica"}
    assert data["services"][0]["name"] == "Corte clásico"
    assert data["services"][0]["duration_minutes"] is None
    assert data["services"][0]["is_active"] is True
    assert data["appointments"][0]["customer_name"] == "Solo Alfa"
    assert data["appointments"][0]["starts_at"] == "2036-01-01T18:00:00+00:00"
    assert data["hours"]["configured"] is False and len(data["hours"]["days"]) == 7
    assert all(day["is_closed"] for day in data["hours"]["days"])
    beta=client.get("/client/dashboard",headers=BETA).json()
    assert beta["appointments"] == [] and beta["services"][0]["name"] == "Corte premium"


def test_create_edit_and_disable_own_service(client,session_factory):
    response=client.post("/client/services",headers=ALFA,json={**SERVICE,"name":"  Corte QA  "})
    assert response.status_code == 201
    row=response.json()
    assert row["name"] == "Corte QA"
    changed={**SERVICE,"price_crc":0,"duration_minutes":60,"is_active":False}
    assert client.put(f"/client/services/{row['id']}",headers=ALFA,json=changed).status_code == 200
    with session_factory() as session:
        saved=session.get(Service,row["id"])
        assert saved.business_id == "alfa" and saved.price_crc == 0 and saved.duration_minutes == 60 and saved.is_active is False
    assert len(client.get("/client/dashboard",headers=BETA).json()["services"]) == 1


def test_cross_tenant_service_id_is_not_exposed(client):
    beta_id=client.get("/client/dashboard",headers=BETA).json()["services"][0]["id"]
    foreign=client.put(f"/client/services/{beta_id}",headers=ALFA,json=SERVICE)
    missing=client.put("/client/services/999999",headers=ALFA,json=SERVICE)
    assert foreign.status_code == missing.status_code == 404 and foreign.json() == missing.json()
    assert client.get("/client/dashboard",headers=BETA).json()["services"][0]["name"] == "Corte premium"


@pytest.mark.parametrize("change",[{"name":" "},{"price_crc":-1},{"price_crc":1.5},{"price_crc":True},{"price_crc":"100"},{"duration_minutes":None},{"duration_minutes":4},{"duration_minutes":481},{"duration_minutes":True},{"is_active":"false"},{"business_id":"beta"}])
def test_invalid_services_are_rejected_without_rows(client,change):
    assert client.post("/client/services",headers=ALFA,json={**SERVICE,**change}).status_code == 422
    assert len(client.get("/client/dashboard",headers=ALFA).json()["services"]) == 1


def test_hours_saved_atomically_and_isolated(client,session_factory):
    response=client.put("/client/hours",headers=ALFA,json=week())
    assert response.status_code == 200 and response.json()["configured"] is True
    assert response.json()["days"][0]["opens_at"] == "09:00"
    with session_factory() as session:
        rows=session.scalars(select(BusinessHours).where(BusinessHours.business_id=="alfa")).all()
        assert len(rows)==7 and rows[0].opens_at==540
    again=week()
    again["days"][0]={"weekday":0,"is_closed":True,"opens_at":None,"closes_at":None}
    assert client.put("/client/hours",headers=ALFA,json=again).status_code == 200
    assert client.get("/client/dashboard",headers=ALFA).json()["hours"]["days"][0]["is_closed"] is True
    assert client.get("/client/dashboard",headers=BETA).json()["hours"]["configured"] is False


@pytest.mark.parametrize("change",[{"opens_at":"18:00","closes_at":"09:00"},{"opens_at":"09:00","closes_at":"09:00"},{"opens_at":None},{"opens_at":"09:00:30"},{"closes_at":"24:00"},{"is_closed":True},{"weekday":7},{"weekday":1},{"is_closed":"false"}])
def test_invalid_week_does_not_overwrite_saved_schedule(client,change):
    valid=week()
    before=client.put("/client/hours",headers=ALFA,json=valid).json()
    invalid=week()
    invalid["days"][0].update(change)
    assert client.put("/client/hours",headers=ALFA,json=invalid).status_code == 422
    assert client.get("/client/dashboard",headers=ALFA).json()["hours"] == before


def test_week_requires_exactly_seven_days_and_no_tenant_field(client):
    assert client.put("/client/hours",headers=ALFA,json={"days":week()["days"][:6]}).status_code==422
    assert client.put("/client/hours",headers=ALFA,json={**week(),"business_id":"beta"}).status_code==422


@pytest.mark.parametrize("method,path,payload",[("POST","/client/services",SERVICE),("PUT","/client/services/1",SERVICE),("PUT","/client/hours",week())])
def test_client_mutations_require_origin(client,method,path,payload):
    assert client.request(method,path,json=payload,headers={"Cookie":ALFA["Cookie"]}).status_code==403
    assert client.request(method,path,json=payload,headers={**ALFA,"Origin":"https://evil.example"}).status_code==403


def test_disabled_business_cannot_use_client_panel(client):
    assert client.patch("/admin/businesses/alfa",headers=ADMIN,json={"is_active":False}).status_code==200
    assert client.get("/client/dashboard",headers=ALFA).status_code==401
    assert client.get("/client/dashboard",headers=BETA).status_code==200
