// Utilidades compartidas por los pasos del video: rutas, guion, duraciones y subtítulos.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const VIDEO = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.dirname(VIDEO);
export const WORK = path.join(VIDEO, '.work');
export const OUT = path.join(VIDEO, 'out');
export const AUDIO = path.join(VIDEO, 'audio');
// ffmpeg: variable de entorno, paquete ffmpeg-static (si está instalado) o el del sistema.
const bundled = async (name, pick) => { try { return pick(await import(name)); } catch { return null; } };
export const FFMPEG = process.env.FFMPEG || (await bundled('ffmpeg-static', m => m.default)) || 'ffmpeg';
export const FFPROBE = process.env.FFPROBE || (await bundled('ffprobe-static', m => m.default.path)) || 'ffprobe';
export const WIDTH = 1920, HEIGHT = 1080, FPS = 30;
// La página se graba ampliada un 25 % (zoom CSS) para que el texto se lea en móvil.
export const PAGE_ZOOM = 1.25;

export const script = JSON.parse(fs.readFileSync(path.join(VIDEO, 'scenes.json'), 'utf8'));
/** Texto que se envía a la voz sintética: la marca se escribe como se pronuncia. */
export const spoken = text => Object.entries(script.pronunciation || {}).reduce((t, [from, to]) => t.replaceAll(from, to), text);
export const chapterLabel = id => script.chapters.find(c => c.id === id).label;

export function ffmpeg(args, quiet = true) {
  execFileSync(FFMPEG, ['-hide_banner', '-loglevel', quiet ? 'error' : 'info', '-y', ...args], { stdio: 'inherit' });
}

export function mediaSeconds(file) {
  const out = execFileSync(FFPROBE, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file]);
  return Number(String(out).trim());
}

const words = text => text.trim().split(/\s+/).length;

/** Duración de cada escena: la de su audio si existe; si no, una estimación por número de palabras. */
export function sceneDurations() {
  return script.scenes.map(scene => {
    const audio = path.join(AUDIO, scene.id + '.mp3');
    if (fs.existsSync(audio)) return { id: scene.id, seconds: Math.round((mediaSeconds(audio) + 0.9) * 100) / 100, source: 'audio' };
    return { id: scene.id, seconds: Math.round((words(scene.narration) / 2.5 + 0.9) * 100) / 100, source: 'estimada' };
  });
}

/** Parte la narración en subtítulos de hasta ~2 líneas, cortando en la puntuación. */
export function cues(narration, max = 78) {
  const parts = narration.match(/[^,.;:?!»”]+[,.;:?!»”]*\s*/g).map(p => p.trim()).filter(Boolean);
  const out = [];
  for (const part of parts) {
    const last = out.at(-1);
    const sentenceEnd = last && /[.?!»”]$/.test(last);
    if (last && !sentenceEnd && (last + ' ' + part).length <= max) out[out.length - 1] = last + ' ' + part;
    else if (last && sentenceEnd && last.length < 28 && (last + ' ' + part).length <= max) out[out.length - 1] = last + ' ' + part;
    else out.push(part);
  }
  return out;
}

/** Subtítulos de todo el video con tiempos repartidos según la longitud de cada frase. */
export function timedCues(durations, lead = 0.25, tail = 0.55, field = 'narration') {
  const result = [];
  let offset = 0;
  script.scenes.forEach((scene, i) => {
    const total = durations[i].seconds;
    const texts = cues(scene[field]);
    const chars = texts.reduce((n, t) => n + t.length, 0);
    let t = offset + lead;
    const span = total - lead - tail;
    for (const text of texts) {
      const d = span * (text.length / chars);
      result.push({ start: t, end: t + d - 0.04, text });
      t += d;
    }
    offset += total;
  });
  return result;
}

const stamp = (s, sep) => {
  const ms = Math.round(s * 1000);
  const pad = (n, l = 2) => String(n).padStart(l, '0');
  return `${pad(Math.floor(ms / 3600000))}:${pad(Math.floor(ms / 60000) % 60)}:${pad(Math.floor(ms / 1000) % 60)}${sep}${pad(ms % 1000, 3)}`;
};

/** Divide un subtítulo en dos líneas equilibradas si es largo. */
export function twoLines(text, limit = 42) {
  if (text.length <= limit) return text;
  const mid = text.length / 2;
  let best = -1;
  for (let i = 0; i < text.length; i++) if (text[i] === ' ' && (best < 0 || Math.abs(i - mid) < Math.abs(best - mid))) best = i;
  return best < 0 ? text : text.slice(0, best) + '\n' + text.slice(best + 1);
}

export const toSrt = list => list.map((c, i) => `${i + 1}\n${stamp(c.start, ',')} --> ${stamp(c.end, ',')}\n${twoLines(c.text)}\n`).join('\n');
export const toVtt = list => 'WEBVTT\n\n' + list.map(c => `${stamp(c.start, '.')} --> ${stamp(c.end, '.')}\n${twoLines(c.text)}\n`).join('\n');
