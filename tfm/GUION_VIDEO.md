# Guion de presentación de ORQENTIVA

Duración orientativa: 10–12 minutos. Los requisitos compartidos no establecen una duración obligatoria. Grabar la pantalla durante la explicación es obligatorio y mostrar el rostro es opcional. Adaptar este texto a tus palabras y confirmar tu nombre completo antes de grabar.

## Preparación

Usar exclusivamente la demo aislada. Cerrar correo y páginas personales. Abrir la presentación y la aplicación. Tener preparada una fecha futura libre. No mostrar .env, gestores de contraseñas ni cuentas reales. Ensayar una vez la reserva y usar otro horario en la grabación.

## 1. Introducción — 0:00 a 0:45

Pantalla: portada de la presentación.

«Hola, soy Jesús Granados. Voy a presentar ORQENTIVA, mi proyecto de fin de máster. Es un MVP web para gestionar los servicios y reservas de diferentes negocios. La demostración utiliza dos barberías ficticias, Alfa y Beta. Mi objetivo es mostrar una aplicación que mantiene separados sus datos y permite completar una reserva mediante un flujo conversacional.»

## 2. Problema y alcance — 0:45 a 1:40

Pantalla: diapositivas del problema y alcance.

«La idea parte de una necesidad de pequeños negocios: responder consultas y organizar citas. En este MVP, un administrador configura los negocios y cada propietario administra sus propios servicios, horarios y reservas. Limité el alcance para poder construir y verificar el flujo completo. WhatsApp, voz y pagos quedan para una etapa posterior. No he medido todavía resultados comerciales con negocios reales.»

## 3. Arquitectura — 1:40 a 2:40

Pantalla: arquitectura y tecnologías.

«La interfaz utiliza React y TypeScript. FastAPI valida los datos y aplica los permisos. SQLAlchemy permite acceder a la base de datos y Alembic mantiene las migraciones. El desarrollo habitual usa PostgreSQL. Para facilitar la revisión preparé una demostración local con SQLite y datos ficticios. También ejecuté comprobaciones separadas con PostgreSQL temporal.»

«LangGraph organiza los pasos del chat. En esta versión utilizo reglas para interpretar las solicitudes. No hay un modelo generativo conectado. La consulta documental recupera fragmentos literales publicados por cada negocio. Esta decisión limita la flexibilidad del lenguaje, pero permite probar el comportamiento con claridad.»

## 4. Roles y paneles — 2:40 a 4:00

Pantalla: iniciar sesión como admin@example.com y luego como alfa@example.com.

«Como administrador puedo gestionar los negocios y sus accesos. Ahora cierro sesión y entro como propietario de Alfa. Aquí aparecen sus servicios, el horario, los profesionales y las reservas. La autorización se comprueba también en la API. Ocultar elementos de la interfaz por sí solo no protegería los datos.»

Mostrar Corte demo, su duración, Ana y el documento de cancelaciones.

## 5. Reserva y documento — 4:00 a 7:00

Pantalla: #reservar/alfa. Abrir «Reservar por chat».

Escribir: «Quiero Corte demo con Ana el AAAA-MM-DD a las 10». Usar una fecha futura libre.

«El asistente identifica el servicio y consulta la disponibilidad. Ahora solicita el nombre que falta.»

Escribir: «Soy Pedro». Mostrar la propuesta.

«Todavía no se ha guardado la cita. El sistema presenta los detalles y espera mi confirmación.»

Preguntar: «¿Con cuánta anticipación puedo cancelar?».

«El sistema busca en los documentos publicados de Alfa y cita la regla de 24 horas con su fuente. La respuesta es un fragmento verificable. Si no encuentra información suficiente, pide consultar al negocio.»

Seleccionar de nuevo «Reservar por chat» y pulsar «Confirmar cita».

«Al confirmar, la API vuelve a comprobar la disponibilidad y guarda la reserva. El mensaje de éxito aparece después de la respuesta del backend.»

Volver al panel de Alfa y mostrar la cita. Abrir Beta y mostrar su política de 48 horas.

«Beta tiene información diferente. La consulta de Alfa no utiliza la política de Beta. Esto es parte del aislamiento por negocio.»

## 6. Pruebas y resultados — 7:00 a 8:30

Pantalla: diapositiva de resultados y documento de verificación.

«La suite completa aprobó 137 pruebas. Dentro de ella hay 30 escenarios de aceptación: diez informativos, diez de reservas y diez adversos. Incluyen falta de información, horarios ocupados, reintentos y acceso entre negocios. También comprobé migraciones y flujos en PostgreSQL temporal, compilación del frontend y lint.»

«Estos resultados describen los escenarios ejecutados. No significan que el sistema sea infalible ni que esté certificado para producción. Los tiempos de los escenarios locales no son una medición de rendimiento público ni un percentil 95.»

## 7. Limitaciones y aprendizaje — 8:30 a 10:00

Pantalla: limitaciones y próximos pasos.

«El chat tiene un vocabulario y reglas acotados. No incluye un LLM ni búsqueda semántica. Los límites de uso actuales son por proceso y falta completar aspectos de una operación pública, como recuperación de contraseña y observabilidad. La versión presentada es un MVP académico.»

«Aprendí a separar interfaz, reglas de negocio y persistencia, a diseñar autorización por empresa y a distinguir una propuesta de una operación confirmada. Las pruebas me ayudan a comprobar lo que afirmo sobre el producto. En el futuro podría incorporar un modelo de lenguaje manteniendo estas validaciones.»

## 8. Cierre — 10:00 a 10:30

Pantalla: cierre y materiales.

«El repositorio incluye instrucciones, accesos de demostración, especificaciones y resultados. ORQENTIVA es una base funcional que puedo seguir mejorando. Gracias por revisar mi proyecto.»

Decir «repositorio» solo después de publicar el código. No afirmar que existe un despliegue público mientras no haya una URL comprobada.

## Preguntas para practicar

- ¿Por qué dos roles? Para separar la gestión de la plataforma de las operaciones de cada negocio.
- ¿Dónde se protege la información? En las dependencias y consultas de la API, además de la interfaz.
- ¿LangGraph es un LLM? No, aquí organiza un flujo con estado y reglas.
- ¿Hay RAG generativo? No. Hay recuperación extractiva de documentos, sin generación por LLM.
- ¿Cuándo se guarda una reserva? Tras confirmación explícita, revalidación y respuesta correcta del backend.
- ¿Por qué probar PostgreSQL además de SQLite? Sus transacciones y bloqueos no son idénticos.
- ¿Qué demuestra pasar las pruebas? Que la versión evaluada cumple esos escenarios concretos.
- ¿Qué mejorarías? Flexibilidad del lenguaje, observabilidad, controles de operación pública y evaluación con usuarios.
