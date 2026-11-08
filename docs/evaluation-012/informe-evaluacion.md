# ORQENTIVA — Evaluación inicial del Sprint 012

Fecha: 6 de noviembre de 2026 (Costa Rica).

## Resultado comprobado

- 30/30 escenarios de aceptación aprobados: 10 informativos, 10 de reservas y 10 adversos.
- Suite completa: 137 pruebas aprobadas, 0 fallos y 0 errores (incluye los 30 escenarios nuevos; 107 pruebas anteriores).
- La ejecución completa terminó en 21,22 segundos según pytest. La ejecución independiente de los 30 escenarios terminó en 11,99 segundos.
- No se necesitaron cambios en la lógica de la aplicación para superar estos escenarios.

## Método y límites

Se evaluó una copia de los archivos locales del proyecto, cuyo último commit leído fue cb56f70. No se confirmó que el árbol original estuviera limpio: este informe no certifica que todos los archivos coincidan exactamente con ese commit.

Entorno: Windows, Python 3.13.5, pytest 9.2.0, FastAPI TestClient y bases SQLite temporales creadas por las fixtures existentes. Se reutilizaron las dependencias instaladas del proyecto. No se copió .env ni se usaron bases de demostración. Los datos se prepararon de nuevo para cada escenario; se usó una fecha de reserva siete días posterior a la fecha local de ejecución.

Los primeros intentos quedaron bloqueados al crear el bucle asíncrono bajo las restricciones del entorno. Se detuvieron; la ejecución con acceso local ampliado completó las pruebas. No se contabilizan aquellos intentos como aprobados ni como fallos del producto.

Las duraciones de la tabla miden el conjunto de solicitudes y verificaciones de cada escenario mediante perf_counter, excluyendo la preparación de datos. Algunos escenarios incluyen varias solicitudes. Son una muestra por escenario de la ejecución completa: NO representan latencia de una petición, p95, carga concurrente de producción ni velocidad del navegador.

El chat actual usa un grafo guiado y recuperación léxica/extractiva. No invoca modelos externos en estos recorridos: no aplica un consumo de tokens de LLM; no se midieron CPU, memoria ni coste de infraestructura. El valor cero de llamadas externas documentado por el test describe esta implementación, no una medición mediante un contador de facturación.

El bloque de reservas prueba la API de confirmación y la ausencia de escrituras del chat. La acción de pulsar el botón de confirmación y la conservación del borrador en React requieren una prueba de navegador. El caso R10 comprueba que la API permite reenviar el borrador, no su persistencia visual automática. Los casos adversos son una muestra de aceptación, no una auditoría completa de seguridad.

## Escenarios observados

| Caso | Criterio | Resultado | Duración del escenario (ms) |
| --- | --- | --- | ---: |
| I01 | Política de cancelación con cita exacta | APROBADO | 13.47 |
| I02 | Pregunta equivalente en inglés | APROBADO | 12.76 |
| I03 | Consulta de efectivo | APROBADO | 16.13 |
| I04 | Información insuficiente sin inventar respuesta | APROBADO | 9.69 |
| I05 | Documento borrador no visible | APROBADO | 46.43 |
| I06 | Documento retirado no visible | APROBADO | 35.83 |
| I07 | Actualización de política reflejada | APROBADO | 21.14 |
| I08 | Referencia al segundo párrafo | APROBADO | 14.12 |
| I09 | Consulta no crea reservas | APROBADO | 19.9 |
| I10 | Pregunta sin evidencia en inglés | APROBADO | 10.26 |
| R01 | Solicita servicio faltante | APROBADO | 8.16 |
| R02 | Solicita fecha faltante | APROBADO | 7.85 |
| R03 | Ofrece horas disponibles | APROBADO | 15.29 |
| R04 | Solicita nombre faltante | APROBADO | 12.8 |
| R05 | Presenta propuesta sin guardar reserva | APROBADO | 24.25 |
| R06 | Confirmación explícita guarda una reserva | APROBADO | 38.04 |
| R07 | Reintento idéntico no duplica reserva | APROBADO | 41.82 |
| R08 | Turno ocupado ofrece alternativas | APROBADO | 41.87 |
| R09 | Fecha pasada no produce propuesta | APROBADO | 10.65 |
| R10 | Consulta durante reserva permite retomar borrador | APROBADO | 36.98 |
| A01 | Beta no recupera documentos de Alfa | APROBADO | 8.6 |
| A02 | Beta no modifica documento de Alfa | APROBADO | 7.53 |
| A03 | Visitante no publica documentos | APROBADO | 2.88 |
| A04 | Empresa enviada en cuerpo es rechazada | APROBADO | 5.74 |
| A05 | Borrador de Alfa no reserva en Beta | APROBADO | 9.57 |
| A06 | Agenda desactivada rechaza consultas | APROBADO | 16.35 |
| A07 | Mensaje demasiado largo rechazado | APROBADO | 3.49 |
| A08 | Horario inválido rechazado | APROBADO | 4.12 |
| A09 | Instrucción de revelar otra empresa no filtra datos | APROBADO | 17.01 |
| A10 | Segunda solicitud al mismo turno rechazada | APROBADO | 34.66 |

## Reproducir

Desde la raíz del repositorio, con el entorno virtual activado:

```powershell
python -m pytest tests/test_evaluation_012.py -q -p no:cacheprovider -o junit_family=legacy --junitxml=evaluation-results.xml
python -m pytest -q -p no:cacheprovider -o junit_family=legacy --junitxml=full-results.xml
```

Las fixtures existentes aíslan las bases de datos; no usar credenciales de producción para estos comandos.

## Pendientes para cerrar el Sprint 012

1. Validación visual en escritorio y móvil: login, ambos paneles, reservas, confirmación, conflicto y consulta de documentos durante una reserva.
2. Validar con PostgreSQL y el entorno de despliegue: las pruebas de esta ejecución usan SQLite y no certifican bloqueos/transacciones reales de PostgreSQL.
3. Revisar compilación del frontend y realizar una demostración manual completa con Alfa y Beta.
4. Actualizar el README, preparar diapositivas y guion del vídeo con estas evidencias y limitaciones.
5. Decidir el despliegue y preparar exclusivamente cuentas y datos de demostración.

El Sprint 012 queda iniciado, con evaluación automatizada completada; no queda cerrado ni se ha publicado la aplicación.
