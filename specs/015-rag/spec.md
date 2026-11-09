# SPEC-015 — Consultas con RAG

## Objetivo
Responder preguntas sobre las políticas del negocio en lenguaje natural, sin inventar datos.

## Alcance
- Recuperación léxica de párrafos publicados del negocio (la de SPEC-011); si no hay coincidencias y el total cabe en 6 000 caracteres, se usan todos los párrafos del negocio.
- Generación con el LLM de SPEC-014: respuesta de hasta 700 caracteres basada solo en los párrafos recibidos, con los ids usados.
- Validación en el servidor: citas a párrafos recibidos, al menos una cita, y ninguna cifra que no esté en los párrafos citados.
- Respaldo extractivo: sin LLM, con error, con respuesta rechazada o con dudas del modelo cuando la búsqueda léxica sí encontró evidencia, se devuelve el párrafo literal.
- Aislamiento: el modelo solo recibe párrafos publicados del negocio del enlace.
- La interfaz indica «Respuesta redactada con IA a partir de:» y muestra las fuentes.

## Fuera de alcance
Embeddings, base vectorial y memoria de conversación.

## Verificación
`tests/test_rag.py` (8 pruebas con el modelo simulado) y `scripts/check_llm.py` con el proveedor real.
