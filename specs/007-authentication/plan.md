# PLAN-007

- Conservar estructura actual; añadir app/auth.py, app/routes/auth.py y un componente AccessPanel.
- Reutilizar SQLAlchemy/get_db. Tablas users y auth_sessions, con FK y restricciones de roles.
- Usar pwdlib[argon2] para contraseñas y secrets.token_urlsafe(32) para sesiones opacas.
- Elegir sesiones persistidas para poder invalidarlas inmediatamente al cerrar sesión; no introducir JWT ni secretos de firma.
- Cookie HttpOnly y verificación estricta de Origin para operaciones de escritura, sin CORS abierto.
- Retirar DEMO_KEYS; adaptar pruebas de reservas a sesiones reales de usuarios de prueba.
- Crear usuarios exclusivamente mediante un comando que solicita contraseña con getpass, valida rol/empresa y nunca sobrescribe cuentas.
- Añadir /auth/login, /auth/me y /auth/logout. El servidor decide identidad y rol.
- React usa fetch de mismo origen, con credenciales en cookie y timeout; no utiliza localStorage para autenticación.
- Conservar /leads y ampliar proxy Vite para /auth. Los futuros paneles tendrán especificaciones propias.
- Probar credenciales, revocación, caducidad, CSRF, roles, aislamiento, privacidad de errores y migraciones en bases temporales.

## Referencias de diseño
- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ (hash Argon2 con pwdlib).
- https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html (sesiones, cookies y expiración).
