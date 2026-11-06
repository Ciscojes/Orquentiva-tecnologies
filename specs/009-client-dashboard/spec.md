# SPEC-009 — Panel del cliente

## Objetivo
Ofrecer a business_admin un espacio ES/EN para mantener su catálogo y horario de
atención y consultar reservas. La empresa procede de la sesión, nunca del navegador.

## Criterios de aceptación
1. GET /client/dashboard devuelve exclusivamente empresa, servicios, reservas y horario del negocio autenticado.
2. Sin sesión: 401; super_admin o negocio desactivado: acceso denegado. No sustituye el panel administrativo.
3. Crear/editar servicios propios: nombre recortado 1–150, precio entero CRC 0–10000000, duración entera 5–480 minutos, estado activo/inactivo.
4. Los servicios anteriores conservan su precio y nombre, quedan activos y con duración sin definir. No inventar duración ni sobrescribir datos.
5. Intentar modificar un servicio ajeno o inexistente devuelve el mismo 404. No aceptar business_id ni id en el cuerpo.
6. Horario semanal de lunes a domingo, un intervalo por día o cerrado, en America/Costa_Rica. Horas HH:MM del mismo día, apertura anterior al cierre.
7. Guardar los siete días en una sola transacción; rechazar duplicados, días faltantes, campos adicionales, segundos y rangos inválidos. Sin configuración inicial: mostrar estado explícito, sin inventar horario abierto.
8. Reservas de solo lectura, orden cronológico, nombre y fecha/hora de Costa Rica. No modificar reservas históricas.
9. Formularios, estados vacíos, errores recuperables, cambio ES/EN sin perder edición y diseño móvil.
10. Persistencia después de recargar, sin cookies/tokens en localStorage; escrituras con Origin permitido y respuestas no-store.
11. Pruebas SQLite/PostgreSQL temporales y navegador real aislado; migración local con respaldo antes de activarla.

## Límites de este incremento
Configurar horario y duración no incorpora aún un motor de disponibilidad: la API
de reservas anterior sigue comprobando solo unicidad por empresa/instante. Antes
del agente se implementarán duración de citas, solapamientos, disponibilidad e
idempotencia. No hay edición, cancelación ni creación de reservas desde este panel.
No incluye empleados, intervalos partidos, festivos, varias zonas horarias, calendario
de arrastrar eventos, RAG ni LangGraph. Commit manual.
