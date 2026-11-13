"""Base de demostración para el video. Todos los datos son ficticios.

Crea video/.work/demo.sqlite3 desde cero en cada ejecución (nunca toca la base
habitual ni tfm-demo.sqlite3). Uso: python video/seed_demo.py
"""
import json
import os
import secrets
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "video" / ".work"
DB = WORK / "demo.sqlite3"
LOGIN = WORK / "demo-login.json"
DEMO_EMAIL = "alfa@example.com"
ANA, DIEGO, SOFIA = "Ana", "Diego", "Sofía"

SERVICES = [  # nombre, precio en colones, minutos
    ("Corte clásico", 5000, 30),
    ("Corte y barba", 8000, 45),
    ("Afeitado tradicional", 4500, 30),
    ("Corte infantil", 4000, 30),
]
TEAM = {  # profesional -> índices de servicios que ofrece
    ANA: [0, 1, 3],
    DIEGO: [0, 1, 2],
    SOFIA: [0, 2, 3],
}
DOCUMENTS = [
    ("Cancelaciones", "Para cancelar o cambiar tu cita, avisa con 24 horas de anticipación. "
                      "Si avisas con menos tiempo, podremos reagendar según la disponibilidad."),
    ("Formas de pago", "Aceptamos efectivo, tarjeta y SINPE Móvil. El pago se realiza en el local al terminar el servicio."),
    ("Llegadas tarde", "Guardamos tu turno durante 10 minutos. Pasado ese tiempo, la cita puede reasignarse."),
]
# Citas ya agendadas: (días desde hoy, hora, profesional, índice de servicio, cliente, contacto)
BOOKINGS = [
    (1, "09:00", ANA, 0, "Marco Solís", "marco.solis@example.com"),
    (1, "10:30", DIEGO, 1, "Esteban Rojas", "esteban.rojas@example.com"),
    (1, "14:00", SOFIA, 3, "Valeria Mora", "valeria.mora@example.com"),
    (2, "09:30", DIEGO, 2, "Andrés Vargas", "andres.vargas@example.com"),
    (2, "11:00", ANA, 1, "Luis Castro", "luis.castro@example.com"),
    (2, "15:30", SOFIA, 0, "Gabriel Jiménez", "gabriel.jimenez@example.com"),
    (3, "09:00", SOFIA, 2, "Daniel Chaves", "daniel.chaves@example.com"),
    (3, "11:30", DIEGO, 0, "José Quesada", "jose.quesada@example.com"),
]


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    DB.unlink(missing_ok=True)
    # El acceso al panel se genera en cada ejecución y solo vive en video/.work (ignorado por git);
    # la grabación lo lee de ahí. Ningún archivo del proyecto contiene una contraseña.
    access = secrets.token_urlsafe(18)
    LOGIN.write_text(json.dumps({"email": DEMO_EMAIL, "password": access}), encoding="utf-8")
    os.environ["DATABASE_URL"] = "sqlite:///" + DB.as_posix()
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    from alembic import command
    from alembic.config import Config
    from app.auth import UserCreate, create_user
    from app.database import SessionLocal, engine
    from app.models import Appointment, Business, BusinessHours, KnowledgeDocument, Professional, Service
    from app.scheduling import LOCAL

    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    # Lunes a sábado de 9:00 a 18:00; domingo cerrado (weekday 6).
    week = [{"weekday": i, "is_closed": i == 6, "opens_at": None if i == 6 else "09:00",
             "closes_at": None if i == 6 else "18:00"} for i in range(7)]
    today = datetime.now(LOCAL).date()
    with SessionLocal.begin() as session:
        session.add(Business(id="alfa", name="Barbería Alfa"))
        session.add(Business(id="beta", name="Barbería Beta"))
        session.flush()
        create_user(session, UserCreate(email=DEMO_EMAIL, password=access, role="business_admin", business_id="alfa"))
        services = [Service(business_id="alfa", name=n, price_crc=p, duration_minutes=m) for n, p, m in SERVICES]
        session.add_all(services)
        session.flush()
        for i in range(7):
            closed = i == 6
            session.add(BusinessHours(business_id="alfa", weekday=i, is_closed=closed,
                                      opens_at=None if closed else 540, closes_at=None if closed else 1080))
        people = {}
        for name, offered in TEAM.items():
            people[name] = Professional(business_id="alfa", name=name, days=week,
                                        service_ids=[services[i].id for i in offered])
            session.add(people[name])
        session.flush()
        for title, body in DOCUMENTS:
            session.add(KnowledgeDocument(business_id="alfa", title=title, body=body, published=True))
        offset = 0
        for days, clock, person, index, customer, contact in BOOKINGS:
            day = today + timedelta(days=days + offset)
            while day.weekday() == 6:  # nunca en domingo
                offset += 1
                day = today + timedelta(days=days + offset)
            hour, minute = map(int, clock.split(":"))
            start = datetime.combine(day, time(hour, minute), LOCAL).astimezone(timezone.utc)
            session.add(Appointment(business_id="alfa", customer_name=customer, customer_contact=contact,
                                    starts_at=start, ends_at=start + timedelta(minutes=services[index].duration_minutes),
                                    professional_id=people[person].id, service_id=services[index].id))
    engine.dispose()
    print("Base de demostración del video lista:", DB)


if __name__ == "__main__":
    main()
