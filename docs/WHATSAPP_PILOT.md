# Piloto WhatsApp de ORQENTIVA

Preparado el 8 de noviembre de 2026. Integración local comprobada; cuenta Meta y conexión real pendientes.

## 1. Crear la cuenta y número de prueba
Entrar en https://developers.facebook.com/ con la cuenta del propietario y completar el registro de desarrollador.
Crear una aplicación con el caso de uso de WhatsApp y asociar el portafolio empresarial que corresponda.
En la configuración de API de WhatsApp, obtener el número de prueba y añadir/verificar el teléfono que hará las pruebas.
Los nombres de las pantallas pueden variar; seguir el asistente vigente del panel.
Guía oficial (requiere sesión): https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started

Anotar de forma privada: App Secret, token de acceso, Phone Number ID y versión de Graph API indicada por Meta.
Crear además un Verify Token aleatorio propio; no es el token de acceso. No pegar secretos en el chat.
Los tokens temporales del panel deben renovarse al caducar. Para operación continua configurar credenciales de servicio.

## 2. Preparar una base aislada
Desde la raíz del proyecto con el entorno Python activo:

```powershell
python scripts/whatsapp_pilot.py prepare
Copy-Item whatsapp.env.example .env.whatsapp
```

El primer comando crea whatsapp-demo.sqlite3 con datos ficticios y las migraciones, y se niega a sobrescribirla.
No modifica las bases anteriores. Completar los valores privados en .env.whatsapp usando un editor local.
En WHATSAPP_PHONE_BUSINESSES poner el identificador del número de Meta asociado a `alfa`.
El archivo privado está excluido de Git. La versión API debe copiarse del panel, no del valor ficticio de las pruebas.

## 3. Arrancar recepción y procesamiento
En dos terminales separadas:

```powershell
python scripts/whatsapp_pilot.py webhook
```

```powershell
python scripts/whatsapp_pilot.py worker
```

El receptor escucha en 127.0.0.1:8013 y solo expone /integrations/whatsapp/webhook.
La aplicación administrativa y sus cuentas demo no se exponen en ese puerto.
Publicar ese puerto mediante un túnel HTTPS para la prueba o un servidor HTTPS para una instalación estable.
El destino/proveedor aún no está elegido; no se ha contratado infraestructura.
Registrar en Meta la URL HTTPS terminada en /integrations/whatsapp/webhook y el Verify Token configurado.
Suscribir el campo messages. Mantener ambos procesos encendidos durante la prueba.

El receptor guarda y confirma la recepción rápidamente. El trabajador procesa la cola y envía las respuestas;
solo debe existir uno por base. Al reiniciarlo, los borradores y mensajes pendientes permanecen guardados.
Para una instalación existente, respaldar su base y ejecutar `alembic upgrade head` con su configuración antes de activar el canal.
No se han aplicado migraciones a bases existentes durante la implementación.

## 4. Prueba real de aceptación
Desde el teléfono autorizado, escribir al número de prueba:
1. «Quiero un Corte demo con Ana mañana a las 10».
2. Dar el nombre cuando lo solicite.
3. Consultar «¿Cuál es la política de cancelaciones?» y comprobar la fuente de Alfa.
4. Tras recibir el resumen, responder CONFIRMO.
5. Abrir el panel local conectado a whatsapp-demo.sqlite3 y comprobar una sola cita.
6. Repetir CONFIRMO: no debe crear otra reserva.
7. Probar otro remitente para el mismo turno y verificar que se pida otra hora.

El panel debe utilizar la misma DATABASE_URL que el piloto; el servidor de demo anterior utiliza otra base.
Se puede iniciar la API completa localmente con esa variable y conectar el frontend mediante su configuración de proxy habitual.
No publicar las cuentas y contraseñas ficticias del piloto en un servidor accesible a terceros.

## 5. Operación y límites
- Texto en español, hasta 350 caracteres por mensaje; no interpreta audios ni ofrece comprensión general con LLM.
- La lista muestra hasta 20 opciones de horario. También se puede escribir otra hora para consultar disponibilidad.
- REINICIAR, CANCELAR o NO descartan el borrador, no cancelan una cita ya guardada.
- HUMANO pausa el asistente; todavía no hay bandeja ni aviso automático a un operador.
- No envía recordatorios ni plantillas. Eventos con 24 horas o más se omiten sin reservar ni responder.
- `sent` registra aceptación de Meta, no confirmación de entrega/lectura. Un fallo de red ambiguo puede duplicar una respuesta;
  la reserva permanece única. Revisar errores de configuración si la cola no avanza.
- Los mensajes y borradores contienen datos personales. Limitar acceso y definir eliminación/retención antes de producción.
- Requiere validar PostgreSQL, supervisión y manejo de errores operativos antes de atender clientes reales.

## Verificación local
147 pruebas aprobadas el 8 de noviembre de 2026 en bases SQLite temporales. Diez pruebas nuevas cubren firmas,
reserva/confirmación, reintentos, aislamiento documental, fallos de envío, caducidad, conflictos, pausa,
canal desconfigurado y mensajes fuera de orden. Los envíos a Meta fueron simulados: no se usaron credenciales reales.

```powershell
python -m pytest -q
```

Referencias oficiales: https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/webhooks/start/
y https://business.whatsapp.com/products/platform-pricing.
La referencia histórica del SDK se consultó para el protocolo; no se añadió ese SDK archivado como dependencia.
