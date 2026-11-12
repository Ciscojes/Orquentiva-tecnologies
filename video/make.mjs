// Regenera el video completo con un solo comando:  npm run video   (desde la carpeta video/)
// Pasos: base de demostración ficticia -> API y frontend en local -> narración -> grabación -> montaje.
// Opciones: --sin-voz (no llama a ElevenLabs), --con-ia (usa el LLM configurado en .env para el chat).
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { OUT, ROOT, VIDEO, WORK } from './lib.mjs';

const args = process.argv.slice(2);
const API_PORT = 8003, WEB_PORT = 5180;
const DB = path.join(WORK, 'demo.sqlite3');
const python = [path.join(ROOT, '.venv', 'Scripts', 'python.exe'), path.join(ROOT, '.venv', 'bin', 'python')].find(fs.existsSync)
  || (process.platform === 'win32' ? 'python' : 'python3');
const vite = path.join(ROOT, 'frontend', 'node_modules', 'vite', 'bin', 'vite.js');
if (!fs.existsSync(vite)) throw new Error('Faltan las dependencias del frontend: ejecuta "npm ci" en la carpeta frontend.');

const children = [];
const stop = () => children.forEach(child => { try { child.kill(); } catch { /* ya terminó */ } });
process.on('exit', stop);
process.on('SIGINT', () => process.exit(130));

function step(title, command, commandArgs, options = {}) {
  console.log(`\n== ${title}`);
  const result = spawnSync(command, commandArgs, { stdio: 'inherit', cwd: ROOT, ...options });
  return result.status ?? 1;
}
function serve(name, command, commandArgs, env, cwd) {
  const log = fs.openSync(path.join(WORK, name + '.log'), 'w');
  const child = spawn(command, commandArgs, { cwd, env: { ...process.env, ...env }, stdio: ['ignore', log, log] });
  child.on('exit', code => { if (code) console.error(`${name} terminó con código ${code}; revisa video/.work/${name}.log`); });
  children.push(child);
}
async function waitFor(url, label) {
  for (let i = 0; i < 80; i++) {
    try { if ((await fetch(url)).ok) return; } catch { /* aún arrancando */ }
    await new Promise(r => setTimeout(r, 500));
  }
  throw new Error(`${label} no respondió en ${url}. Revisa los registros en video/.work.`);
}

fs.mkdirSync(WORK, { recursive: true });
if (step('Datos de demostración ficticios', python, [path.join(VIDEO, 'seed_demo.py')])) process.exit(1);

console.log('\n== Aplicación en local');
// Sin --con-ia el chat usa solo reglas: el resultado es el mismo en cada ejecución.
const llm = args.includes('--con-ia') ? {} : { LLM_API_KEY: '', LLM_MODEL: '' };
serve('api', python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(API_PORT)], {
  DATABASE_URL: 'sqlite:///' + DB.replaceAll('\\', '/'), AUTH_COOKIE_SECURE: 'false',
  AUTH_ALLOWED_ORIGINS: `http://127.0.0.1:${WEB_PORT}`, ...llm,
}, ROOT);
serve('web', process.execPath, [vite, '--host', '127.0.0.1', '--port', String(WEB_PORT), '--strictPort'],
  { ORQENTIVA_API_TARGET: `http://127.0.0.1:${API_PORT}` }, path.join(ROOT, 'frontend'));
await waitFor(`http://127.0.0.1:${API_PORT}/health`, 'La API');
await waitFor(`http://127.0.0.1:${WEB_PORT}/`, 'El frontend');

const node = script => [process.execPath, [path.join(VIDEO, script)]];
if (!args.includes('--sin-voz')) {
  const status = step('Narración (ElevenLabs)', ...node('tts.mjs'));
  if (status === 2) console.log('Se continúa con los audios que ya existan en video/audio; las escenas sin audio quedarán mudas.');
  else if (status) process.exit(1);
}
if (step('Grabación', ...node('record.mjs'), { env: { ...process.env, VIDEO_BASE_URL: `http://127.0.0.1:${WEB_PORT}` } })) process.exit(1);
if (step('Montaje', ...node('compose.mjs'))) process.exit(1);
stop();
console.log(`\nListo. Archivos en ${path.relative(ROOT, OUT)}`);
process.exit(0);
