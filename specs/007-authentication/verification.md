# Verificación — SPEC-007

Fecha: 2026-11-04.

## Estado de partida

Commit 77bf6bb confirmado, árbol limpio. Antes de editar: 42 tests aprobados,
build y lint correctos, pip check sin incompatibilidades. Los checklist de
SPEC-005 y SPEC-006 se actualizaron con sus commits ya comprobados.

## Resultados del incremento

- pytest: 56 pruebas aprobadas. Conservado aviso de deprecación Starlette/httpx,
  sin fallos ni incompatibilidades; no se cambia la infraestructura de tests por ese aviso.
- Build TypeScript/Vite y lint: correctos.
- pip check: sin requisitos incompatibles.
- git diff --check: correcto.
- Alembic y modelos coinciden en SQLite y PostgreSQL 17 temporal.
- Upgrade desde d8f25b602d7b conserva servicios existentes. Downgrade de auth y
  nuevo upgrade verificados únicamente en PostgreSQL temporal.
- Integración real PostgreSQL: credenciales Argon2, sesiones con fecha consciente
  de zona horaria, roles, rechazo de claves demo, aislamiento Alfa/Beta, reservas
  concurrentes, UTC/microsegundos, leads, importación histórica y logout.
- El servidor PostgreSQL temporal fue detenido al terminar.

## Navegador contra API real aislada

Edge con frontend compilado y FastAPI sobre SQLite temporal, cuentas ficticias,
sin conectar a PostgreSQL habitual ni leer .env:

- Credenciales incorrectas rechazadas; contraseña vaciada después del intento.
- Login de Alfa, Beta y Super Admin; acceso y permisos comprobados en servidor.
- Cookie HttpOnly/SameSite=Strict, no visible mediante document.cookie.
- No se guardan tokens ni credenciales en localStorage.
- Cambio ES/EN y recarga conservan la sesión válida.
- Falta de Origin rechazada al escribir una reserva.
- Logout real y reproducción de la cookie anterior: 401.
- Error simulado 503 al cerrar sesión: se mantiene la cuenta y aparece aviso,
  sin presentar una revocación como exitosa.
- Sin errores JavaScript ni desbordamiento horizontal a 1366, 768, 390 y 320 px.
- Captura de escritorio revisada visualmente.

La herramienta de navegador es auxiliar fuera del repositorio. El entorno
completo de QA y sus cuentas desaparecen al terminar. Para repetir manualmente,
seguir docs/AUTENTICACION.md en una base de desarrollo y comprobar el acceso de
cada rol, recarga, cambio de idioma y cierre de sesión.

## Pendiente operativo

La migración y creación de usuarios en la base habitual NO se han ejecutado.
No se ha leído ni mostrado .env, hecho commit ni desplegado el sitio.
Los dashboards corresponden a SPEC-008/009; LangGraph y RAG siguen pendientes.

Commit sugerido: implementar autenticación por sesiones y roles del MVP.

## Activación local autorizada — 2026-11-04

Aplicada e713a007c001 en orqentiva_db, 127.0.0.1:5434, después de pg_dump.
Comparación por contenido antes/después: sin cambios en 2 empresas, 2 servicios,
1 reserva y 0 leads. Tablas de autenticación creadas; usuarios: 0.
La nota anterior de migración pendiente corresponde al estado previo a esta activación.

API: 127.0.0.1:8001. Web: 127.0.0.1:5178. Puerto 8000 ocupado por otro proyecto;
no se detuvo ese servicio. Proxy /auth y /leads actualizado al 8001.
Comprobados health, web y rechazo 401 de acceso sin cuenta desde el proxy real.
Falta que el usuario cree su cuenta mediante create_user.py y elija una contraseña.
