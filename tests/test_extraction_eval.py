"""El set de evaluación de extracción es coherente y las reglas no estropean un LLM correcto.

La medición con un modelo real se hace con scripts/eval_llm.py y no forma parte de la suite.
"""
import re
from datetime import date

from scripts.eval_llm import FIELDS, SKIP, evaluate, load_cases, render

DATA, TODAY = load_cases()
CASES, CATALOG = DATA["cases"], DATA["catalog"]


def test_cases_are_well_formed():
    services = {s["id"] for s in CATALOG["services"]}
    team = {p["id"] for p in CATALOG["team"]}
    assert len(CASES) >= 40 and len({c["id"] for c in CASES}) == len(CASES)
    assert {c["language"] for c in CASES} == {"es", "en"}
    for case in CASES:
        expected = case["expected"]
        assert set(expected) <= set(FIELDS) and len(case["message"]) <= 350, case["id"]
        assert expected.get("service_id") in services | {None}, case["id"]
        assert expected.get("professional_id") in team | {None}, case["id"]
        if expected.get("day"):
            assert date.fromisoformat(expected["day"]) >= TODAY, case["id"]
        if expected.get("clock") not in (None, SKIP):
            assert re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", expected["clock"]), case["id"]


def test_rules_only_baseline_does_not_regress():
    """Piso medido al crear el set; si una regla nueva lo baja, la suite avisa."""
    rules = evaluate(CASES, CATALOG, TODAY)["rules"]
    assert rules["fields"]["professional_id"][0] == 40
    assert rules["fields"]["day"][0] >= 37
    assert rules["fields"]["clock"][0] >= 34
    assert rules["fields"]["service_id"][0] >= 29
    assert rules["cases"][0] >= 21
    # Las reglas pueden quedarse cortas, pero nunca inventan: ningún campo esperado vacío sale relleno.
    assert not [miss for miss in rules["misses"] if miss[2] is None]


def test_a_correct_llm_is_never_made_worse_by_the_rules():
    """Con un LLM simulado que acierta siempre, reglas + LLM debe acertar todos los casos."""
    def oracle(case):
        hints = {field: value for field, value in case["expected"].items() if value != SKIP}
        if "day" in hints:
            hints["day"] = date.fromisoformat(hints["day"])
        return hints, False, 0.0
    report = evaluate(CASES, CATALOG, TODAY, oracle)
    assert report["combined"]["misses"] == []
    assert report["combined"]["cases"] == [len(CASES), len(CASES)]
    assert "Reglas + LLM" in render(report, "simulado", len(CASES))


def test_a_failing_llm_leaves_the_rules_result():
    report = evaluate(CASES, CATALOG, TODAY, lambda case: ({}, True, 0.0))
    assert report["failures"] == len(CASES)
    assert report["combined"]["cases"] == report["rules"]["cases"]
