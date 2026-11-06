# ORQENTIVA AI — Alcance del MVP del TFM

Fecha de actualización: 2026-11-04. Caso de demostración: dos barberías ficticias.
Se conserva la estructura del repositorio y la web corporativa; no se crea otro proyecto.

## Orden de los incrementos

| Especificación | Alcance | Estado |
| --- | --- | --- |
| 004 | Captación de leads | Commit 184dac2 |
| 005 | Persistencia PostgreSQL unificada | Commit 91168cf |
| 006 | Servicios comerciales claros ES/EN | Commit 77bf6bb |
| 007 | Login, roles, sesiones, acceso ES/EN | Activada localmente; commit e825124 |
| 008 | Panel de administrador: listar, crear y activar negocios; asignar usuarios | Commit 7a99ee0; activo localmente |
| 009 | Panel de cliente: servicios, duración, consulta de reservas y horarios | Implementado en d429249 |
| 010a | Agenda por profesional y reservas por enlace | Implementado para validación local |
| 010b | LangGraph: chat web de reservas con confirmación explícita | Implementado en desarrollo local (SPEC 010b) |
| 011 | RAG básico con documentos separados por empresa y referencias | Pendiente |
| 012 | Evaluación, documentación, slides y guion del vídeo | Pendiente |

La numeración propuesta en el chat se desplaza porque SPEC-006 ya existía.
No se anuncian login, paneles o IA como desplegados por haberlos especificado.

## Condiciones del flujo final

- Super Admin administra negocios. Cada business_admin solo opera sobre su empresa.
- El agente recibe la empresa del contexto autenticado, nunca de una instrucción del usuario o documento.
- Debe pedir datos faltantes y confirmar la operación antes de reservar; solo comunica éxito tras confirmación del backend.
– La agenda por profesional verifica horarios, duración y solapamientos antes de confirmar. El agente será un canal posterior.
- RAG filtra documentos por negocio y reconoce información insuficiente.
- Objetivo de evaluación: 30 escenarios (10 informativos, 10 reservas, 10 adversos), con resultados reales, latencia y consumo observados.
- WhatsApp, voz, pagos, suscripciones y n8n complejo quedan fuera del TFM.

## Entrega académica

Según el texto de requisitos proporcionado por el usuario: README completo, código
fuente en GitHub, slides y vídeo explicativo con captura de pantalla. Despliegue
recomendado si es viable. Incluir enlaces y cuentas exclusivamente de demostración
cuando estén preparados. No publicar contraseñas reales ni inventar resultados.
No se ha enviado la entrega ni compartido acceso con terceros.
