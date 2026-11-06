# Panel de administrador — SPEC-008

## Uso local

Abrir http://127.0.0.1:5178/#access con la cuenta super_admin. Si ya hay sesión,
recargar la página. Un business_admin no ve el panel y recibe 403 en sus rutas.

1. Crear negocio: identificador único de minúsculas, números y guiones, y nombre.
   El identificador no se modifica después.
2. Seleccionar «Gestionar» en el negocio.
3. Crear su cuenta de cliente con correo y contraseña inicial, repetida para confirmar.
   El servidor fija business_admin y el negocio seleccionado; no se envía correo.
4. Comunicar la contraseña al titular por un canal privado. No guardarla en Git.
5. Desactivar requiere confirmación: conserva datos, cierra sesiones e impide login.
6. Reactivar permite nuevos logins, pero no recupera sesiones anteriores.

No incluye traslado de cuentas, eliminación de negocios, cambio de contraseñas ni
edición de reservas. El panel de cliente está disponible en SPEC-009; ver PANEL_CLIENTE.md.

## Contrato

Todas las rutas requieren sesión super_admin. Escrituras requieren Origin permitido.
Las respuestas privadas incluyen Cache-Control: no-store.

| Ruta | Método | Resultado |
| --- | --- | --- |
| /admin/businesses | GET | Negocios con id, name, is_active |
| /admin/businesses | POST | Crea negocio; 201, duplicado 409 |
| /admin/businesses/{id} | PATCH | Cambia is_active, booleano estricto |
| /admin/businesses/{id}/users | GET | Cuentas del negocio sin secretos |
| /admin/businesses/{id}/users | POST | Crea cuenta business_admin; 201, duplicado 409 |

Crear cuenta acepta solo email y password; no acepta rol ni empresa en el cuerpo.
No modifica cuentas existentes. Las claves demo siguen sin conceder acceso.

## Migración y arranque

Revisión f814b008d002: businesses.is_active, inicialmente true. Aplicada en desarrollo
el 2026-11-04, con respaldo pg_dump y verificación de conservación de datos y cuentas.
No se crearon negocios ni cuentas de QA en la base habitual.

API 127.0.0.1:8001, web 127.0.0.1:5178. Desde la raíz, en dos terminales:

```powershell
.\scripts\start_development.ps1 -Component api
.\scripts\start_development.ps1 -Component web
```

Vite redirige /admin, /auth y /leads a ORQENTIVA. Para una base nueva, seguir
README y Alembic. No ejecutar downgrade en la base habitual.

Resultados: specs/008-admin-dashboard/verification.md.

Navegación: usar «Acceso clientes» en la cabecera para iniciar sesión y «Mi panel» para volver al dashboard. En móvil, acceso e idioma permanecen visibles; los enlaces del sitio se agrupan en «Menú». El enlace #access anterior sigue funcionando.
