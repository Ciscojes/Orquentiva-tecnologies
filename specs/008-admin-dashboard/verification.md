# Verificación — SPEC-008

Fecha de ejecución: 2026-11-04. Base: e825124, Git limpio al comenzar.

## Automatización

- pytest: 71 pruebas aprobadas; persiste el aviso conocido Starlette/httpx.
- Build TypeScript/Vite y lint correctos, sin avisos de lint.
- PostgreSQL 17 temporal: migración, correspondencia modelos/esquema, estado activo
  de negocios anteriores, creación de negocio/cuenta, duplicados, permisos y revocación.
- Regresiones aprobadas: reservas concurrentes, UTC/microsegundos, aislamiento,
  leads, importación histórica y logout.
- Upgrade/downgrade ensayados únicamente sobre bases temporales.

## Navegador con API real aislada

Edge con frontend compilado, SQLite temporal y cuentas ficticias:

- Crear negocio y cuenta; confirmación de contraseña y limpieza de campos secretos.
- Cliente no ve el panel ni accede a /admin (403).
- Cancelar desactivación conserva acceso; confirmar revoca sesión y bloquea login.
- Reactivar permite nuevo login; cookie anterior sigue rechazada.
- ES/EN conserva selección; recarga conserva idioma y consulta datos persistidos.
- Duplicados muestran mensaje; 503 permite reintentar; sesión vencida retira panel.
- Sin errores JavaScript ni desbordamiento a 1440, 768, 390 y 320 px.
- Capturas de escritorio y móvil revisadas visualmente.

Herramienta auxiliar de navegador fuera del repositorio; datos temporales eliminados
al terminar. Recorrido manual reproducible: docs/PANEL_ADMINISTRADOR.md en entorno
 de pruebas. No se utilizó la contraseña del usuario.

## Activación local

Destino comprobado: orqentiva_db, 127.0.0.1:5434. Respaldo pg_dump verificado.
Aplicada f814b008d002. Comparación de contenido antes/después sin diferencias,
exceptuando la columna añadida: 2 empresas, 2 servicios, 1 reserva, 0 leads,
1 usuario y 1 sesión. Ambas empresas quedan activas.

API ORQENTIVA recargada sin detener otros proyectos. Comprobadas rutas y proxy:
401 sin cookie y Cache-Control no-store. Sin cuentas ni negocios de QA en esta base.

## Cierre

Documentación guardada al retomar tras un fallo de la revisión automática por límite
de uso; no hubo fallo de las pruebas ni pérdida de implementación.
Commit manual pendiente. Mensaje sugerido:
`implementar panel administrativo de negocios y cuentas del MVP`.
