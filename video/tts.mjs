// Genera la narración de cada escena con la API de ElevenLabs y la guarda en video/audio.
// La clave y la voz se leen solo de las variables de entorno ELEVENLABS_API_KEY y
// ELEVENLABS_VOICE_ID; no se escriben en ningún archivo.
// Solo vuelve a pedir el audio de las escenas cuyo texto ha cambiado.
// Para repetir la toma de una escena concreta:  npm run voz -- s1-problema
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { AUDIO, script, spoken } from './lib.mjs';

const API = process.env.ELEVENLABS_API_URL || 'https://api.elevenlabs.io';
const MODEL = process.env.ELEVENLABS_MODEL || 'eleven_multilingual_v2';
const key = process.env.ELEVENLABS_API_KEY, voice = process.env.ELEVENLABS_VOICE_ID;
const force = process.argv.includes('--force');
const chosen = process.argv.slice(2).filter(arg => !arg.startsWith('--'));
const unknown = chosen.filter(id => !script.scenes.some(s => s.id === id));
if (unknown.length) {
  console.error(`Escena desconocida: ${unknown.join(', ')}. Disponibles: ${script.scenes.map(s => s.id).join(', ')}.`);
  process.exit(1);
}
const texts = script.scenes.map(s => spoken(s.narration));
const digest = text => crypto.createHash('sha256').update(MODEL + '\n' + text).digest('hex').slice(0, 16);

fs.mkdirSync(AUDIO, { recursive: true });
const pending = script.scenes.map((scene, i) => ({ scene, i, mp3: path.join(AUDIO, scene.id + '.mp3'), mark: path.join(AUDIO, scene.id + '.hash') }))
  .filter(({ scene, i, mp3, mark }) => force || chosen.includes(scene.id) || !fs.existsSync(mp3) || !fs.existsSync(mark) || fs.readFileSync(mark, 'utf8').trim() !== digest(texts[i]));

if (!pending.length) {
  console.log('Narración al día: no hay escenas con texto nuevo.');
  process.exit(0);
}
if (!key || !voice) {
  const missing = [!key && 'ELEVENLABS_API_KEY', !voice && 'ELEVENLABS_VOICE_ID'].filter(Boolean).join(' y ');
  console.error(`Falta definir ${missing} en el entorno. Escenas sin audio actualizado: ${pending.map(p => p.scene.id).join(', ')}.`);
  process.exit(2);
}

for (const { scene, i, mp3, mark } of pending) {
  const response = await fetch(`${API}/v1/text-to-speech/${encodeURIComponent(voice)}?output_format=mp3_44100_128`, {
    method: 'POST',
    headers: { 'xi-api-key': key, 'Content-Type': 'application/json', Accept: 'audio/mpeg' },
    body: JSON.stringify({
      text: texts[i],
      model_id: MODEL,
      // El contexto ayuda a que la entonación enlace con las escenas vecinas.
      previous_text: texts[i - 1] ?? undefined,
      next_text: texts[i + 1] ?? undefined,
      // Estabilidad alta y sin estilo añadido: menos muletillas y sonidos improvisados al empezar.
      voice_settings: { stability: 0.65, similarity_boost: 0.8, style: 0, use_speaker_boost: true },
    }),
  });
  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    console.error(`ElevenLabs rechazó la escena ${scene.id} (HTTP ${response.status}): ${detail}`);
    process.exit(1);
  }
  fs.writeFileSync(mp3, Buffer.from(await response.arrayBuffer()));
  fs.writeFileSync(mark, digest(texts[i]) + '\n');
  console.log(`${scene.id}: narración generada`);
}
