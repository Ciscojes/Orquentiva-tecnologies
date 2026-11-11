# ORQENTIVA Technologies

MVP académico de una aplicación web para gestionar servicios, profesionales y reservas de varios negocios. Incluye un asistente conversacional con LangGraph que puede apoyarse en un LLM para entender lenguaje libre, y consultas de políticas con referencias a documentos publicados.

## Problema y objetivo

Los pequeños negocios necesitan atender consultas y coordinar citas sin mezclar información de sus clientes. ORQENTIVA centraliza catálogo, horarios y reservas. El caso de demostración utiliza dos barberías ficticias: Alfa y Beta. El proyecto demuestra desarrollo full stack, control de acceso y verificación de operaciones mediante pruebas. No se han medido mejoras de ventas o productividad en negocios reales.

## Funcionalidades implementadas

- Página comercial ES/EN y formulario de contacto que guarda solicitudes de posibles clientes.
- Inicio y cierre de sesión, roles super_admin y business_admin, sesiones revocables y contraseñas con Argon2.
- Administrador: crear y activar negocios, habilitar agenda y crear cuentas de negocio.
- Cliente: gestionar servicios, duración, horarios, profesionales y documentos. Consultar sus reservas.
- Enlace público por negocio con disponibilidad y confirmación de citas. El cliente deja un teléfono o correo de contacto, que el negocio ve en su agenda; por WhatsApp se guarda su número automáticamente.
- Chat con LangGraph: solicita datos, consulta disponibilidad y prepara una propuesta. La interfaz solicita confirmación y llama al backend para guardar la reserva.
- Interpretación opcional con LLM (API compatible con OpenAI): entiende frases como «la semana que viene a media mañana con la chica de siempre». El modelo solo propone campos; el servidor los valida contra el catálogo y nunca reserva sin confirmación.
- Consultas de políticas con RAG: recupera los párrafos publicados del negocio y, con el LLM activo, redacta la respuesta citando título y número de párrafo. Sin LLM devuelve el párrafo literal. Ante evidencia insuficiente, pide consultar al negocio.
- Reintentos idempotentes, control de solapamientos y separación de datos por negocio.
- Piloto de WhatsApp (webhook de Meta con firma verificada y worker de procesamiento) preparado para un número de prueba. La conexión con Meta está pendiente y no está publicada. Ver [configuración del piloto](docs/WHATSAPP_PILOT.md) y [SPEC-013](specs/013-whatsapp-booking/spec.md).

### Cómo usa la IA el chat

El grafo de LangGraph tiene tres nodos: `understand` (LLM opcional), `interpret` (reglas) y `availability` (agenda). Las reglas mandan cuando el patrón es inequívoco (fecha AAAA-MM-DD, «hoy», «mañana», hora con «am/pm» o «de la tarde», nombre completo de un servicio) y el LLM completa lo que no reconocen. En lo dudoso el LLM precisa dentro de límites que las reglas sí conocen: con «el viernes» puede cambiar de semana pero no de día, con «la semana que viene» solo vale un día de esa semana, y con «a las 4» solo elige entre las 04:00 y las 16:00. Cada campo propuesto por el modelo se valida contra el catálogo del negocio; si el LLM falla, tarda más de 8 s o se supera el límite de 20 llamadas por IP y minuto, el chat sigue solo con reglas. Detalle en [SPEC-014](specs/014-llm-interpretation/spec.md).

Las preguntas sobre el negocio usan RAG ([SPEC-015](specs/015-rag/spec.md)):

1. **Recuperación:** búsqueda léxica en los párrafos publicados del negocio. Si no encuentra nada y los documentos caben en 6 000 caracteres, el LLM los recibe todos para entender sinónimos («¿me regresan la plata si falto?»).
2. **Generación:** el LLM redacta una respuesta breve usando solo esos párrafos e indica cuáles usó.
3. **Validación:** se descarta la respuesta si cita párrafos que no recibió o si contiene cifras que no aparecen en ellos. En ese caso, o sin LLM, se muestra el párrafo literal.

El chat marca las respuestas generadas («Respuesta redactada con IA a partir de:») y siempre muestra las fuentes.

Para activarlo, escribir la configuración una sola vez en el archivo `.env` de la raíz del proyecto (no se sube a git):

```dotenv
# Ejemplo con Groq (plan gratuito, probado con openai/gpt-oss-20b)
LLM_API_KEY=tu-clave
LLM_MODEL=openai/gpt-oss-20b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

La API lee esas variables al arrancar, también en la demo con SQLite, y lo indica en su terminal: `LLM activo: modelo ... en ...` o `LLM inactivo: el chat usa solo reglas (...)`. Una variable definida en la terminal (`$env:LLM_MODEL = "..."`) tiene prioridad sobre el archivo. `python scripts/check_llm.py` comprueba la clave y lista los modelos si falla. Las pruebas nunca usan la clave real.

Sin estas variables el comportamiento es determinista y la consulta de políticas devuelve párrafos literales. La recuperación no usa embeddings: los documentos de un negocio son pocos y así no hay costos ni dependencias extra. El proyecto se desarrolló con especificaciones por incremento (`specs/`) y asistentes de IA como apoyo de ingeniería.

## Tecnologías

| Capa | Tecnología y finalidad |
| --- | --- |
| Interfaz | React, TypeScript y Vite para página, paneles y chat |
| API | Python y FastAPI, validación con Pydantic |
| Datos | SQLAlchemy, PostgreSQL y migraciones Alembic |
| Conversación | LangGraph, reglas de interpretación y LLM opcional vía API compatible con OpenAI (httpx) |
| Autenticación | pwdlib/Argon2, sesiones opacas en cookie HttpOnly |
| Verificación | pytest, TestClient, PostgreSQL temporal, TypeScript, oxlint y GitHub Actions |
| Despliegue | Docker: una imagen con API y frontend en el mismo origen |

Las versiones de frontend se resuelven con frontend/package-lock.json. requirements.txt acota las dependencias Python y fija LangGraph; requirements-dev.txt añade pytest. Python 3.13 en local y en GitHub Actions. La demostración local opcional usa SQLite para facilitar la revisión, mientras que el desarrollo habitual usa PostgreSQL.

## Instalación y ejecución

Requisitos: Python 3.13, Node.js/npm compatible con el proyecto y, para el modo PostgreSQL, PostgreSQL 17. Descargar o clonar el código y abrir PowerShell en su raíz.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Set-Location frontend
npm ci
Set-Location ..
```

### Demostración aislada para el evaluador

```powershell
python scripts/prepare_tfm_demo.py
.\scripts\start_tfm_demo.ps1 -Component api
```

En otra terminal, desde la raíz:

```powershell
.\scripts\start_tfm_demo.ps1 -Component web
```

Abrir http://127.0.0.1:5179/#access (también se admite http://localhost:5179/#access). Mantener abiertas las dos terminales: `api` ejecuta el backend y el LLM configurado en `.env`; `web` sirve la interfaz. Usar el mismo hostname durante la sesión: las cookies de localhost y 127.0.0.1 son independientes. El backend usa el puerto 8002. El preparador crea tfm-demo.sqlite3 con migraciones, dos negocios, usuarios ficticios, profesionales, horarios y políticas. Si la base ya existe, se detiene sin sobrescribirla. No lee .env ni modifica la base habitual.

Los usuarios de prueba están en la sección [Usuarios de prueba](#usuarios-de-prueba).

### Desarrollo con PostgreSQL

Crear una base vacía dedicada a ORQENTIVA y configurar DATABASE_URL como variable de entorno, o POSTGRES_PASSWORD en un .env local según app/database.py. No subir ese archivo. DATABASE_URL prevalece sobre .env. La configuración predeterminada de desarrollo utiliza usuario orqentiva, base orqentiva_db, host 127.0.0.1 y puerto 5434.

```powershell
python -m alembic upgrade head
python seed.py
python scripts/create_user.py --email admin@example.com --role super_admin
python scripts/create_user.py --email alfa@example.com --role business_admin --business-id alfa
python scripts/create_user.py --email beta@example.com --role business_admin --business-id beta
.\scripts\start_development.ps1 -Component api
```

Las contraseñas se solicitan sin mostrarlas. En otra terminal ejecutar .\scripts\start_development.ps1 -Component web y abrir http://127.0.0.1:5178/#access. El backend habitual usa 8001. Seed crea catálogo inicial sin duración y sin profesionales: configurar estos datos desde el panel antes de reservar. Las cuentas del modo demostración no se crean en PostgreSQL automáticamente.

## Estructura

```text
app/                    API, modelos, seguridad y reglas de fecha y hora
  routes/               Solo HTTP: autenticación, paneles, reservas, chat y documentos
  services/             Lógica: agenda, chat (grafo), RAG y límites de uso
evals/                  Frases de evaluación de la extracción del chat
frontend/src/           Interfaz React y estilos
alembic/versions/       Historial de migraciones
scripts/                Preparación, arranque y validación
tests/                  Pruebas aisladas y 30 escenarios de aceptación
specs/                  Especificaciones y decisiones por incremento
docs/                   Arquitectura, operación y resultados
seed.py                 Dos negocios y catálogo ficticio inicial
requirements.txt        Dependencias de la aplicación
requirements-dev.txt    Las anteriores más pytest
Dockerfile              Imagen de despliegue (API + frontend)
```

## Pruebas y evidencia

```powershell
python -m pytest -q
python scripts/verify_postgres.py --postgres-bin "C:\Program Files\PostgreSQL\17\bin"
Set-Location frontend
npm run build
npm run lint
```

Las pruebas pytest utilizan SQLite temporal. verify_postgres inicia un PostgreSQL temporal limitado a este equipo, valida migraciones y flujos, y lo detiene. No utiliza .env ni la base habitual.

Resultado consolidado: 240 pruebas aprobadas, incluidas 30 de aceptación, las del LLM y del RAG con el modelo simulado, las reglas de fecha y hora con fecha fija y la vigilancia de capas. También se comprobó PostgreSQL temporal y la compilación y lint del frontend. Consulte la [verificación consolidada](docs/VERIFICACION_TFM.md) para el estado vigente y la [evaluación inicial](docs/evaluation-012/informe-evaluacion.md) como evidencia histórica.

### Evaluación de la extracción del chat

`evals/extraction_cases.json` contiene 40 frases en español e inglés con el resultado esperado por campo. `scripts/eval_llm.py` mide precisión por campo, casos completos, llamadas fallidas y latencia, y compara solo reglas, la propuesta del LLM y reglas + LLM ([SPEC-017](specs/017-date-rules-and-extraction-eval/spec.md)).

```powershell
python scripts/eval_llm.py --rules-only                                        # sin clave ni red
python scripts/eval_llm.py --delay 2 --report docs/evaluation-017/informe-extraccion.md   # con LLM_API_KEY y LLM_MODEL
```

Medición solo con reglas: 21 de 40 frases completas (día 37/40, hora 34/38, servicio 29/40); ver [informe](docs/evaluation-017/informe-solo-reglas.md). La medición real con `openai/gpt-oss-20b` obtuvo 39/40 casos completos con reglas + LLM, 0/40 llamadas fallidas y latencia mediana de 1,46 s; ver [informe de extracción](docs/evaluation-017/informe-extraccion.md). Es una ejecución sobre casos ficticios conocidos, no una garantía general de exactitud.

## Arquitectura, seguridad y límites

Consulte [Arquitectura](docs/ARQUITECTURA_TFM.md). Las autorizaciones se comprueban en la API. Las fechas se guardan en UTC y la agenda se presenta en horario de Costa Rica. No hay registro público, recuperación de contraseña ni MFA. Los límites de uso se mantienen en memoria por proceso. La publicación exige HTTPS y configuración de origen; ver [Despliegue](#despliegue). La demo con contraseña conocida es exclusivamente local y contiene datos ficticios.

WhatsApp queda como piloto sin conectar. No se incluyen voz, pagos, suscripciones ni n8n. El LLM propone campos para las reservas y puede redactar respuestas documentales con citas verificadas (SPEC-015). No confirma reservas ni escribe en la base de datos. La evaluación es de un MVP y no acredita disponibilidad o seguridad de producción.

## Despliegue

El `Dockerfile` crea una sola imagen: compila el frontend, lo sirve desde FastAPI en el mismo origen que la API, aplica las migraciones al arrancar y escucha en el puerto `PORT` (8000 por defecto). Sirve para cualquier proveedor de contenedores (Render, Railway, Fly.io).

```powershell
docker build -t orqentiva .
docker run --rm -p 8000:8000 -e DATABASE_URL="sqlite:////tmp/orqentiva.sqlite3" `
  -e AUTH_ALLOWED_ORIGINS="http://localhost:8000" -e AUTH_COOKIE_SECURE=false orqentiva
```

| Variable | Valor en producción |
| --- | --- |
| DATABASE_URL | PostgreSQL dedicada (`postgresql+psycopg://usuario:clave@host:5432/orqentiva_db`) |
| AUTH_ALLOWED_ORIGINS | Origen HTTPS exacto de la publicación |
| AUTH_COOKIE_SECURE | `true` |
| LLM_API_KEY, LLM_MODEL, LLM_BASE_URL | Opcionales: activan la interpretación con LLM |

Los límites de peticiones viven en memoria, así que la publicación usa una sola instancia. Las cuentas publicadas deben ser ficticias y distintas de las de la demo local.

## Usuarios de prueba

Disponibles solo en la demostración local aislada (`tfm-demo.sqlite3`), con datos ficticios.

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Administrador de plataforma | admin@example.com | Orqentiva-Demo-2026! |
| Barbería Alfa | alfa@example.com | Orqentiva-Demo-2026! |
| Barbería Beta | beta@example.com | Orqentiva-Demo-2026! |

Reservas públicas: http://127.0.0.1:5179/#reservar/alfa y http://127.0.0.1:5179/#reservar/beta

## Enlaces del proyecto

- Repositorio: https://github.com/Ciscojes/orqentiva-technologies
- Presentación: _pendiente de añadir el enlace público_
- Vídeo: _pendiente de añadir_
- Despliegue: _pendiente de añadir la URL_ (ver [Despliegue](#despliegue))
