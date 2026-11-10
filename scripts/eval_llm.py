"""Mide cuánto entiende el chat de reservas: solo reglas frente a reglas + LLM.

    python scripts/eval_llm.py --rules-only          # sin clave ni red
    python scripts/eval_llm.py --report docs/evaluation-017/informe-extraccion.md

Usa evals/extraction_cases.json: frases con el resultado esperado por campo y una fecha
fija, para que "mañana" o "el viernes" signifiquen lo mismo en cada ejecución. Con LLM
necesita LLM_API_KEY y LLM_MODEL (y LLM_BASE_URL si no es OpenAI); cada frase es una
llamada real al proveedor. No toca la base de datos ni crea reservas.
"""
import argparse
import json
import os
import statistics
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import llm  # noqa: E402
from app.routes.booking_chat import Turn, interpret  # noqa: E402

CASES_FILE = ROOT / "evals" / "extraction_cases.json"
FIELDS = ("service_id", "professional_id", "day", "clock", "name")
LABELS = {"service_id": "Servicio", "professional_id": "Profesional", "day": "Día", "clock": "Hora", "name": "Nombre"}
SKIP = "*"


def load_cases(path=CASES_FILE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data, date.fromisoformat(data["today"])


def plain(value):
    """Valor comparable: fechas como texto, nombres sin tildes ni mayúsculas, vacío como None."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = unicodedata.normalize("NFD", value.strip().casefold())
        return "".join(c for c in text if not unicodedata.combining(c))
    return value


def run_rules(case, catalog, today, hints=None):
    """Borrador final del nodo de reglas, con o sin propuesta del LLM."""
    state = {"turn": Turn(message=case["message"], language=case["language"]), "menu": catalog,
             "hints": hints or {}, "today": today}
    draft = interpret(state)["draft"]
    return {field: getattr(draft, field) for field in FIELDS}


def score(cases, results):
    """Aciertos por campo y por caso. Un campo esperado vacío cuenta: detecta datos inventados."""
    fields = {field: [0, 0] for field in FIELDS}
    whole, misses = 0, []
    for case, result in zip(cases, results):
        correct = True
        for field in FIELDS:
            expected = case["expected"].get(field)
            if expected == SKIP:
                continue
            fields[field][1] += 1
            if plain(result.get(field)) == plain(expected):
                fields[field][0] += 1
            else:
                correct = False
                misses.append((case["id"], field, expected, result.get(field)))
        whole += correct
    return {"fields": fields, "cases": [whole, len(cases)], "misses": misses}


def evaluate(cases, catalog, today, extract=None, delay=0.0):
    """extract(case) -> (hints, falló, segundos). Sin extract solo se miden las reglas."""
    rules = [run_rules(case, catalog, today) for case in cases]
    report = {"rules": score(cases, rules)}
    if extract is None:
        return report
    proposals, combined, seconds, failures = [], [], [], 0
    for index, case in enumerate(cases):
        if index and delay:
            time.sleep(delay)
        hints, failed, elapsed = extract(case)
        failures += failed
        seconds.append(elapsed)
        proposals.append(hints)
        combined.append(run_rules(case, catalog, today, hints))
    report.update(llm=score(cases, proposals), combined=score(cases, combined),
                  failures=failures, seconds=seconds)
    return report


def real_extract(catalog, today):
    """Llama al modelo configurado y distingue "no entendió nada" de "la llamada falló"."""
    original = llm.request_json
    outcome = {}

    def tracked(system, context):
        data = original(system, context)
        outcome["failed"] = data is None
        return data

    llm.request_json = tracked

    def extract(case):
        outcome["failed"] = False
        start = time.perf_counter()
        hints = llm.extract(case["message"], catalog, today, case["language"])
        return hints, outcome["failed"], time.perf_counter() - start
    return extract


def percent(pair):
    return f"{pair[0]}/{pair[1]} ({100 * pair[0] / pair[1]:.0f} %)" if pair[1] else "—"


def render(report, model, total):
    modes = [("rules", "Solo reglas")]
    if "combined" in report:
        modes += [("llm", "Solo propuesta del LLM"), ("combined", "Reglas + LLM")]
    lines = ["# Evaluación de extracción del chat de reservas", "",
             f"Casos: {total} · modelo: {model or 'ninguno (solo reglas)'} · fecha fija de los casos: ver evals/extraction_cases.json", "",
             "| Campo | " + " | ".join(label for _, label in modes) + " |",
             "| --- |" + " ---: |" * len(modes)]
    for field in FIELDS:
        lines.append(f"| {LABELS[field]} | " + " | ".join(percent(report[key]["fields"][field]) for key, _ in modes) + " |")
    lines.append("| **Caso completo** | " + " | ".join(percent(report[key]["cases"]) for key, _ in modes) + " |")
    if "combined" in report:
        seconds = sorted(report["seconds"])
        p95 = seconds[min(len(seconds) - 1, round(0.95 * (len(seconds) - 1)))]
        lines += ["", f"Llamadas fallidas (el chat siguió solo con reglas): {report['failures']}/{total}.",
                  f"Latencia de la llamada al LLM: mediana {statistics.median(seconds):.2f} s · p95 {p95:.2f} s · máxima {seconds[-1]:.2f} s."]
    final = report.get("combined", report["rules"])
    lines += ["", f"## Fallos de {'reglas + LLM' if 'combined' in report else 'solo reglas'}", ""]
    if final["misses"]:
        lines += ["| Caso | Campo | Esperado | Obtenido |", "| --- | --- | --- | --- |"]
        lines += [f"| {case} | {LABELS[field]} | {expected or 'vacío'} | {got or 'vacío'} |" for case, field, expected, got in final["misses"]]
    else:
        lines.append("Ninguno.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--rules-only", action="store_true", help="no llama al LLM")
    parser.add_argument("--delay", type=float, default=0.0, help="segundos entre llamadas (límites del plan gratuito)")
    parser.add_argument("--report", type=Path, help="guarda el informe en Markdown")
    args = parser.parse_args()
    data, today = load_cases()
    cases, catalog = data["cases"], data["catalog"]
    extract = None
    if not args.rules_only:
        if not llm.enabled():
            raise SystemExit("Faltan LLM_API_KEY o LLM_MODEL. Usa --rules-only para medir solo las reglas.")
        extract = real_extract(catalog, today)
    report = evaluate(cases, catalog, today, extract, args.delay)
    text = render(report, None if args.rules_only else os.environ["LLM_MODEL"], len(cases))
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
        print(f"Informe guardado en {args.report}")


if __name__ == "__main__":
    main()
