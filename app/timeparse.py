"""Reglas para leer el día y la hora de un mensaje ya normalizado (minúsculas, sin tildes).

Funciones puras: reciben el texto y la fecha de hoy, no consultan reloj ni base de datos.
Cada resultado indica si el patrón es inequívoco (`sure`). Cuando no lo es, el chat puede
dejar que el LLM lo precise, siempre dentro de los límites que estas reglas sí conocen.
"""
import re
from dataclasses import dataclass
from datetime import date, timedelta

WEEKDAYS = (("lunes", "monday"), ("martes", "tuesday"), ("miercoles", "wednesday"), ("jueves", "thursday"),
            ("viernes", "friday"), ("sabado", "saturday"), ("domingo", "sunday"))

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# "por la mañana", "a media mañana", "esta mañana": franja del día, no el día siguiente.
MORNING_SLOT = re.compile(r"(?<!\w)(?:las?|esta|media|buena)\s+mananas?(?!\w)")
NEXT_WEEK = re.compile(r"(?<!\w)(?:semana\s+(?:que\s+viene|proxima|entrante|siguiente)"
                       r"|(?:proxima|siguiente|otra)\s+semana|next\s+week)(?!\w)")
CLOCK = re.compile(r"(?:\ba las?\s+|\bat\s+|^)(\d{1,2})(?::([0-5]\d))?\s*(a\.?m\.?|p\.?m\.?)?(?![\w:-])")
AFTERNOON = re.compile(r"\s*(?:(?:de|por|en)\s+la\s+(?:tarde|noche)|in\s+the\s+(?:afternoon|evening)|at\s+night)(?!\w)")
MORNING = re.compile(r"\s*(?:(?:de|por|en)\s+la\s+manana|in\s+the\s+morning)(?!\w)")


@dataclass(frozen=True)
class DayMatch:
    value: date | None = None
    sure: bool = False              # fecha ISO, hoy, mañana o pasado mañana
    weekday: int | None = None      # día de la semana nombrado (0 = lunes)
    next_week: bool = False         # "la semana que viene"

    @property
    def mentioned(self) -> bool:
        return self.value is not None or self.next_week


@dataclass(frozen=True)
class ClockMatch:
    value: str | None = None
    sure: bool = False              # False: hora de 1 a 7 sin "am/pm" ni "de la tarde"

    @property
    def alternative(self) -> str | None:
        """La misma hora doce horas después: única corrección que se acepta del LLM."""
        if self.value is None or self.sure:
            return None
        return f"{int(self.value[:2]) + 12:02d}{self.value[2:]}"


def has(text: str, word: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text) is not None


def next_week_start(today: date) -> date:
    """Lunes de la semana siguiente a la de hoy."""
    return today + timedelta(days=7 - today.weekday())


def find_day(text: str, today: date) -> DayMatch:
    """Lanza ValueError si el mensaje trae una fecha AAAA-MM-DD imposible."""
    iso = ISO_DATE.search(text)
    if iso:
        return DayMatch(date.fromisoformat(iso[0]), sure=True)
    if has(text, "pasado manana") or has(text, "day after tomorrow"):
        return DayMatch(today + timedelta(days=2), sure=True)
    if has(MORNING_SLOT.sub(" ", text), "manana") or has(text, "tomorrow"):
        return DayMatch(today + timedelta(days=1), sure=True)
    if has(text, "hoy") or has(text, "today"):
        return DayMatch(today, sure=True)
    next_week = NEXT_WEEK.search(text) is not None
    for index, names in enumerate(WEEKDAYS):
        if any(has(text, name) for name in names):
            if next_week:
                day = next_week_start(today) + timedelta(days=index)
            else:
                # El mismo día de la semana que hoy significa el siguiente: para hoy existe "hoy".
                day = today + timedelta(days=(index - today.weekday()) % 7 or 7)
            return DayMatch(day, weekday=index, next_week=next_week)
    return DayMatch(next_week=next_week)


def find_clock(text: str) -> ClockMatch:
    match = CLOCK.search(text)
    if not match:
        return ClockMatch()
    hour, minutes, suffix = int(match[1]), match[2] or "00", (match[3] or "").replace(".", "")
    rest = text[match.end():]
    afternoon, morning = AFTERNOON.match(rest), MORNING.match(rest)
    sure = bool(suffix or afternoon or morning) or not 1 <= hour <= 7
    if suffix and 1 <= hour <= 12:
        hour = hour % 12 + (12 if suffix == "pm" else 0)
    elif afternoon and 1 <= hour <= 11:
        hour += 12
    elif afternoon and hour == 12 and "tarde" not in afternoon[0] and "afternoon" not in afternoon[0]:
        hour = 0  # "12 de la noche"
    if hour > 23:
        return ClockMatch()
    return ClockMatch(f"{hour:02d}:{minutes}", sure)

