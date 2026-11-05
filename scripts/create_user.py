"""Crear una cuenta explícitamente, sin contraseñas en argumentos ni salida."""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=["super_admin", "business_admin"])
    parser.add_argument("--business-id")
    args = parser.parse_args()
    password = getpass.getpass("Contraseña (12–128 caracteres): ")
    if not 12 <= len(password) <= 128:
        print("La contraseña debe tener entre 12 y 128 caracteres. No se creó la cuenta.")
        return 1
    if not password.strip():
        print("La contraseña no puede contener solamente espacios. No se creó la cuenta.")
        return 1
    if password != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.")
        return 1
    from pydantic import ValidationError
    from sqlalchemy.exc import SQLAlchemyError
    from app.auth import UserCreate, create_user
    from app.database import SessionLocal, engine
    try:
        payload = UserCreate(email=args.email, password=password, role=args.role, business_id=args.business_id)
        with SessionLocal.begin() as session:
            create_user(session, payload)
        print("Cuenta creada correctamente. No se modificaron cuentas existentes.")
        return 0
    except ValidationError as exc:
        # Nunca imprimir exc ni sus inputs: pueden contener la contraseña.
        fields = {error["loc"][0] for error in exc.errors(include_input=False, include_context=False) if error["loc"]}
        if "email" in fields:
            print("El correo electrónico no tiene un formato válido.")
        elif "password" in fields:
            print("La contraseña debe tener entre 12 y 128 caracteres.")
        else:
            print("Revisa rol y empresa: super_admin no lleva --business-id; business_admin lo requiere.")
    except ValueError as exc:
        print(str(exc))  # Mensajes controlados de create_user, sin datos sensibles.
    except SQLAlchemyError:
        print("No se pudo crear la cuenta. Revisa conexión y migraciones; no se muestran datos internos.")
    finally:
        engine.dispose()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
