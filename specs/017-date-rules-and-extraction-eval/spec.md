# SPEC-017 — Reglas de fecha y hora, prioridad frente al LLM y evaluación de extracción

## Objetivo
Corregir errores de interpretación de fechas del chat, definir cuándo decide el LLM y medir la extracción con un conjunto fijo de frases.

## Problemas corregidos
- «por la mañana», «a media mañana» o «de la mañana» se leían como el día siguiente, incluso con otro día nombrado («el viernes por la mañana»).
- El mismo día de la semana que hoy devolvía hoy.
- «a las 4 de la tarde» se guardaba como 04:00.
- Como las reglas siempre ganaban, el LLM no podía corregir ninguno de estos casos.

## Alcance
- `app/timeparse.py`: reglas puras de día y hora; reciben el texto y la fecha de hoy.
- El mismo día de la semana que hoy significa el de la semana siguiente; para hoy existe «hoy».
- «La semana que viene» con día concreto usa ese día de la semana siguiente; sin día, el chat pregunta.
- Prioridad:
  - Mandan las reglas con fecha AAAA-MM-DD, «hoy», «mañana», «pasado mañana», hora con «am/pm» o franja y nombre completo de un servicio.
  - Con un día de la semana, el LLM puede proponer una semana posterior («viernes 20») pero no otro día ni una fecha anterior.
  - Con «la semana que viene» sin día, solo se acepta un día de esa semana.
  - Una hora de 1 a 7 sin «am/pm» ni franja es dudosa: el LLM solo elige entre esa hora y doce horas después.
  - Con coincidencia parcial o ambigua de servicio decide el LLM, ya validado contra el catálogo.
- Sin LLM se aplican solo las reglas. La confirmación explícita y la revalidación de la agenda no cambian.
- `evals/extraction_cases.json` y `scripts/eval_llm.py`: 40 frases ES/EN con fecha fija; precisión por campo, casos completos, llamadas fallidas y latencia.
- Capa `app/services/`: las rutas quedan solo con HTTP y no se importan entre sí.
- `app/database.py` informa la falta de configuración al conectar, no al importar. `requirements-dev.txt` separa pytest.

## Fuera de alcance
Fechas escritas con número de día y mes sin LLM («el 25 de noviembre»), horas en palabras sin LLM, zona horaria por negocio, límite de uso compartido entre instancias y pruebas de navegador.

## Verificación
- `tests/test_timeparse.py`: reglas con fecha fija y regresiones en el chat.
- `tests/test_llm.py`: desacuerdos entre reglas y LLM con el modelo simulado.
- `tests/test_extraction_eval.py`: coherencia del conjunto, piso de las reglas y garantía de que las reglas no empeoran a un LLM que acierta.
- `tests/test_architecture.py`: dependencias entre capas.
- Con el mismo conjunto, el código anterior resolvía 15 de 40 frases completas solo con reglas (día 32/40, hora 29/38); el actual, 21 de 40 (día 37/40, hora 34/38).
- La medición con un modelo real no se ha ejecutado: requiere clave y se lanza con `scripts/eval_llm.py`.
