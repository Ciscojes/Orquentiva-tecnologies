# Verificación del paquete de entrega

Fecha de referencia: 6 de noviembre de 2026, Costa Rica. Este documento amplía el informe inicial de docs/evaluation-012, que se conserva como registro histórico.

## Resultados comprobados

| Comprobación | Resultado y alcance |
| --- | --- |
| pytest | 137 aprobadas en la ejecución registrada. Incluye 30 escenarios de aceptación y 107 pruebas anteriores. Bases SQLite temporales. |
| PostgreSQL temporal | Migraciones hasta head y downgrade, modelos, cuentas, roles, paneles, reservas concurrentes, documentos, chat, confirmación, reintentos, conflicto y logout aprobados. Servidor temporal detenido al terminar. |
| Frontend | npm run build y npm run lint completados correctamente, también tras añadir la selección del backend de demostración. |
| Preparación de demo | Base nueva creada con migraciones, datos ficticios y cuentas de prueba. No se utilizó .env. |
| Navegador de escritorio | Edge automatizado, 1440 × 1000: login administrador y Alfa, consulta de política durante reserva, retorno al modo reservas, confirmación y cita visible en panel. |
| Vista móvil | Edge automatizado, 390 × 844: consulta en Beta devuelve su política de 48 horas, sin desbordamiento horizontal. |
| Errores JavaScript | Ninguno registrado por pageerror durante el recorrido que finalizó correctamente. |
| Presentación | 12 diapositivas editables exportadas a PPTX y vistas previas revisadas. No se ha abierto en PowerPoint de escritorio. |

Los intentos iniciales de automatización de navegador se detuvieron por selectores demasiado estrictos al buscar textos dentro de párrafos o citas con elementos hijos. Se corrigieron los selectores de comprobación; no se cambió la lógica de la aplicación. El recorrido final terminó con código 0 y guardó browser-results.json.

## Evidencias

- docs/evaluation-012/full-results.xml y escenarios.csv: ejecución original.
- postgres-tfm.log: verificación PostgreSQL ampliada.
- browser-results.json: resultado del recorrido de navegador.
- capturas/: pantallas reales de la demo con datos ficticios.

## Límites de la validación

La revisión móvil corresponde a una anchura de 390 px y al recorrido indicado, no a todos los dispositivos. La captura de página completa puede mostrar la cabecera fija en la posición de scroll; no representa una maquetación nueva. No se ha medido carga de producción, p95 de peticiones ni mejora comercial. La instalación desde cero en otro equipo sigue pendiente: se utilizaron dependencias ya instaladas para las pruebas.

Los 137 tests no constituyen una auditoría de seguridad. El flujo actual no llama a un LLM. Publicación, vídeo, comprobación de enlaces públicos y envío académico siguen pendientes.
