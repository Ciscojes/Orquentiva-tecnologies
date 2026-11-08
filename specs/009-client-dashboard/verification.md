# Verificación — SPEC-009

Base: commit 7a99ee0 y árbol limpio antes de editar. Ejecución: 2026-11-04.

## Pruebas

- 104 tests pytest aprobados. Aviso conocido de deprecación Starlette/httpx sin fallos.
- TypeScript/Vite build y lint correctos.
- SQLite y PostgreSQL 17 temporal: migraciones coherentes con modelos, upgrade y downgrade.
- Catálogo: duración nullable de datos anteriores, creación, edición, estado, tipos
  estrictos, límites y 404 idéntico para recurso ajeno/inexistente.
- Horario: siete días, intervalo válido o cerrado, persistencia, aislamiento y rechazo
  de semanas incorrectas sin sobrescribir el horario anterior.
- Controles de rol, sesión, negocio activo, Origin y campos adicionales.
- Regresiones de autenticación, administración, leads y reservas aprobadas.

## Navegador real aislado

Edge, frontend compilado y FastAPI sobre SQLite temporal con cuentas ficticias:

- Crear servicio, editar precio/duración y desactivar.
- ES/EN conserva edición de servicio y horario.
- Intervalo inválido no guarda; horario válido persiste después de recargar.
- Reservas mostradas en Costa Rica aun con navegador configurado en Asia/Tokyo.
- Beta no ve servicio/reserva/horario de Alfa; escritura contra servicio ajeno devuelve 404.
- Error 503 recuperable; pérdida de sesión retira el panel.
- Sin errores JavaScript ni desbordamiento a 1440, 768, 390 y 320 px.
- Capturas de móvil y escritorio inspeccionadas.

Herramienta auxiliar fuera del repositorio; cuentas y datos temporales eliminados
al terminar. Repetición manual documentada en PANEL_CLIENTE.md.

## Activación local

Destino verificado: orqentiva_db en 127.0.0.1:5434. Respaldo pg_dump verificado.
Aplicada a915c009e003. Datos previos conservados: 2 empresas, 2 servicios,
1 reserva, 0 leads, 1 usuario y 0 sesiones en el momento de la migración.
Servicios anteriores activos, duración sin definir; business_hours sin filas iniciales.

API ORQENTIVA recargada sin detener otros proyectos. Comprobados /client/dashboard,
proxy y respuesta 401 sin cookie con no-store. No se usó la contraseña del usuario
ni se crearon datos de QA en su base habitual.

## Pendientes

Revisión del usuario y commit manual. La gestión avanzada de reservas y la validación
de disponibilidad/solapamientos siguen pendientes antes del agente.
Mensaje sugerido: implementar panel de cliente con servicios horarios y reservas.

## Ajuste de navegación responsive solicitado durante la revisión

La web comercial ya no contiene el login ni los dashboards. El botón de cabecera
muestra Acceder/Sign in o Mi panel/My dashboard según el estado de sesión.
Pantallas independientes con #login y #panel; #access continúa siendo compatible.
Los enlaces #client-services, #client-hours y #client-bookings conservan el panel.

Build y lint aprobados. Navegador con API temporal: menú móvil/Escape, etiquetas
ES/EN, login de ambos roles, logout, recarga, Atrás/Adelante, retorno al sitio,
entrada heredada y anclajes internos. Botón de acceso táctil de al menos 44 px,
sin desbordamiento a 320, 390, 768 y 1440 px. Capturas móviles inspeccionadas.
Se corrigió la normalización del enlace heredado al navegar dentro de la misma
pantalla. No se requirió migración ni se cambió la autorización del backend.
