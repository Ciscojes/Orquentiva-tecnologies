# Video de presentación

Genera el video comercial de ORQENTIVA a partir de la aplicación en local. Todos los datos que aparecen son ficticios (`seed_demo.py`).

## Preparación (una sola vez)

Requiere el entorno habitual del proyecto: `.venv` con `requirements.txt` instalado y `npm ci` hecho en `frontend/`.

```powershell
Set-Location video
npm install
npm run preparar   # descarga el navegador Chromium de Playwright
```

## Regenerar el video

```powershell
Set-Location video
npm run video
```

El comando crea una base SQLite ficticia, levanta la API (puerto 8003) y el frontend (puerto 5180), genera la narración, graba las escenas a 1920x1080 y monta el resultado en `video/out/`:

| Archivo | Uso |
| --- | --- |
| `orqentiva-presentacion.mp4` | Versión para la web (subtítulos aparte) |
| `orqentiva-presentacion.subtitulado.mp4` | Versión para redes, con subtítulos incrustados |
| `orqentiva-presentacion.es.vtt`, `.en.vtt` | Subtítulos en español e inglés |
| `orqentiva-presentacion.chapters.json` | Inicio de cada capítulo |
| `orqentiva-presentacion.poster.jpg` | Imagen de portada |

Cuando el video tiene narración, el montaje también actualiza la página de inicio: copia el video, los subtítulos y la portada a `frontend/public/presentacion.*` y los capítulos a `frontend/src/assets/presentacion.json`. El reproductor está en `frontend/src/components/VideoPresentation.tsx`.

Opciones: `npm run video -- --sin-voz` no llama a ElevenLabs; `npm run video -- --con-ia` graba el chat con el LLM configurado en `.env` (por defecto usa solo reglas, para que el resultado sea siempre el mismo).

## Narración

`npm run voz` (o el propio `npm run video`) pide a ElevenLabs el audio de cada escena y lo guarda en `video/audio/`. Lee la clave y la voz de las variables de entorno `ELEVENLABS_API_KEY` y `ELEVENLABS_VOICE_ID`; no se guardan en ningún archivo. Solo se vuelven a pedir las escenas cuyo texto cambió (`npm run voz -- --force` las regenera todas). Sin esas variables, el video se monta con los audios que ya existan, o mudo.

Cada escena se graba con la duración de su audio, así que tras cambiar la narración hay que ejecutar `npm run video` completo.

## Qué editar

- `scenes.json`: guion (`narration`), su traducción para los subtítulos en inglés (`narration_en`), títulos, capítulos y pronunciación de la marca.
- `record.mjs`: qué hace el cursor en cada escena (selectores de la interfaz).
- `overlay.js`: aspecto de títulos, resaltados, cartelas y cursor.
- `seed_demo.py`: datos ficticios de la demostración.

La escena de WhatsApp es una ilustración y lo indica en pantalla: esa función todavía no está conectada.
