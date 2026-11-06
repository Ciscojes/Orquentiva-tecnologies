"""SPEC-008: administración, permisos y desactivación de negocios."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select
from app.models import Business, User, AuthSession
from app.auth import token_digest, verify_password

ADMIN = {"Cookie": "orqentiva_session=test-admin", "Origin": "http://testserver"}
ALFA = {"Cookie": "orqentiva_session=test-alfa", "Origin": "http://testserver"}
BETA = {"Cookie": "orqentiva_session=test-beta", "Origin": "http://testserver"}
PASSWORD = "Temporary-User-QA-123!"


@pytest.mark.parametrize("method,path,body", [
    ("get", "/admin/businesses", None),
    ("post", "/admin/businesses", {"id":"gamma","name":"Gamma"}),
    ("patch", "/admin/businesses/alfa", {"is_active":False}),
    ("get", "/admin/businesses/alfa/users", None),
    ("post", "/admin/businesses/alfa/users", {"email":"qa@example.com","password":PASSWORD}),
])
def test_every_admin_endpoint_is_protected(client, method, path, body):
    assert client.request(method, path, json=body).status_code == 401
    assert client.request(method, path, json=body, headers=ALFA).status_code == 403


def test_business_creation_validation_duplicates_and_persistence(client, session_factory):
    initial = client.get("/admin/businesses", headers=ADMIN)
    assert initial.status_code == 200 and initial.headers["cache-control"] == "no-store"
    assert {item["id"] for item in initial.json()} == {"alfa", "beta"}
    response = client.post("/admin/businesses", headers=ADMIN, json={"id":"  gamma  ", "name":"  Negocio Gamma  "})
    assert response.status_code == 201
    assert response.json() == {"id":"gamma", "name":"Negocio Gamma", "is_active":True, "booking_enabled":True}
    with session_factory() as session:
        assert session.get(Business,"gamma").name == "Negocio Gamma"
    assert client.post("/admin/businesses", headers=ADMIN, json={"id":"gamma","name":"Otro"}).status_code == 409
    for payload in [{"id":"Gamma","name":"Name"}, {"id":"bad/id","name":"Name"}, {"id":"new","name":"   "}, {"id":"a"*51,"name":"Name"}, {"id":"new","name":"Name","is_active":False}]:
        assert client.post("/admin/businesses", headers=ADMIN,json=payload).status_code == 422


def test_concurrent_duplicate_businesses(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: client.post("/admin/businesses", headers=ADMIN, json={"id":"gamma","name":"Gamma"}).status_code, range(2)))
    assert sorted(statuses) == [201,409]


def test_disable_revokes_only_target_and_reactivation_requires_login(client, session_factory):
    assert client.patch("/admin/businesses/alfa", headers=ADMIN, json={"is_active":False}).json()["is_active"] is False
    assert client.get("/auth/me", headers=ALFA).status_code == 401
    assert client.get("/services", headers=BETA).status_code == 200
    with session_factory() as session:
        assert session.get(AuthSession, token_digest("test-alfa")) is None
    login = {"email":"alfa@example.com", "password":"Only-for-tests-123!"}
    assert client.post("/auth/login", headers={"Origin":"http://testserver"},json=login).status_code == 401
    assert client.patch("/admin/businesses/alfa",headers=ADMIN,json={"is_active":True}).status_code == 200
    assert client.get("/services",headers=ALFA).status_code == 401
    assert client.post("/auth/login", headers={"Origin":"http://testserver"},json=login).status_code == 200
    assert client.get("/services").json()[0]["name"] == "Corte clásico"


def test_disabled_business_rejected_even_if_session_exists(client,session_factory):
    with session_factory.begin() as session:
        session.get(Business,"alfa").is_active = False
    assert client.get("/auth/me",headers=ALFA).status_code == 403
    assert client.get("/appointments",headers=ALFA).status_code == 403


def test_create_account_for_selected_business(client,session_factory):
    response = client.post("/admin/businesses/beta/users",headers=ADMIN,json={"email":" New@example.com ","password":PASSWORD})
    assert response.status_code == 201
    assert response.json()["business_id"] == "beta" and response.json()["role"] == "business_admin"
    assert PASSWORD not in response.text and "password_hash" not in response.text
    with session_factory() as session:
        user = session.scalar(select(User).where(User.email == "new@example.com"))
        assert verify_password(PASSWORD,user.password_hash)
    rows = client.get("/admin/businesses/beta/users",headers=ADMIN).json()
    assert {row["email"] for row in rows} == {"beta@example.com","new@example.com"}
    assert {row["email"] for row in client.get("/admin/businesses/alfa/users",headers=ADMIN).json()} == {"alfa@example.com"}
    assert client.post("/auth/login",headers={"Origin":"http://testserver"},json={"email":"new@example.com","password":PASSWORD}).status_code == 200
    assert client.get("/business/me").json()["id"] == "beta"
    assert client.get("/admin/businesses").status_code == 403


def test_account_creation_rejects_escalation_duplicate_and_invalid_data(client):
    base = {"email":"new@example.com","password":PASSWORD}
    for extra in [{"role":"super_admin"}, {"business_id":"alfa"}]:
        response = client.post("/admin/businesses/beta/users",headers=ADMIN,json={**base,**extra})
        assert response.status_code == 422 and PASSWORD not in response.text
    for change in [{"email":"bad"}, {"password":"too-short"}, {"password":" "*12}]:
        response = client.post("/admin/businesses/beta/users",headers=ADMIN,json={**base,**change})
        assert response.status_code == 422 and PASSWORD not in response.text
    response = client.post("/admin/businesses/beta/users",headers=ADMIN,json={**base,"email":"ALFA@example.com"})
    assert response.status_code == 409
    assert client.get("/business/me",headers=ALFA).json()["id"] == "alfa"


def test_state_is_strict_and_target_must_exist(client):
    for value in ["false",0,None]:
        assert client.patch("/admin/businesses/alfa",headers=ADMIN,json={"is_active":value}).status_code == 422
    assert client.patch("/admin/businesses/missing",headers=ADMIN,json={"is_active":False}).status_code == 404
    assert client.get("/admin/businesses/missing/users",headers=ADMIN).status_code == 404
    assert client.post("/admin/businesses/missing/users",headers=ADMIN,json={"email":"qa@example.com","password":PASSWORD}).status_code == 404


@pytest.mark.parametrize("method,path,body", [
    ("post","/admin/businesses",{"id":"gamma","name":"Gamma"}),
    ("patch","/admin/businesses/alfa",{"is_active":False}),
    ("post","/admin/businesses/alfa/users",{"email":"new@example.com","password":PASSWORD}),
])
def test_admin_mutations_require_origin(client,method,path,body):
    assert client.request(method,path,headers={"Cookie":ADMIN["Cookie"]},json=body).status_code == 403
    assert client.request(method,path,headers={**ADMIN,"Origin":"https://evil.example"},json=body).status_code == 403
