# Lección 01 — API multiempresa, de cero

## ROCE (Resultado, Observación, Concepto, Ejercicio)

**Resultado:** una API que gestiona reservas de dos negocios de demostración sin mezclarlas.
**Observación:** una misma ruta `/services` devuelve resultados distintos según la empresa autenticada.
**Concepto:** `tenant` = empresa cliente de tu SaaS; `tenant isolation` = cada empresa accede únicamente a sus datos. **Nunca** confíes en un `tenant_id` que envía el usuario sin autorización.
**Ejercicio:** ejecuta las pruebas, agrega un servicio de demostración al negocio Alfa y comprueba que no aparece en Beta.

## Glosario

- **Frontend:** interfaz que ve una persona; más adelante React.
- **Backend:** servidor que aplica reglas y entrega datos; aquí FastAPI.
- **API REST:** rutas HTTP que permiten intercambiar datos entre aplicaciones.
- **Endpoint:** una ruta (`GET /services`) y su comportamiento.
- **HTTP 401:** credenciales ausentes o incorrectas.
- **HTTP 409:** conflicto, como una cita duplicada.
- **PostgreSQL:** futura base de datos transaccional de producción.
- **SQLite:** base de datos pequeña para practicar localmente.
- **RAG:** recuperar fragmentos relevantes de documentos antes de responder con un modelo.
- **LLM:** modelo de lenguaje; todavía no está integrado.
- **LangGraph:** framework de orquestación que modela un proceso como estados, nodos y transiciones; todavía no está instalado.
- **Nodo:** función que realiza una tarea dentro de un grafo.
- **Arista:** transición que conecta nodos; puede depender de una condición.
- **Estado:** datos acumulados del proceso, como intención, fecha y confirmación.
- **n8n:** herramienta de automatización e integraciones; futura etapa.

## Qué sucede cuando reservas

1. Cliente envía una solicitud HTTP al backend.
2. La dependencia `current_business()` determina la empresa según la clave demo.
3. Pydantic valida el cuerpo y obliga a enviar zona horaria.
4. SQLite comprueba el índice único `(business_id, starts_at)`.
5. Devuelve HTTP 201 si creó la reserva o 409 si ese horario estaba ocupado.

## Próxima lección: el primer grafo

Se implementará un flujo básico `interpretar solicitud -> consultar disponibilidad -> pedir confirmación -> reservar`. Primero con pasos deterministas y pruebas; después agregaremos un LLM, herramientas y RAG. Un LLM nunca debe reservar sin validación y consentimiento.

## Límites de esta versión

No hay interfaz React, autenticación real, política de horarios de apertura, duración de servicios, normalización de instantes UTC, ni pagos. No usar con clientes reales.
