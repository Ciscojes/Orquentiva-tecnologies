// Une las escenas grabadas con su narración y genera los archivos finales en video/out.
// Genera dos versiones: la de la web (subtítulos aparte, en .vtt) y la de redes (subtítulos incrustados).
import fs from 'node:fs';
import path from 'node:path';
import { AUDIO, OUT, ROOT, WORK, ffmpeg, mediaSeconds, script, timedCues, toSrt, toVtt } from './lib.mjs';

const NAME = 'orqentiva-presentacion';
const LEAD = 0.3; // silencio antes de cada narración
fs.mkdirSync(OUT, { recursive: true });

const scenes = script.scenes.map(scene => {
  const file = path.join(WORK, 'scenes', scene.id + '.mp4');
  if (!fs.existsSync(file)) throw new Error(`Falta la escena grabada ${scene.id}. Ejecuta antes la grabación.`);
  return { ...scene, file, seconds: mediaSeconds(file), audio: path.join(AUDIO, scene.id + '.mp3') };
});
const total = scenes.reduce((n, s) => n + s.seconds, 0);

// 1. Imagen: todas las escenas seguidas.
const list = path.join(WORK, 'scenes.txt');
fs.writeFileSync(list, scenes.map(s => `file '${s.file.replaceAll('\\', '/')}'`).join('\n') + '\n');
const silent = path.join(WORK, 'silent.mp4');
ffmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', silent]);

// 2. Sonido: cada narración empieza con su escena; si falta alguna, el video queda mudo.
const voiced = scenes.every(s => fs.existsSync(s.audio));
let track = null;
if (voiced) {
  const parts = scenes.map(s => {
    const wav = path.join(WORK, 'scenes', s.id + '.wav');
    ffmpeg(['-i', s.audio, '-af', `adelay=${LEAD * 1000}:all=1,apad`, '-t', s.seconds.toFixed(3), '-ar', '48000', '-ac', '2', wav]);
    return wav;
  });
  const audioList = path.join(WORK, 'audio.txt');
  fs.writeFileSync(audioList, parts.map(f => `file '${f.replaceAll('\\', '/')}'`).join('\n') + '\n');
  track = path.join(WORK, 'narration.wav');
  ffmpeg(['-f', 'concat', '-safe', '0', '-i', audioList, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', track]);
} else {
  const missing = scenes.filter(s => !fs.existsSync(s.audio)).map(s => s.id);
  console.log(`Sin narración (faltan ${missing.length} audios en video/audio): el video se genera mudo.`);
}

// 3. Subtítulos, capítulos y portada.
const seconds = scenes.map(s => ({ seconds: s.seconds }));
const cueList = timedCues(seconds, voiced ? LEAD : 0.25);
fs.writeFileSync(path.join(OUT, NAME + '.es.vtt'), toVtt(cueList));
fs.writeFileSync(path.join(OUT, NAME + '.en.vtt'), toVtt(timedCues(seconds, voiced ? LEAD : 0.25, 0.55, 'narration_en')));
const srt = path.join(WORK, 'subtitles.srt');
fs.writeFileSync(srt, toSrt(cueList));
let at = 0;
const chapters = [];
for (const s of scenes) {
  if (chapters.at(-1)?.id !== s.chapter) {
    const chapter = script.chapters.find(c => c.id === s.chapter);
    chapters.push({ id: chapter.id, es: chapter.label, en: chapter.label_en, start: Math.round(at * 100) / 100 });
  }
  at += s.seconds;
}
fs.writeFileSync(path.join(OUT, NAME + '.chapters.json'), JSON.stringify({ duration: Math.round(total * 100) / 100, chapters }, null, 2) + '\n');
const posterAt = scenes[0].seconds + scenes[1].seconds * 0.78;
ffmpeg(['-ss', posterAt.toFixed(2), '-i', silent, '-frames:v', '1', '-vf', 'scale=1280:-2', '-q:v', '3', path.join(OUT, NAME + '.poster.jpg')]);

// 4. Versión para la web y versión para redes con los subtítulos incrustados.
const audioIn = track ? ['-i', track] : [];
const audioOut = track ? ['-c:a', 'aac', '-b:a', '128k'] : ['-an'];
const final = path.join(OUT, NAME + '.mp4');
ffmpeg(['-i', silent, ...audioIn, '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-pix_fmt', 'yuv420p',
  '-g', '60', '-movflags', '+faststart', ...audioOut, final]);
console.log(`${path.relative(process.cwd(), final)}: ${total.toFixed(1)} s, ${(fs.statSync(final).size / 1048576).toFixed(1)} MB${voiced ? '' : ' (mudo)'}`);
{
  const style = "FontName=Inter,FontSize=13,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&HA0291F10,BorderStyle=4,Outline=0,Shadow=0,MarginV=22";
  const out = path.join(OUT, NAME + '.subtitulado.mp4');
  const srtArg = srt.replaceAll('\\', '/').replace(':', '\\:');
  ffmpeg(['-i', silent, ...audioIn, '-vf', `subtitles='${srtArg}':force_style='${style}'`, '-c:v', 'libx264', '-preset', 'medium',
    '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', ...audioOut, out]);
  console.log(`${path.relative(process.cwd(), out)}: versión para redes, con subtítulos incrustados`);
}

// 5. Publicación en la página: el frontend sirve estos archivos tal cual.
const PUBLIC = path.join(ROOT, 'frontend', 'public');
const copies = [
  ['.mp4', path.join(PUBLIC, 'presentacion.mp4')],
  ['.es.vtt', path.join(PUBLIC, 'presentacion.es.vtt')],
  ['.en.vtt', path.join(PUBLIC, 'presentacion.en.vtt')],
  ['.poster.jpg', path.join(PUBLIC, 'presentacion-poster.jpg')],
  ['.chapters.json', path.join(ROOT, 'frontend', 'src', 'assets', 'presentacion.json')],
];
if (voiced || process.argv.includes('--publicar')) {
  for (const [ext, target] of copies) fs.copyFileSync(path.join(OUT, NAME + ext), target);
  console.log('Página actualizada: frontend/public/presentacion.* y frontend/src/assets/presentacion.json');
} else {
  console.log('El video mudo no se copia a la página (usa --publicar para forzarlo).');
}
