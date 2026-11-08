# SPEC-007 — Autenticación y roles del MVP TFM

La SPEC-006 ya está dedicada a servicios comerciales; se mantiene su numeración.
Este incremento inicia el MVP acordado: autenticación, paneles mínimos, LangGraph,
RAG básico, evaluación y documentación. Los paneles y la IA serán incrementos posteriores.

## Criterios de aceptación
1. Login con correo y contraseña, validado en servidor, con mensajes genéricos ante credenciales incorrectas.
2. Contraseñas con Argon2; ninguna contraseña o identificador de sesión en logs, respuestas JSON o almacenamiento web.
3. Sesiones aleatorias de 256 bits, guardadas solo mediante SHA-256 en base de datos, con caducidad absoluta de 8 horas.
4. Cookie HttpOnly, SameSite=Strict, Secure por defecto. HTTP local exige configuración explícita.
5. Logout revoca la sesión en el servidor. Reutilizar la cookie después produce 401.
6. Usuario ausente, inactivo, sesión inválida o caducada: 401. Rol sin autorización: 403.
7. business_admin pertenece a una sola empresa; super_admin no hereda acceso a las reservas de clientes.
8. Empresa autorizada derivada del usuario en cada petición. Se rechazan las antiguas claves demo; modificar parámetros no cambia la empresa.
9. Login, logout y operaciones protegidas de escritura verifican un Origin de la lista explícita; no se confía en Host ni X-Forwarded-For del visitante.
10. Límite inicial de 5 intentos de login/IP/minuto por proceso. Documentar que no es un contador distribuido.
11. React ofrece acceso ES/EN, recuperación de sesión al recargar y cierre de sesión. No anuncia dashboards ni agentes aún pendientes.
12. Creación de usuarios mediante comando local con contraseña oculta; sin registro público ni credenciales predeterminadas.
13. Alembic añade usuarios y sesiones sin reescribir reservas, servicios ni leads existentes. Pruebas SQLite y PostgreSQL temporales.
14. POST /leads y web comercial siguen siendo públicos y funcionales.

## Fuera de alcance
Paneles de gestión, múltiples empresas por usuario, recuperación de contraseña, MFA,
invitaciones, OAuth externo, IA, despliegue y migración automática de la base habitual.
El commit sigue siendo manual.
