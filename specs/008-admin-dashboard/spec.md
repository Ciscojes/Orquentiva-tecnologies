# SPEC-008 — Panel de administrador del MVP

## Objetivo
Permitir a super_admin gestionar negocios y crear sus cuentas desde la web ES/EN.
Mantener el acceso del cliente limitado a su empresa y conservar la web comercial.

## Criterios de aceptación
1. Solo super_admin puede acceder a todas las rutas /admin: 401 sin sesión y 403 para business_admin.
2. Listar negocios con identificador, nombre y estado activo/inactivo; vista vacía y errores recuperables.
3. Crear negocio con identificador único de 1–50 caracteres (minúsculas, dígitos y guiones) y nombre recortado de 1–150. Duplicado: 409; datos incorrectos: 422 sin reflejar inputs.
4. Activar/desactivar mediante booleano estricto y operación idempotente. Desactivar requiere confirmación explícita en la interfaz y conserva datos del negocio.
5. Al desactivar, revocar sesiones de sus usuarios y rechazar nuevos logins. Reactivar no restaura sesiones antiguas. Alfa no afecta a Beta.
6. Crear una cuenta business_admin dentro del negocio elegido, con correo único normalizado y contraseña de 12–128 caracteres, protegida con Argon2. La interfaz pide confirmación de contraseña.
7. El rol y la empresa se asignan exclusivamente en servidor; rechazar role o business_id añadidos al cuerpo. No mover usuarios existentes ni cambiar sus contraseñas.
8. Listar cuentas del negocio sin hashes, tokens ni contraseñas. No enviar correos ni revelar leads desde el panel.
9. Todas las escrituras verifican Origin; respuestas privadas no-store. No conceder permisos por ocultar botones en React.
10. Persistencia después de recargar, interfaz ES/EN y móvil, estados pendientes/errores, sin botones decorativos.
11. Migración añade businesses.is_active=true para los negocios existentes sin cambiar sus datos ni cuentas.
12. Verificar con SQLite y PostgreSQL temporales, pruebas de permisos y recorrido de navegador. Activación local solo después de verificar y respaldar.

## Fuera de alcance
Eliminar negocios/usuarios, restablecer contraseñas, invitaciones por correo, permisos
por módulo, auditoría comercial completa, facturación, panel cliente, LangGraph y RAG.
El commit es manual.
