"""Additional booking/chat/document checks for the temporary PostgreSQL verifier."""
from datetime import datetime, timedelta
from uuid import uuid4

def verify(client, alfa, beta):
    from app.scheduling import LOCAL
    from app.routes.public_booking import limiter
    limiter.buckets.clear()
    response = client.post('/client/services',headers=alfa,json={'name':'Corte QA TFM','price_crc':5000,'duration_minutes':30})
    response.raise_for_status()
    service = response.json()
    days = [{'weekday':i,'is_closed':False,'opens_at':'09:00','closes_at':'17:00'} for i in range(7)]
    client.put('/client/hours',headers=alfa,json={'days':days}).raise_for_status()
    response=client.post('/client/team',headers=alfa,json={'name':'Ana QA','days':days,'service_ids':[service['id']]})
    response.raise_for_status()
    member=response.json()
    day=(datetime.now(LOCAL)+timedelta(days=7)).date().isoformat()
    draft={'service_id':service['id'],'professional_id':member['id'],'day':day,'clock':'10:00','name':'Prueba TFM','step':'review'}
    def chat(tenant, **body):
        r=client.post(f'/book/{tenant}/chat',json=body)
        r.raise_for_status()
        return r.json()
    count=len(client.get('/client/dashboard',headers=alfa).json()['appointments'])
    proposal=chat('alfa',message='',draft=draft)['proposal']
    assert proposal
    assert len(client.get('/client/dashboard',headers=alfa).json()['appointments'])==count
    payload={**proposal,'request_key':str(uuid4())}
    first=client.post('/book/alfa',json=payload)
    assert first.status_code==201
    assert client.post('/book/alfa',json=payload).json()==first.json()
    assert client.post('/book/alfa',json={**payload,'request_key':str(uuid4())}).status_code==409
    doc=client.post('/client/documents',headers=alfa,json={'title':'Cancelaciones QA','body':'Para cancelar, avisa con 24 horas de anticipación.','published':True})
    doc.raise_for_status()
    question='¿Con cuánta anticipación puedo cancelar?'
    assert chat('alfa',message=question)['sources'][0]['quote']=='Para cancelar, avisa con 24 horas de anticipación.'
    assert not chat('beta',message=question)['sources']
    print('OK: chat, confirmación, reintento, conflicto y documentos aislados en PostgreSQL')
    # Remove only the QA service introduced here so the existing migration verifier
    # can compare the original service rows after downgrade.
    from sqlalchemy import delete
    from app.database import SessionLocal
    from app.models import Appointment, Professional, Service, KnowledgeDocument
    with SessionLocal.begin() as session:
        session.execute(delete(Appointment).where(Appointment.service_id==service['id']))
        session.execute(delete(Professional).where(Professional.id==member['id']))
        session.execute(delete(Service).where(Service.id==service['id']))
        session.execute(delete(KnowledgeDocument).where(KnowledgeDocument.id==doc.json()['id']))
