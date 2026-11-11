# Verificación consolidada del TFM

Fecha: 10 de noviembre de 2026, Costa Rica.

## Alcance

Se revisa la implementación local basada en 11f075b (rama mejoras-chat), con las
correcciones de esta consolidación. La evidencia forma parte del commit que contiene
este informe. Se integra el trabajo mediante el PR #1 hacia main. No se modifica
.env ni se restablecen contraseñas ni se sobrescriben bases existentes.

## Correcciones

- La demo admite Origin http://127.0.0.1:5179 y http://localhost:5179. Cada hostname
  tiene su cookie; mantener el mismo durante la sesión. Reiniciar el componente api
  para aplicar el cambio si ya estaba ejecutándose.
- FastAPI registra únicamente los archivos reales de la compilación. Se elimina
  la ruta comodín que convertía GET /leads en 404 en lugar de 405. Se conserva el
  encabezado Allow y las rutas de API no pueden ser ocultadas por un archivo.
- README, arquitectura, charter y alcance distinguen extracción para reservas,
  generación documental con citas y respaldo extractivo. Las specs históricas
  enlazan la ampliación SPEC-015.
- Se conserva el informe histórico de 137 pruebas sin atribuirle la cobertura actual.

## Resultados

| Verificación | Resultado |
| --- | --- |
| Suite Python | 240 pruebas aprobadas; incluye dos regresiones con/sin frontend compilado |
| Compilación TypeScript/Vite | Aprobada |
| Lint oxlint | Aprobado |
| PostgreSQL 17 temporal con frontend compilado | Aprobado, incluido GET /leads = 405 |
| Credenciales de demo existentes | Admin, Alfa y Beta verificadas sobre copia aislada; login, identidad, panel y logout |
| Extracción con LLM real | 39/40 casos completos con reglas + LLM; 0 llamadas fallidas |
| Latencia del LLM | Mediana 1,46 s; p95 1,95 s; máxima 2,06 s |

Evidencias: [pytest](evaluation-final-tests.xml), [PostgreSQL](evaluation-final-postgres.txt),
[evaluación LLM](evaluation-017/informe-extraccion.md).

La suite y PostgreSQL usan bases temporales. El proveedor real solo recibe casos
ficticios de extracción. No se midieron tokens/coste, carga de producción ni calidad
semántica del RAG con modelo real. El LLM confundió en un caso el nombre de la
profesional con el del cliente; no se afirma exactitud perfecta.

## Revisión visual: incompleta

Se abrió en Edge la web compilada de una instancia aislada con copia de la base,
en http://localhost:8013/#login. Se verificó visualmente el formulario de acceso en
escritorio. La automatización del navegador falló al pulsar el acceso y finalmente
se detuvo porque no podía verificar con suficiente confianza la URL de la ventana.
No se certifica el recorrido visual de paneles, confirmación de reservas ni móvil.
Las comprobaciones por API no sustituyen ese recorrido.

Para completar manualmente: iniciar sesión como Alfa y Beta; revisar ambos paneles;
abrir el enlace público, reservar Corte demo con contacto ficticio y confirmar;
comprobar la cita en agenda y el rechazo del mismo turno; consultar Cancelaciones
durante otro borrador; repetir en ancho móvil y verificar cierre de sesión.

## Estado académico

Presentación y vídeo excluidos de esta intervención por instrucción del autor.
No se inventaron enlaces ni se declara realizada la entrega. El despliegue público
no está realizado y WhatsApp sigue como piloto sin conexión Meta real. La revisión
no certifica cumplimiento de una rúbrica externa ni seguridad de producción.
