# ORQENTIVA AI

MVP académico de una aplicación web para gestionar servicios, profesionales y reservas de varios negocios. Incluye un asistente conversacional guiado y consultas de políticas con referencias a documentos publicados.

## Problema y objetivo

Los pequeños negocios necesitan atender consultas y coordinar citas sin mezclar información de sus clientes. ORQENTIVA centraliza catálogo, horarios y reservas. El caso de demostración utiliza dos barberías ficticias: Alfa y Beta. El proyecto demuestra desarrollo full stack, control de acceso y verificación de operaciones mediante pruebas. No se han medido mejoras de ventas o productividad en negocios reales.

## Funcionalidades implementadas

- Página comercial ES/EN y formulario de contacto que guarda solicitudes de posibles clientes.
- Inicio y cierre de sesión, roles super_admin y business_admin, sesiones revocables y contraseñas con Argon2.
- Administrador: crear y activar negocios, habilitar agenda y crear cuentas de negocio.
- Cliente: gestionar servicios, duración, horarios, profesionales y documentos. Consultar sus reservas.
- Enlace público por negocio con disponibilidad y confirmación de citas.
- Chat guiado con LangGraph: solicita datos, consulta disponibilidad y prepara una propuesta. La interfaz solicita confirmación y llama al backend para guardar la reserva.
- Recuperación léxica de párrafos publicados por negocio, con título y número de párrafo. Ante evidencia insuficiente, pide consultar al negocio.
- Reintentos idempotentes, control de solapamientos y separación de datos por negocio.

El chat actual no invoca un LLM, no usa embeddings ni genera una respuesta libre a partir de documentos. LangGraph organiza un flujo con reglas. La consulta documental es extractiva. Los nombres históricos «IA» o «RAG» en algunas especificaciones no implican integración de un modelo generativo.

## Tecnologías

| Capa | Tecnología y finalidad |
| --- | --- |
| Interfaz | React, TypeScript y Vite para página, paneles y chat |
| API | Python y FastAPI, validación con Pydantic |
| Datos | SQLAlchemy, PostgreSQL y migraciones Alembic |
| Conversación | LangGraph y reglas de interpretación |
| Autenticación | pwdlib/Argon2, sesiones opacas en cookie HttpOnly |
| Verificación | pytest, TestClient, PostgreSQL temporal, TypeScript y oxlint |

Las versiones de frontend se resuelven con frontend/package-lock.json. requirements.txt acota las dependencias Python y fija LangGraph. La evaluación se ejecutó con Python 3.13.5. La demostración local opcional usa SQLite para facilitar la revisión, mientras que el desarrollo habitual usa PostgreSQL.

## Instalación y ejecución

Requisitos: Python 3.13, Node.js/npm compatible con el proyecto y, para el modo PostgreSQL, PostgreSQL 17. Descargar o clonar el código y abrir PowerShell en su raíz.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
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

Abrir http://127.0.0.1:5179/#access. El backend usa el puerto 8002. El preparador crea tfm-demo.sqlite3 con migraciones, dos negocios, usuarios ficticios, profesionales, horarios y políticas. Si la base ya existe, se detiene sin sobrescribirla. No lee .env ni modifica la base habitual.

Accesos y recorrido: [Guía de demostración](tfm/ACCESO_DEMO.md).

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
app/                    API, modelos, seguridad y agenda
  routes/               Autenticación, paneles, reservas, chat y documentos
frontend/src/           Interfaz React y estilos
alembic/versions/       Historial de migraciones
scripts/                Preparación, arranque y validación
tests/                  Pruebas aisladas y 30 escenarios de aceptación
specs/                  Especificaciones y decisiones por incremento
docs/                   Arquitectura, operación y resultados
tfm/                    Presentación, guion y lista de entrega
seed.py                 Dos negocios y catálogo ficticio inicial
requirements.txt        Dependencias Python
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

Resultado registrado: 137 pruebas aprobadas, incluidas 30 de aceptación. También se comprobó PostgreSQL temporal y la compilación y lint del frontend. Consulte [Verificación de entrega](tfm/VERIFICACION.md) y [Evaluación inicial](docs/evaluation-012/informe-evaluacion.md) para alcance, fechas y límites.

## Arquitectura, seguridad y límites

Consulte [Arquitectura](docs/ARQUITECTURA_TFM.md). Las autorizaciones se comprueban en la API. Las fechas se guardan en UTC y la agenda se presenta en horario de Costa Rica. No hay registro público, recuperación de contraseña ni MFA. Los límites de uso se mantienen en memoria por proceso. La publicación exige HTTPS y configuración de origen/proxy. La demo con contraseña conocida es exclusivamente local y contiene datos ficticios.

No se incluyen WhatsApp, voz, pagos, suscripciones, n8n ni un modelo generativo. La evaluación es de un MVP y no acredita disponibilidad o seguridad de producción.

## Material de entrega

- [Presentación PowerPoint](tfm/ORQENTIVA-TFM.pptx).
- [Guion y recorrido de grabación](tfm/GUION_VIDEO.md).
- [Accesos de prueba](tfm/ACCESO_DEMO.md).
- [Lista de entrega y enlaces](tfm/ENTREGA.md).
- [Plan de publicación](tfm/DESPLIEGUE.md).

Repositorio público: pendiente de publicación por el autor. Vídeo: pendiente de grabación y enlace. Despliegue público: no realizado. No se ha enviado el formulario del máster. La presentación adjunta satisface la opción de incluir el archivo en el código; el formulario requiere completar su URL de acceso.
