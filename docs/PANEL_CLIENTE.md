# Panel del cliente — SPEC-009

## Acceso

Abrir http://127.0.0.1:5178/#access con una cuenta business_admin. Super Admin
continúa entrando al panel de administración; no puede operar como cliente.
Si no existe cuenta de cliente, crearla desde Administrador > Gestionar negocio >
Crear cuenta de cliente. Elegir contraseña propia y no compartirla en el chat.
Cerrar la sesión de administrador y entrar con la cuenta del negocio.

## Servicios

Crear o editar nombre, precio entero en colones, duración entre 5 y 480 minutos
y estado activo/inactivo. No se eliminan servicios. Los anteriores conservan
nombre/precio y aparecen con duración «Por definir»; el cliente debe indicar
su duración real. Cada cuenta puede ver y cambiar exclusivamente su empresa.

## Horario de atención

Semana de lunes a domingo en America/Costa_Rica (UTC−06:00), con un intervalo
por día o cerrado. Desmarcar Cerrado y completar apertura y cierre en HH:MM.
La apertura debe ser anterior al cierre dentro del mismo día. Guardar horario
actualiza los siete días en una sola transacción. Al inicio no hay horario
configurado y la pantalla lo indica; no se crean horas abiertas automáticamente.
Esta versión no contempla pausas, varios turnos, empleados ni días festivos.

## Reservas

Lista de solo lectura con nombre, referencia y fecha/hora en Costa Rica,
independientemente de la zona horaria del navegador. No se crean, cancelan ni
modifican reservas desde este incremento.

Guardar horarios o duración no añade por sí solo validación de disponibilidad.
POST /appointments conserva el contrato anterior y la unicidad por empresa e
instante. Antes de LangGraph se implementarán duración de citas, solapamientos,
validación del horario e idempotencia. El agente y el RAG todavía no están activos.

## API y controles

| Ruta | Método | Resultado |
| --- | --- | --- |
| /client/dashboard | GET | Empresa, catálogo, horario y reservas propios |
| /client/services | POST | Crear servicio; 201 |
| /client/services/{id} | PUT | Actualizar servicio propio; 200, ajeno/inexistente 404 |
| /client/hours | PUT | Guardar semana completa; 200 |

Todas requieren sesión business_admin de negocio activo. Escrituras verifican
Origin, rechazan campos adicionales y no aceptan business_id. Respuestas no-store.
Sin sesión: 401; rol incorrecto: 403. Datos inválidos: 422 sin reflejar inputs.
Sin secretos ni tokens en localStorage. Una sesión vencida retira el panel.

## Activación y comprobación

Migración a915c009e003 aplicada en desarrollo con pg_dump previo y comparación de
contenido. Añade duración nullable, estado de servicios y tabla business_hours.
No modifica nombres, precios, reservas ni cuentas existentes. No se crearon
cuentas ni servicios de prueba en la base habitual.

API 127.0.0.1:8001; Vite 127.0.0.1:5178 con proxy /client. El script
start_development.ps1 conserva el arranque existente. Consultar README para una
base nueva. No ejecutar downgrade sobre datos de uso habitual.

Pruebas: pytest y scripts/verify_postgres.py, ambos con bases temporales.
Recorrido manual en entorno de prueba: entrar con Alfa, editar un servicio,
guardar horario, recargar, cambiar idioma y comparar contra una cuenta de Beta.
Resultados: specs/009-client-dashboard/verification.md.

Navegación: usar «Acceso clientes» en la cabecera para iniciar sesión y «Mi panel» para volver al dashboard. En móvil, acceso e idioma permanecen visibles; los enlaces del sitio se agrupan en «Menú». El enlace #access anterior sigue funcionando.

## Agenda por profesional

Con la agenda habilitada, configura primero servicios con duración y horario de atención del negocio. En **Mi equipo**, registra a cada profesional con el nombre que deseas publicar, marca sus servicios y guarda sus días y horas. El enlace de reservas aparece debajo del equipo. Comparte ese enlace con tus clientes.

El visitante elige servicio, fecha y profesional o «Cualquiera disponible». Al confirmar recibe el horario y el profesional asignado. Actualiza los datos del panel para ver la reserva. La tabla muestra una columna por profesional en escritorio y agrupa los nombres por turno en móvil. Las reservas antiguas sin asignación aparecen como «Sin asignar». Para evitar conflictos de duración desconocida, el sistema bloquea ese día en la disponibilidad pública.

Los horarios se interpretan en Costa Rica. Se consultan fechas hasta 365 días por adelantado; los turnos se ofrecen cada cinco minutos dentro del intervalo disponible.
