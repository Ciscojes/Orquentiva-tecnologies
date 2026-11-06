# PLAN-009

- Añadir Service.duration_minutes nullable e is_active=true. Conservar valores históricos.
- Crear business_hours con clave (business_id, weekday), indicador cerrado y minutos
  de apertura/cierre opcionales. Restricciones de coherencia en modelo y base.
- Router /client: GET /dashboard, POST /services, PUT /services/{id}, PUT /hours.
- Resolver current_business en todas las rutas; no exponer operaciones cruzadas ni
  permitir que el cliente envíe empresa. Mismo 404 para servicio ajeno/inexistente.
- Validar con Pydantic estricto y rechazar campos extra. Guardar semana completa,
  bloqueando la fila de empresa en PostgreSQL para serializar cambios concurrentes.
- React: ClientDashboard para business_admin, catálogo editable, horario semanal y
  tabla responsive de reservas. Formatear UTC con Intl y zona America/Costa_Rica.
- Reutilizar estilos de panel y ampliar proxy /client. Mantener panel administrador.
- Pruebas de aislamiento, CSRF, persistencia, actualización atómica y datos históricos;
  recorrido de navegador con dos negocios ficticios, sin contraseñas reales.
