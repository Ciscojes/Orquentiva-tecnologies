# PLAN-004 — Implementación técnica

## Arquitectura

Frontend:

- React + TypeScript
- ContactForm.tsx
- Fetch API para solicitudes HTTP

Backend:

- FastAPI
- Pydantic para validaciones
- SQLAlchemy para persistencia

Base de datos:

- PostgreSQL 17
- Alembic para migraciones

## Flujo principal

1. El visitante completa el formulario.
2. React valida los campos.
3. React envía POST /leads con JSON.
4. FastAPI valida los datos con Pydantic.
5. El backend aplica controles antiabuso.
6. SQLAlchemy registra el lead.
7. PostgreSQL guarda la información.
8. FastAPI responde con HTTP 201.
9. React presenta una confirmación.

## Seguridad

- No exponer credenciales en React.
- No reutilizar claves de autenticación privadas.
- Limitar frecuencia de solicitudes.
- Restringir CORS a los orígenes autorizados.
- Incremento local: mismo origen mediante proxy Vite para /leads, sin CORS abierto.
- Validar los datos en el backend.
- No crear endpoints públicos para listar leads.
- Preparar información de privacidad y consentimiento.

## Dependencias

- Revisar integración actual con PostgreSQL.
- Confirmar configuración de Alembic.
- Adaptar las pruebas a una base de datos aislada.

## Estrategia

Implementar incrementalmente, verificando cada cambio
sin romper los endpoints existentes.
