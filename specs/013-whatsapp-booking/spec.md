# SPEC-013 — Reservas guiadas y consultas por WhatsApp

Autorizada el 8 de noviembre de 2026. Amplía el alcance posterior al TFM sin reemplazar el panel web.

## Alcance del piloto
- Cloud API oficial, texto en español y un número de prueba asociado a Alfa.
- Mismo catálogo, agenda, LangGraph y consultas extractivas del canal web; sin LLM.
- Verificación del webhook y firma HMAC sobre el cuerpo original.
- Asociación número receptor → empresa controlada en configuración, nunca por instrucciones del cliente.
- Bandeja persistente de entrada/salida y borrador por empresa/remitente.
- Resumen y confirmación explícita posterior a su aceptación por Meta antes de reservar.
- Reserva, respuesta y estado guardados en una transacción. Reintentos de entrada no duplican citas.
- Consulta de políticas conserva el borrador y muestra fuentes.
- Respuestas libres solo dentro de 24 horas del mensaje recibido; eventos vencidos no crean citas.
- Eventos anteriores al último turno no sobrescriben el borrador.

## Fuera de este incremento
Recordatorios/plantillas, voz, multimedia, botones, cancelación de citas existentes, bandeja de operadores,
alta automática de negocios y despliegue comercial. HUMANO pausa y orienta a contactar al negocio;
no promete una transferencia que aún no existe. REINICIAR descarta únicamente el borrador.

## Estado
Implementado y verificado localmente con eventos firmados simulados y transporte HTTP simulado.
147 pruebas aprobadas (137 anteriores + 10 nuevas), incluida migración completa de ida y vuelta en SQLite.
Pendientes: alta Meta, credenciales, HTTPS, prueba real de ida y vuelta y validación de esta ampliación en PostgreSQL.
No se han enviado mensajes reales ni publicado el servicio.

## Criterios para cerrar
- [x] Firma, desafío, números no asociados y canal desconfigurado.
- [x] Reserva visible en panel, confirmación posterior al resumen y rechazo de duplicados.
- [x] Conflicto de horario y nueva confirmación, aislamiento, fuentes y borrador persistente.
- [x] Cola conservada ante fallo de envío, caducidad, mensajes fuera de orden y pausa.
- [ ] Cuenta/número Meta configurados con secretos fuera del repositorio.
- [ ] Prueba real con teléfono autorizado y cita visible en el panel.
- [ ] Validación PostgreSQL y operación supervisada antes de uso comercial.

## Límite de entrega
`sent` significa que Meta aceptó el envío; no prueba lectura ni entrega al teléfono. Si Meta acepta un envío
y se pierde la respuesta de red, el reintento puede repetir el texto, pero no la reserva. Los eventos de estado
se ignoran en este piloto. Se ejecuta un trabajador único por base con bloqueo; no está diseñado para alto volumen.
La cola y borradores contienen datos personales: definir retención y acceso antes de producción.

Guía operativa: ../../docs/WHATSAPP_PILOT.md.
