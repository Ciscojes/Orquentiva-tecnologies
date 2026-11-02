# TASKS-004 — Captación de leads

## SPEC

- [x] Definir requisitos funcionales.
- [x] Establecer criterios de aceptación.

## PLAN

- [x] Documentar arquitectura propuesta.
- [x] Revisar modelos y dependencias existentes.

## TEST

- [x] Configurar pruebas aisladas.
- [x] Probar validación del endpoint.
- [x] Probar creación y persistencia (SQLite temporal).
- [x] Probar medidas antiabuso.

## IMPLEMENT

- [x] Crear modelo Lead.
- [x] Crear migración Alembic.
- [x] Implementar POST /leads.
- [x] Conectar ContactForm.tsx.
- [x] Incorporar aviso de privacidad.

## VERIFY

- [x] Ejecutar pruebas backend.
- [x] Ejecutar npm run build y npm run lint.
- [x] Probar formulario ES/EN (envíos en entorno temporal aislado).
- [x] Verificar seguridad básica del endpoint de leads.
- [x] Consultar revisión y estructura PostgreSQL en modo solo lectura.
- [x] Probar escritura en PostgreSQL en una instancia temporal exclusiva de integración.
- [x] Corregir y probar nombres vacíos, equivalencia de zonas horarias y concurrencia en reservas.

## GIT

- [ ] Revisar cambios en Source Control.
- [ ] Registrar commit en español.
