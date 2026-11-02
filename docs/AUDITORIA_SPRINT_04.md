# Auditoría y correcciones — 1 de noviembre de 2026

## Resultado actual

Los fallos reproducidos en el alcance auditado quedaron corregidos. POST /leads
y el formulario ES/EN están implementados; las reservas rechazan nombres vacíos
y horarios equivalentes aunque usen distintas zonas horarias. No se creó ningún commit.
Esto no constituye una garantía de ausencia de cualquier error futuro.

## Estructura y Git

- Estructura adecuada para el incremento: app, frontend, tests, specs y alembic.
- Se añadió app/routes/leads.py, pruebas de regresión y scripts/verify_postgres.py.
- Rama master; último commit previo 874d4cf. Se conservaron los cambios anteriores
  del usuario en modelos, migración y especificaciones. En app/models.py solo se
  quitó la línea vacía sobrante al final; no se cambió el modelo.
- .env está excluido de Git. No se mostraron sus valores.
- README, alcance del Sprint 04 y tareas SDD actualizados.

## Fallos corregidos

- Faltaba POST /leads y el formulario solo validaba sin enviar.
- requirements.txt omitía dependencias necesarias de persistencia y validación.
- Los tests dependían de la configuración local; ahora fuerzan bases temporales.
- Los nombres de reservas se validaban antes de quitar espacios.
- La unicidad por cadena permitía reservar el mismo instante con offsets distintos.
- El listado ordenaba cadenas de fechas y podía presentar horarios fuera de orden.
- La comprobación e inserción de reservas ahora se serializan con BEGIN IMMEDIATE.
  Se comparan también las fechas antiguas por instante, sin reescribir registros.
- Se corrigió la advertencia del frontend sobre el cálculo del año al renderizar.

## Captación de leads

Validación de nombre, correo, empresa, catálogo de servicios y mensaje. Respuesta
201 mínima, errores 422 sin reflejar datos personales, 503 sin detalles SQL y
límite básico de cinco envíos válidos por IP/minuto/proceso. Sin listado público.
Formulario bilingüe con aviso de uso de datos, envío, confirmación y errores.
Mismo origen en el navegador, con proxy Vite a la API local.

## Evidencia

- 29 pruebas backend aprobadas: validación, persistencia, antiabuso, privacidad,
  aislamiento entre empresas, reservas concurrentes, fechas antiguas, offsets,
  microsegundos, orden cronológico y migraciones SQLite temporales.
- Integración aprobada en un PostgreSQL 17 temporal independiente, limitado a
  127.0.0.1 y puerto temporal: upgrade completo, comparación de esquema/ORM,
  seed repetible, GET /business/me por empresa, POST /leads con persistencia real
  y created_at con zona horaria, errores 422, ausencia de listado, límite 429
  sin filas adicionales y downgrade completo. Servidor temporal detenido.
- npm run build, npm run lint y pip check aprobados.
- Navegador: envíos ficticios ES y EN completados con base temporal, confirmación
  visible y formulario vaciado. Captura guardada como evidencia.
- PostgreSQL habitual solo se consultó en modo lectura durante la primera auditoría:
  tabla leads y revisión d8f25b602d7b confirmadas. No se aplicaron migraciones,
  seeds ni escrituras sobre esa instancia.
- Persiste una advertencia de deprecación de TestClient/httpx del entorno instalado;
  no impide las pruebas y no se actualizaron paquetes por ese aviso.

## Decisiones y trabajo posterior

- Servicios y reservas siguen en SQLite demo; empresa actual y leads en PostgreSQL.
  Es una transición de arquitectura pendiente, no uno de los fallos de reservas
  corregidos. La migración completa debe abordarse como el siguiente incremento.
- El límite antiabuso es local a cada proceso. Un despliegue con varias instancias
  necesita contador compartido y configuración de proxies de confianza.
- Las claves demo siguen siendo educativas. No se declara el sistema listo para
  exposición pública ni se añade autenticación real fuera del alcance del sprint.
- No se revisaron ni modificaron reservas históricas de bases existentes para
  eliminar posibles duplicados anteriores.
- El siguiente paso inmediato es revisar los cambios y hacer el commit manualmente.

Mensaje sugerido: `implementar captación de leads y corregir validación y horarios de reservas`.
