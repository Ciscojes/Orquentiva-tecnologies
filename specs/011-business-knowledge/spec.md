# Información pública por negocio

> Alcance histórico de este incremento. SPEC-015 amplía la consulta documental con generación opcional mediante LLM y citas verificadas; las restricciones extractivas de este documento no describen todo el estado actual.

El dueño escribe documentos de texto con título, organizados en párrafos y guardados como borrador por defecto. Puede publicar, actualizar o retirar cada documento. La empresa procede de la sesión privada.
El visitante consulta desde el chat del negocio habilitado. Las preguntas sobre políticas se reconocen directamente; un selector permite consultar otros temas. La recuperación léxica filtra por empresa y publicación antes de puntuar párrafos. La respuesta extractiva muestra texto literal, título y número de párrafo. Con evidencia insuficiente se pide consultar al negocio. Sin proveedor externo ni escritura en reservas. Se buscan palabras y equivalencias frecuentes ES/EN y se citan los párrafos en el idioma publicado. No se traducen ni se generan políticas.

Verificación: 107 pruebas, migración PostgreSQL 17 temporal, compilación y lint. En Edge se publicó una regla de prueba desde el panel y se comprobó que el visitante en móvil recibió el texto y la referencia. Consultar durante una reserva conserva el borrador y requiere retomar el flujo para confirmarla.
