"""Local pilot entrypoint. Exposes only Meta's webhook, never demo administration."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "webhook", "worker"])
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.action == "prepare":
        from scripts import prepare_tfm_demo as demo
        demo.DB = ROOT / "whatsapp-demo.sqlite3"
        demo.main()
        return
    from dotenv import load_dotenv
    config = ROOT / ".env.whatsapp"
    if not config.exists():
        raise SystemExit("Primero configura .env.whatsapp a partir de whatsapp.env.example")
    load_dotenv(config, override=True)
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("Falta DATABASE_URL en la configuración del piloto")
    if args.action == "webhook":
        import uvicorn
        from fastapi import FastAPI
        from app.routes.whatsapp import router
        app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        app.include_router(router)
        uvicorn.run(app, host="127.0.0.1", port=8013)
    else:
        from app.whatsapp_worker import main as worker_main
        sys.argv = [sys.argv[0]]
        worker_main()


if __name__ == "__main__":
    main()
