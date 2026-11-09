# SPEC-014 — Interpretación opcional con LLM

## Objetivo
Entender solicitudes de reserva en lenguaje libre sin perder las garantías del flujo guiado.

## Alcance
- Nuevo nodo `understand` en el grafo de LangGraph, antes de `interpret`.
- Proveedor configurable con API compatible con OpenAI: `LLM_API_KEY`, `LLM_MODEL` y `LLM_BASE_URL` (opcional).
- El LLM devuelve JSON con servicio, profesional, día, hora y nombre; cada campo se valida por separado contra el catálogo del negocio.
- Las reglas tienen prioridad; el LLM solo completa los campos que ellas no reconocieron.
- El LLM no escribe en la base de datos ni redacta respuestas; la confirmación explícita y la revalidación de la agenda no cambian.
- El mensaje del cliente se envía como texto no confiable; los ids inventados se descartan.
- Límite de 20 llamadas por IP y minuto, tiempo máximo de 8 segundos; ante cualquier fallo el chat sigue solo con reglas.
- Sin configuración, el comportamiento es idéntico al anterior.

## Fuera de alcance
Respuestas generadas por el LLM, embeddings y RAG generativo sobre las políticas (la consulta documental sigue siendo extractiva).

## Verificación
`tests/test_llm.py` simula el modelo: lenguaje libre, campos inventados, fallos de red, JSON inválido, prioridad de reglas y límite de llamadas. No se llama a la red en las pruebas.
