from datetime import datetime, timedelta
from uuid import uuid4
from app.scheduling import LOCAL
from app.routes.public_booking import limiter

OWNER = {"Cookie":"orqentiva_session=test-alfa", "Origin":"http://testserver"}


def test_chat_review_conflict_and_replay(client):
    limiter.buckets.clear()
    service = client.post("/client/services",headers=OWNER,json={"name":"Corte recto","duration_minutes":30,"price_crc":5000}).json()
    days = [{"weekday":i,"is_closed":False,"opens_at":"09:00","closes_at":"13:00"} for i in range(7)]
    client.put("/client/hours",headers=OWNER,json={"days":days}).raise_for_status()
    ana = client.post("/client/team",headers=OWNER,json={"name":"Ana","days":days,"service_ids":[service["id"]]}).json()
    def turn(message, draft=None):
        response=client.post("/book/alfa/chat",json={"message":message, "draft":draft or {}})
        response.raise_for_status()
        return response.json()
    day=(datetime.now(LOCAL)+timedelta(days=7)).date().isoformat()
    first=turn(f"Quiero un corte con Ana el {day} a las 10")
    assert first["draft"]["step"]=="name"
    review=turn("Soy Pedro",first["draft"])
    assert all(v in review["reply"] for v in ("Pedro","Ana","Corte recto",day,"10:00"))
    assert not client.get("/client/dashboard",headers=OWNER).json()["appointments"]
    proposal=review["proposal"]
    assert proposal["professional_id"]==ana["id"]
    other=client.post("/book/beta/chat",json={"message":"","draft":review["draft"]}).json()
    assert other["proposal"] is None and "Ana" not in other["reply"]
    payload={**proposal,"request_key":str(uuid4())}
    once=client.post("/book/alfa",json=payload)
    assert once.status_code==201 and client.post("/book/alfa",json=payload).json()==once.json()
    assert client.post("/book/alfa",json={**payload,"request_key":str(uuid4())}).status_code==409
    alternatives=turn("",{**review["draft"],"clock":None})
    assert alternatives["proposal"] is None and "10:00" not in alternatives["options"] and "10:30" in alternatives["options"]
    assert turn("10:30",alternatives["draft"])["proposal"]
    assert len(client.get("/client/dashboard",headers=OWNER).json()["appointments"])==1
