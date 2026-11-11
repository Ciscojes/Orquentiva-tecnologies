"""Capas: las rutas no dependen unas de otras y los servicios no conocen las rutas."""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
    return found


def test_routes_do_not_import_other_routes():
    for path in (APP / "routes").glob("*.py"):
        assert not [name for name in imports(path) if name.startswith("app.routes")], path.name


def test_services_and_worker_do_not_import_routes():
    for path in [*(APP / "services").glob("*.py"), APP / "whatsapp_worker.py", APP / "timeparse.py", APP / "llm.py"]:
        assert not [name for name in imports(path) if name.startswith("app.routes")], path.name


def test_chat_logic_does_not_need_a_database_connection():
    """El grafo recibe la sesión como contexto: se puede evaluar sin configurar la base."""
    for name in ("chat.py", "agenda.py", "knowledge.py"):
        assert "app.database" not in imports(APP / "services" / name), name
