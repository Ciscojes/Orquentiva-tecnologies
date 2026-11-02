# Correcciones de regresión detectadas durante Sprint 04

## Problemas reproducidos

- Un nombre formado solo por espacios producía una reserva con nombre vacío.
- Dos fechas que representan el mismo instante con offsets distintos producían dos reservas.
- Ordenar las fechas por texto no garantizaba el orden cronológico con offsets diferentes.

## Comportamiento acordado para las correcciones

1. Quitar espacios antes de validar la longitud del nombre (1–100 caracteres).
2. Guardar fechas nuevas en UTC; mantener el requisito de zona horaria.
3. Comparar por instante contra reservas antiguas sin reescribirlas.
4. Rechazar con HTTP 409 la segunda reserva del mismo instante para la misma empresa.
5. Serializar comprobación e inserción para que dos solicitudes simultáneas no dupliquen reservas.
6. Mantener aislamiento entre empresas y precisión de microsegundos.
7. Ordenar el listado por instante, incluyendo fechas antiguas con offsets diferentes.

## Verificación

Diez casos añadidos en tests/test_appointment_regressions.py, con SQLite temporal
por prueba. La operación se serializa con BEGIN IMMEDIATE. La comparación de
fechas antiguas recorre las reservas de la empresa: es una solución para el
prototipo; la migración futura a PostgreSQL debe conservar una restricción única
por empresa e instante. No se modifican registros de las bases existentes.
