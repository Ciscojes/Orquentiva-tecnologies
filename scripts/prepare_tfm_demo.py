"""Create an isolated local demo. Refuses to overwrite any existing database."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'tfm-demo.sqlite3'
PASSWORD = 'Orqentiva-Demo-2026!'

def main():
    if DB.exists():
        raise SystemExit('La base de demostración ya existe. Se conserva sin cambios.')
    os.environ['DATABASE_URL'] = 'sqlite:///' + DB.as_posix()
    sys.path.insert(0, str(ROOT))
    from alembic import command
    from alembic.config import Config
    from app.database import SessionLocal, engine
    from app.auth import UserCreate, create_user
    from app.models import BusinessHours, Professional, Service, KnowledgeDocument
    from seed import seed_database
    os.chdir(ROOT)
    command.upgrade(Config(str(ROOT/'alembic.ini')), 'head')
    seed_database()
    days = [{'weekday':i,'is_closed':False,'opens_at':'09:00','closes_at':'17:00'} for i in range(7)]
    with SessionLocal.begin() as session:
        for name in ('admin','alfa','beta'):
            create_user(session, UserCreate(email=f'{name}@example.com', password=PASSWORD,
                role='super_admin' if name=='admin' else 'business_admin',
                business_id=None if name=='admin' else name))
        for business, person in [('alfa','Ana'),('beta','Luis')]:
            service = Service(business_id=business, name='Corte demo', price_crc=5000, duration_minutes=30)
            session.add(service)
            session.flush()
            for i in range(7):
                session.add(BusinessHours(business_id=business,weekday=i,is_closed=False,opens_at=540,closes_at=1020))
            session.add(Professional(business_id=business,name=person,days=days,service_ids=[service.id]))
            hours = 24 if business=='alfa' else 48
            session.add(KnowledgeDocument(business_id=business,title='Cancelaciones',
                body=f'Para cancelar, avisa con {hours} horas de anticipación.',published=True))
    engine.dispose()
    print('Demostración aislada preparada. Consulta tfm/ACCESO_DEMO.md para los accesos.')

if __name__ == '__main__':
    main()
