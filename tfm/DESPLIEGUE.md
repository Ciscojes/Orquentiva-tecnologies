# Publicación del MVP

Estado: aplicación validada localmente. No hay URL pública ni infraestructura nueva contratada.

El requisito compartido por el alumno recomienda el despliegue cuando sea posible. La entrega incluye instrucciones de ejecución local y una demostración aislada.

## Configuración necesaria para publicar

- Generar frontend/dist con npm ci y npm run build.
- Servir los archivos estáticos con fallback a index.html. El enrutamiento de la interfaz usa hash.
- En el mismo origen HTTPS, reenviar /auth, /admin, /client, /book y /leads hacia FastAPI.
- Configurar DATABASE_URL para una base PostgreSQL dedicada. Ejecutar alembic upgrade head antes de abrir el acceso.
- Configurar AUTH_COOKIE_SECURE=true y AUTH_ALLOWED_ORIGINS con el origen HTTPS exacto.
- Preparar solo negocios y cuentas ficticios para la revisión. No publicar la demo local con su contraseña conocida.
- Revisar límites compartidos si hay varias instancias, copias de seguridad y registros sin datos sensibles.
- Comprobar login, logout, roles, disponibilidad, confirmación, reintentos, políticas y revocación en el entorno publicado.

No se ha elegido proveedor ni presupuesto. No se presentan comandos de despliegue sin haber concretado el destino. Una vez publicado, añadir la URL real a README y ENTREGA.md y probar el acceso desde otro dispositivo.
