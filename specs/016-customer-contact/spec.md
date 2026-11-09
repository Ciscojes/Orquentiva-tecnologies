# SPEC-016 — Contacto del cliente en las reservas

## Objetivo
Que el negocio pueda avisar al cliente si cambia o cancela una cita reservada por la web.

## Alcance
- Nueva columna `appointments.customer_contact` (migración e015contact), opcional en la base.
- Reserva pública (formulario y chat): teléfono o correo obligatorio. Teléfono de 7 a 15 dígitos, con + opcional; correo validado y en minúsculas.
- Chat: después del nombre pregunta «¿A qué teléfono o correo te avisamos si hay cambios?» y repite la pregunta si el dato no es válido; el resumen muestra el contacto.
- WhatsApp: no pregunta; guarda el número del remitente.
- Panel del negocio: el contacto aparece bajo el nombre en la agenda.
- Un reintento con la misma clave y otro contacto se rechaza (409).

## Fuera de alcance
Envío de avisos o recordatorios, y edición del contacto desde el panel.

## Verificación
`tests/test_customer_contact.py`, `tests/test_booking_chat.py` y `tests/test_whatsapp.py`.
