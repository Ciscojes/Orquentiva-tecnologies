# Verificación — SPEC-006

- `npm run build`: correcto (TypeScript y Vite).
- `npm run lint`: correcto.
- `pytest -q`: 42 pruebas aprobadas con bases temporales. Un aviso de deprecación de Starlette/httpx; no se cambian dependencias en este incremento.
- `git diff --check`: correcto.
- Edge sin interfaz, servido desde Vite local: cuatro desplegables abiertos con Enter y seis apartados por servicio.
- Cambio ES/EN: conserva desplegables abiertos, nombre y servicio elegidos; traducción del selector y errores coherente.
- Cuatro enlaces de asesoría: destino #contact comprobado.
- POST /leads interceptado en navegador: respuesta 201 muestra confirmación y limpia campos; 429 muestra aviso. Se conservan los valores growth y saas del contrato. No se envió ninguna solicitud al backend.
- Preferencia de idioma conservada al recargar.
- Sin errores JavaScript ni desbordamiento horizontal a 1440, 768, 390 y 320 píxeles. Capturas de escritorio y móvil revisadas.
- Prueba de navegador ejecutada desde herramienta auxiliar fuera del repositorio; no se añadieron dependencias. La compilación y pytest son repetibles con los comandos existentes.

## Revisión manual reproducible

1. Ejecutar el frontend y abrir Servicios.
2. Recorrer «Conocer el servicio» con Tab y abrir/cerrar con Enter.
3. Revisar contenido en ES y EN, incluidos alcance, ejemplos y proceso.
4. Pulsar «Solicitar asesoría» y elegir el servicio en el formulario.
5. Escribir un borrador y cambiar idioma: los campos deben conservarse.
6. Revisar móvil y escritorio. Para probar envíos, usar un entorno aislado o respuestas simuladas.

## Estado

Implementación lista para revisión y commit manual. No se modificó backend, esquema ni datos. No se desplegó el sitio.
Mensaje sugerido: `mejorar presentación comercial bilingüe de servicios con SDD`.
