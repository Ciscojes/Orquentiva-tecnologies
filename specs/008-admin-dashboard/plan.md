# PLAN-008

- Añadir Business.is_active con default y server_default true, mediante Alembic.
- Crear router /admin protegido globalmente con require_super_admin; usar get_db.
- GET/POST /admin/businesses, PATCH /admin/businesses/{id}, GET/POST /admin/businesses/{id}/users.
- Actualizaciones de estado toman bloqueo de fila PostgreSQL; login del negocio toma
  el mismo bloqueo para no generar sesiones simultáneas a una desactivación.
- Desactivar revoca sesiones en la misma transacción. current_user verifica empresa
  activa en cada petición; login inválido conserva mensaje genérico.
- Crear usuarios reutilizando UserCreate/create_user; el cliente no selecciona rol ni envía empresa en el cuerpo.
- Añadir AdminDashboard solo a la sesión super_admin en AccessPanel. Formularios de
  negocio y cuenta, selección de negocio, estado y confirmación antes de desactivar.
- Reutilizar fetch mismo origen; añadir proxy /admin. Mantener claves solo en cookies HttpOnly.
- Probar permisos, CSRF, normalización, duplicados, revocación y persistencia; E2E con
  cuentas y empresas temporales. No utilizar la cuenta real del usuario en QA.
