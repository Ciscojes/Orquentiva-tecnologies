
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Business, Service


DEMO_BUSINESSES = [
    ("alfa", "Barbería Alfa", "Corte clásico", 5000),
    ("beta", "Barbería Beta", "Corte premium", 8500),
]


def seed_database():
    with SessionLocal.begin() as session:
        for business_id, name, service_name, price in DEMO_BUSINESSES:
            business = session.get(Business, business_id)

            if business is None:
                session.add(
                    Business(id=business_id, name=name)
                )

            existing_service = session.scalar(
                select(Service).where(
                    Service.business_id == business_id,
                    Service.name == service_name,
                )
            )

            if existing_service is None:
                session.add(
                    Service(
                        business_id=business_id,
                        name=service_name,
                        price_crc=price,
                    )
                )

    print("Datos de demostración preparados correctamente.")


if __name__ == "__main__":
    seed_database()
