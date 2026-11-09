from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from datetime import date, timedelta

from app.routes.public_booking import limiter

ALFA = {"Cookie":"orqentiva_session=test-alfa","Origin":"http://testserver"}
BETA = {"Cookie":"orqentiva_session=test-beta","Origin":"http://testserver"}
ADMIN = {"Cookie":"orqentiva_session=test-admin","Origin":"http://testserver"}


def test_concurrent_customer_bookings_and_module_access(client):
    limiter.buckets.clear()
    service = client.post("/client/services", headers=ALFA, json={"name":"Corte","duration_minutes":30,"price_crc":5000}).json()["id"]
    days = [{"weekday":i,"is_closed":False,"opens_at":"09:00","closes_at":"13:00"} for i in range(7)]
    assert client.put("/client/hours", headers=ALFA,json={"days":days}).status_code == 200
    ids = []
    for name in ("Ana","Luis"):
        res = client.post("/client/team", headers=ALFA,json={"name":name,"days":days,"service_ids":[service]})
        assert res.status_code == 201
        ids.append(res.json()["id"])
    assert client.put(f"/client/team/{ids[0]}",headers=BETA,json={"name":"Other","days":days,"service_ids":[]}).status_code == 404
    path = "/book/alfa"
    params = {"day":(date.today()+timedelta(days=7)).isoformat(),"service_id":service}
    slots = client.get(path+"/availability",params=params).json()
    assert len(slots)==43
    stamp=slots[12]
    assert "T16:00:00" in stamp
    def reserve(name):
        payload={"customer_name":name,"service_id":service,"starts_at":stamp,"request_key":str(uuid4()),
                 "customer_contact":"8888-1234"}
        return payload,client.post(path,json=payload)
    with ThreadPoolExecutor(3) as pool:
        results=list(pool.map(reserve,["Pedro","María","Juan"]))
    assert sorted(r.status_code for _,r in results)==[201,201,409]
    winners=[(p,r.json()) for p,r in results if r.status_code==201]
    assert {r["professional_id"] for _,r in winners}==set(ids)
    payload, result = winners[0]
    assert client.post(path,json=payload).json()==result
    remaining=client.get(path+"/availability",params=params).json()
    assert slots[13] not in remaining and slots[18] in remaining
    dashboard=client.get("/client/dashboard",headers=ALFA).json()
    assert len(dashboard["appointments"])==2
    assert not client.get("/client/dashboard",headers=BETA).json()["appointments"]
    assert "appointments" not in client.get(path).json()
    assert client.post("/appointments",headers=ALFA,json={"customer_name":"Old","starts_at":stamp}).status_code==409
    url="/admin/businesses/alfa/agenda"
    assert client.put(url,headers=ALFA,json={"booking_enabled":False}).status_code==403
    assert client.put(url,headers=ADMIN,json={"booking_enabled":False}).status_code==200
    assert client.get(path).status_code==404
    assert client.post(path,json=payload).status_code==404
    assert not client.get("/client/dashboard",headers=ALFA).json()["booking_enabled"]
    assert client.put("/client/hours",headers=ALFA,json={"days":days}).status_code==409
    assert client.put(url,headers=ADMIN,json={"booking_enabled":True}).status_code==200
    assert len(client.get("/client/dashboard",headers=ALFA).json()["appointments"])==2
