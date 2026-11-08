# SPEC-004 — Captación de clientes potenciales

## 1. Objetivo

Permitir que visitantes de la página corporativa de
ORQENTIVA Technologies envíen solicitudes comerciales.

Las solicitudes válidas se almacenarán en PostgreSQL
para su posterior gestión administrativa.

## 2. Actores

- Visitante: completa y envía el formulario.
- Administrador: gestiona las oportunidades comerciales.

## 3. Datos del formulario

- name: nombre del contacto (obligatorio).
- email: correo electrónico (obligatorio).
- company: nombre de la empresa (opcional).
- service: servicio de interés (obligatorio).
- message: descripción del proyecto (obligatorio).

## 4. Reglas de negocio

RN-01: El nombre debe tener entre 2 y 100 caracteres.
RN-02: El correo debe tener un formato válido.
RN-03: El mensaje debe tener entre 10 y 2000 caracteres.
RN-04: El servicio debe pertenecer al catálogo permitido.
RN-05: El servidor debe validar todos los datos.
RN-06: El endpoint público no debe requerir
las API keys privadas de las empresas.
RN-07: La plataforma debe limitar los envíos abusivos.
RN-08: Los datos enviados no deben aparecer en logs
ni respuestas públicas innecesarias.

### Decisiones del incremento verificado

- Catálogo: `agents`, `automation`, `growth`, `saas`.
- Recortar espacios antes de validar; empresa opcional, máximo 150 caracteres;
  correo máximo 254 caracteres. Rechazar campos adicionales.
- HTTP 201 devuelve únicamente `{"status":"created"}`.
- HTTP 422 no refleja los datos personales rechazados; HTTP 503 oculta errores SQL.
- Límite básico: 5 solicitudes válidas por IP en 60 segundos, por proceso;
  HTTP 429 con Retry-After. No equivale a protección distribuida.
- React utiliza `/leads` en el mismo origen. Vite lo reenvía a la API local.
  En despliegue debe configurarse la ruta equivalente; no se habilita CORS abierto.

## 5. Criterios de aceptación

AC-01: Se puede completar el formulario en español.
AC-02: Se puede completar el formulario en inglés.
AC-03: Los campos obligatorios se validan.
AC-04: Un formulario válido se envía a POST /leads.
AC-05: La API devuelve HTTP 201 al crear un lead.
AC-06: El lead se almacena en PostgreSQL.
AC-07: Los datos incorrectos reciben HTTP 422.
AC-08: El formulario muestra errores de conexión.
AC-09: Se puede comprobar la creación mediante
pruebas automatizadas.
AC-10: Se implementa una protección básica
contra envíos automatizados abusivos.
AC-11: El endpoint público no permite consultar
ni enumerar los leads registrados.
AC-12: Se informa al visitante del uso previsto
de sus datos antes de enviarlos.

## 6. Fuera del alcance inicial

- Pagos y suscripciones.
- CRM completo.
- Envío automático de correos comerciales.
- Panel administrativo para gestionar leads.
- Agentes autónomos para seguimiento de ventas.

## 7. Definición de terminado

- Requisitos implementados.
- Pruebas automatizadas aprobadas.
- Frontend compilando sin errores.
- Migración de PostgreSQL aplicada.
- Verificación manual completada.
- Commit registrado en Git.
