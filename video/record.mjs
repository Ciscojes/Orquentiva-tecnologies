// Graba el recorrido de la demo escena por escena con Playwright (1920x1080).
// Requiere la API y el frontend de demostración en marcha (los levanta make.mjs).
// Uso: node video/record.mjs [id-de-escena ...]
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';
import { FPS, HEIGHT, PAGE_ZOOM, VIDEO, WIDTH, WORK, chapterLabel, ffmpeg, sceneDurations, script } from './lib.mjs';

const BASE = process.env.VIDEO_BASE_URL || 'http://127.0.0.1:5179';
const DEMO_USER = 'alfa@example.com';
// Contraseña de la demo local ficticia (la misma del README); no es una credencial real.
const DEMO_PASSWORD = 'Orqentiva-Demo-2026!';
const CHAT_MESSAGE = 'Quiero un corte clásico con Ana el sábado a las 10';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ease = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

const only = process.argv.slice(2);
const durations = sceneDurations();
fs.mkdirSync(path.join(WORK, 'scenes'), { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1, locale: 'es-CR', timezoneId: 'America/Costa_Rica',
});
await context.addInitScript(`window.__V_PAGE_ZOOM = ${PAGE_ZOOM};`);
await context.addInitScript({ path: path.join(VIDEO, 'overlay.js') });
const page = await context.newPage();
const cdp = await context.newCDPSession(page);
const v = (method, ...args) => page.evaluate(([m, a]) => window.__v[m](...a), [method, args]);

// ---------- Cursor y acciones con ritmo humano ----------
const mouse = { x: 1200, y: 500 };
async function move(x, y, ms) {
  const dx = x - mouse.x, dy = y - mouse.y, dist = Math.hypot(dx, dy);
  if (dist < 2) return;
  ms ??= Math.min(1100, 320 + dist * 0.55);
  const bow = Math.min(60, dist * 0.08), nx = -dy / dist, ny = dx / dist;
  const start = performance.now(), from = { ...mouse };
  for (;;) {
    const t = Math.min(1, (performance.now() - start) / ms), e = ease(t), arc = Math.sin(Math.PI * e) * bow;
    mouse.x = from.x + dx * e + nx * arc;
    mouse.y = from.y + dy * e + ny * arc;
    await page.mouse.move(mouse.x, mouse.y);
    if (t >= 1) break;
    await sleep(8);
  }
}
const box = async target => (typeof target === 'string' ? page.locator(target).first() : target).boundingBox();
async function moveTo(target, { ax = 0.5, ay = 0.5, ms } = {}) {
  const b = await box(target);
  await move(b.x + b.width * ax, b.y + b.height * ay, ms);
}
async function click(target, opts) {
  await moveTo(target, opts);
  await sleep(130);
  await page.mouse.down();
  await sleep(70);
  await page.mouse.up();
}
/** Clic solo visual (onda), para controles cuyo efecto real no conviene disparar. */
const tap = () => page.evaluate(([x, y]) => window.dispatchEvent(new MouseEvent('mousedown', { clientX: x, clientY: y })), [mouse.x, mouse.y]);
const type = (text, delay = 32) => page.keyboard.type(text, { delay });
async function view(target, frac = 0.2, ms = 900) {
  const b = await box(target);
  const y = await page.evaluate(() => window.scrollY);
  await v('scrollTo', y + b.y - HEIGHT * frac, ms);
}
async function spot(target, pad = 12) {
  const b = await box(target);
  await v('spot', b.x - pad, b.y - pad, b.width + pad * 2, b.height + pad * 2);
}
let zoomScale = 1;
const SAFE_BOTTOM = 905; // por debajo van los subtítulos
/** Acerca la página a `target`. Con `fit`, lo centra sin que su borde inferior invada la zona de subtítulos. */
async function zoomTo(target, scale, ms = 900, { ay = 0.5, fit = false } = {}) {
  const b = await box(target), ratio = scale / zoomScale;
  let fy = b.y + b.height * ay;
  if (fit) {
    const centre = Math.min(HEIGHT / 2, SAFE_BOTTOM - (b.height * ratio) / 2);
    fy = b.y + b.height / 2 + (HEIGHT / 2 - centre) / ratio;
  }
  await v('zoom', b.x + b.width / 2, fy, scale, ms);
  zoomScale = scale;
}
const zoomReset = async ms => { await v('zoomReset', ms); zoomScale = 1; };
const chip = (scene, seconds = 3.4) => v('chip', chapterLabel(scene.chapter), scene.title, seconds * 1000);
async function settle() {
  await page.evaluate(() => document.fonts.ready);
  await sleep(350);
}
async function open(hash, ready) {
  await page.goto(BASE + '/' + hash);
  if (ready) await page.locator(ready).first().waitFor();
  await v('clear');
  await zoomReset(1);
  await v('scrollTo', 0, 1);
  await settle();
}
async function login() {
  await open('#login', '#login-email');
  await page.locator('#login-email').fill(DEMO_USER);
  await page.locator('#login-password').fill(DEMO_PASSWORD);
  await page.locator('#access form button').first().click();
  await page.locator('#client-services').waitFor();
}

// ---------- Escenas ----------
// Cada escena tiene `prepare` (fuera de cámara) y `run` (grabado). Los tiempos de `run`
// están en segundos nominales; S.at() los escala a la duración real de la narración.
const BUBBLES = ['¿Tienen espacio el sábado?', '¿Cuánto cuesta el corte y barba?', '¿Puedo cambiar mi cita?', '¿Hasta qué hora atienden?'];
const ICONS = {
  chat: '<svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/></svg>',
  calendar: '<svg viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4M8.5 15l2.5 2.5 4.5-4.5"/></svg>',
  shield: '<svg viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.500-8-9V6z"/><path d="M8.500 12l2.500 2.500 4.500-4.500"/></svg>',
};
const BENEFITS = [
  ['chat', 'Menos mensajes repetidos', 'El asistente responde las consultas frecuentes y toma las reservas.'],
  ['calendar', 'Agenda sin citas cruzadas', 'Cada turno se valida contra la disponibilidad antes de confirmarse.'],
  ['shield', 'Tus datos, separados', 'La información de cada negocio se mantiene aparte de las demás.'],
];

const scenes = {
  's1-problema': {
    nominal: 12,
    async prepare() { await open('#home', '.hero'); await v('stage', 'bg'); await sleep(450); },
    async run(S) {
      await v('add', 'eyebrow', 'v-eyebrow', 'El día a día de tu negocio', { left: '150px', top: '300px' });
      await v('add', 'h1', 'v-h1', 'Atender bien<br>toma tiempo', { left: '150px', top: '352px' }, 150);
      for (const [i, text] of BUBBLES.entries()) {
        await S.at(1.1 + i * 1.35);
        await v('add', 'b' + i, 'v-bubble', `${text}<small>Sin responder</small>`, { left: 1010 + (i % 2) * 150 + 'px', top: 150 + i * 190 + 'px' });
      }
      await S.at(6.8);
      await v('add', 'row', 'v-row', ['Teléfono', 'Chat', 'Agenda'].map((t, i) => `<span class="v-pill" style="--d:${(i * 0.55 * S.k).toFixed(2)}s">${t}</span>`).join(''),
        { top: '640px', left: '150px', right: 'auto' });
      await S.at(9.2);
      await v('add', 'sub', 'v-sub', 'Coordinar citas se vuelve un trabajo aparte.', { left: '150px', top: '740px' });
      await S.at(11.5);
      await v('remove');
    },
  },
  's2-que-es': {
    nominal: 9.5,
    async prepare() { await open('#home', '.hero'); await move(1180, 650, 1); await v('cursor', true); },
    async run(S, scene) {
      await S.at(0.25);
      await chip(scene, 2.1 * S.k);
      await move(700, 480, 1100);
      await S.at(2.3);
      await zoomTo('.hero h1', 1.16, 900, { ay: 1.65 });
      await S.at(3.3);
      const pills = ['Servicios', 'Horarios', 'Equipo', 'Reservas'].map((t, i) => `<span class="v-pill" style="--d:${(i * 0.55 * S.k).toFixed(2)}s">${t}</span>`).join('');
      await v('add', 'row', 'v-row', pills + `<span class="v-pill accent" style="--d:${(3.1 * S.k).toFixed(2)}s">+ Asistente para tus clientes</span>`, { top: '742px' });
      await S.at(8.3);
      await v('remove');
      await zoomReset(800);
    },
  },
  's3-chat': {
    nominal: 16.5,
    async prepare() { await open('#reservar/alfa', 'details.booking-chat'); await move(1480, 430, 1); await v('cursor', true); },
    async run(S, scene) {
      const chat = page.locator('details.booking-chat');
      const input = chat.locator('form input');
      const log = chat.locator('[role=log]');
      await S.at(0.2);
      await chip(scene);
      await S.at(0.9);
      await click(chat.locator('summary'), { ax: 0.12 });
      await zoomTo(chat, 1.25, 800, { fit: true });
      await click(input, { ax: 0.3 });
      await type(CHAT_MESSAGE);
      await sleep(250);
      await click(chat.getByRole('button', { name: 'Enviar' }));
      await log.getByText('¿A qué nombre').waitFor();
      await zoomTo(chat, 1.25, 500, { fit: true });
      await S.at(5.9);
      await click(input, { ax: 0.3 });
      await type('Carlos Méndez');
      await page.keyboard.press('Enter');
      await log.getByText('teléfono o correo').waitFor();
      await zoomTo(chat, 1.25, 500, { fit: true });
      await S.at(7.9);
      await click(input, { ax: 0.3 });
      await type('carlos.mendez@example.com', 26);
      await page.keyboard.press('Enter');
      await log.getByText('¿Confirmas esta cita?').waitFor();
      await zoomTo(chat, 1.25, 600, { fit: true });
      await S.at(10.4);
      const confirm = chat.getByRole('button', { name: 'Confirmar cita' });
      await S.at(11.6);
      await spot(confirm, 10);
      await moveTo(confirm, { ms: 900 });
      await S.at(13.3);
      await page.mouse.down(); await sleep(70); await page.mouse.up();
      await log.getByText('Cita confirmada.').waitFor();
      await sleep(250);
      await zoomTo(chat, 1.25, 400, { fit: true });
      await spot(log.getByText('Cita confirmada.'), 12);
      await S.at(15.5);
      await v('spotHide');
      await zoomReset(750);
    },
  },
  's4-fuentes': {
    nominal: 10.5,
    async prepare() {
      await page.goto(BASE + '/#home');
      await open('#reservar/alfa', 'details.booking-chat');
      await page.locator('details.booking-chat summary').click();
      await zoomTo('details.booking-chat', 1.3, 1, { fit: true });
      await move(1520, 520, 1);
      await v('cursor', true);
      await sleep(300);
    },
    async run(S, scene) {
      const chat = page.locator('details.booking-chat');
      await S.at(0.2);
      await chip(scene);
      await moveTo(chat.locator('select').first(), { ax: 0.5 });
      await tap();
      await sleep(160);
      await chat.locator('select').first().selectOption('knowledge');
      await S.at(1.9);
      await click(chat.locator('form input'), { ax: 0.3 });
      await type('¿Puedo cancelar mi cita?');
      await page.keyboard.press('Enter');
      const quote = chat.locator('blockquote').first();
      await quote.waitFor();
      await zoomTo(chat, 1.3, 600, { fit: true });
      await S.at(5.2);
      await spot(quote, 14);
      await move(mouse.x + 220, mouse.y + 170, 900);
      await S.at(9.5);
      await v('spotHide');
      await zoomReset(750);
    },
  },
  // WhatsApp todavía no está conectado: la escena es una ilustración propia y lo dice en pantalla.
  's4b-whatsapp': {
    nominal: 5.7,
    async prepare() { await open('#home', '.hero'); await v('cursor', false); await v('stage', 'bg'); await sleep(450); },
    async run(S) {
      const d = s => `style="--d:${(s * S.k).toFixed(2)}s"`;
      await v('add', 'tag', '', '<span class="v-pill accent">Próximamente</span>', { left: '150px', top: '330px' });
      await v('add', 'h2', 'v-h2', 'El mismo asistente,<br>también por WhatsApp', { left: '150px', top: '420px' }, 150);
      await v('add', 'note', 'v-note', 'Conversación ilustrativa: esta función aún no está disponible.', { left: '150px', top: '590px' }, 350);
      await v('add', 'phone', '', `<div class="v-phone"><div class="v-phone-screen">
        <div class="v-phone-top"><i>A</i><div><strong>Barbería Alfa</strong><small>Asistente</small></div></div>
        <div class="v-phone-body">
          <p class="me" ${d(0.9)}>Hola, ¿tienen espacio el sábado?</p>
          <p class="bot" ${d(2.1)}>¡Hola! Ana tiene libre el sábado a las 10:00. ¿Te la reservo?</p>
          <p class="me" ${d(3.4)}>Sí, por favor</p>
          <p class="bot" ${d(4.3)}>Listo, tu cita quedó confirmada.</p>
        </div></div></div>`, { left: '1230px', top: '150px' }, 250);
      await S.at(5.25);
      await v('remove');
    },
  },
  's5-panel': {
    nominal: 12.5,
    async prepare() {
      await login();
      await v('clear');
      await view('#client-title', 0.16, 1);
      await move(1700, 540, 1);
      await v('cursor', true);
      await settle();
    },
    async run(S, scene) {
      await S.at(0.2);
      await chip(scene);
      await view('#client-services', 0.13, 800);
      await S.at(1.3);
      await spot('.client-services', 14);
      await moveTo('.client-services', { ax: 0.55, ay: 0.3 });
      await S.at(3.7);
      await v('spotHide');
      await view('#client-hours', 0.13, 850);
      await spot('.client-hours-grid', 14);
      await moveTo('.client-hours-grid', { ax: 0.4, ay: 0.3 });
      await S.at(6.3);
      await v('spotHide');
      const team = page.getByRole('heading', { name: 'Mi equipo' }).locator('xpath=..');
      await view(team, 0.25, 850);
      await spot(team.locator('.business-list').first(), 14);
      await moveTo(team.locator('.business-list').first(), { ax: 0.3, ay: 0.5 });
      await S.at(8.7);
      await v('spotHide');
      const row = page.locator('#client-bookings tr', { hasText: 'Carlos Méndez' });
      await view(row, 0.62, 850);
      await S.at(9.9);
      await spot(row, 6);
      await moveTo(row, { ax: 0.42, ay: 0.7 });
      await S.at(12.1);
      await v('spotHide');
    },
  },
  's6-beneficios': {
    nominal: 11,
    async prepare() {
      if (!(await page.locator('#client-bookings').count())) await login();
      await v('clear');
      await view(page.locator('#client-bookings tr', { hasText: 'Carlos Méndez' }), 0.62, 1);
      await v('cursor', false);
      await settle();
    },
    async run(S, scene) {
      await v('stage', 'dim');
      await S.at(0.3);
      await chip(scene);
      for (const [i, [icon, title, text]] of BENEFITS.entries()) {
        await S.at(0.9 + i * 2.9);
        await v('add', 'k' + i, 'v-benefit', `<i>${ICONS[icon]}</i><h3>${title}</h3><p>${text}</p>`, { left: 140 + i * 560 + 'px', top: '360px' });
      }
      await S.at(10.4);
      await v('remove');
    },
  },
  's7-cta': {
    nominal: 10,
    async prepare() {
      await context.clearCookies();
      await page.goto(BASE + '/#login');
      await open('#home', '.hero');
      await move(1300, 700, 1);
      await v('cursor', true);
    },
    async run(S, scene) {
      await S.at(0.2);
      await chip(scene);
      await moveTo('.hero .btn-outline');
      await sleep(200);
      await tap();
      await view('#contact', 0.1, 1100);
      await S.at(3.0);
      await zoomTo('.contact-form', 1.12, 800, { ay: 0.3 });
      await click('#contact-name', { ax: 0.3 });
      await type('Laura Vega', 45);
      await S.at(6.1);
      await v('chipHide');
      await v('cursor', false);
      await v('stage', 'bg');
      await v('add', 'logo', 'v-center', '<div class="v-logo"><em>O</em>ORQENTIVA</div>', { top: '300px' }, 250);
      await v('add', 'h2', 'v-center v-h2', 'Solicita una asesoría', { top: '470px' }, 550);
      await v('add', 'sub', 'v-center v-sub', 'Cuéntanos qué necesitas y preparamos una propuesta.', { top: '566px' }, 800);
      await v('add', 'cta', 'v-center', '<div class="v-cta">Formulario de contacto</div>', { top: '680px' }, 1100);
      await sleep(600);
      await zoomReset(1);
    },
  },
};

// ---------- Captura ----------
async function record(scene, seconds) {
  const def = scenes[scene.id];
  const dir = path.join(WORK, 'frames', scene.id);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  await def.prepare();
  const frames = [], writes = [];
  const onFrame = ({ data, sessionId }) => {
    const t = performance.now();
    cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {});
    const file = path.join(dir, String(frames.length + 1).padStart(6, '0') + '.jpg');
    frames.push({ file, t });
    writes.push(fs.promises.writeFile(file, Buffer.from(data, 'base64')));
  };
  cdp.on('Page.screencastFrame', onFrame);
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 96, maxWidth: WIDTH, maxHeight: HEIGHT, everyNthFrame: 1 });
  while (!frames.length) await sleep(20);
  const t0 = performance.now(), k = seconds / def.nominal;
  const S = { k, at: async s => { const wait = t0 + s * k * 1000 - performance.now(); if (wait > 0) await sleep(wait); } };
  await def.run(S, scene);
  const used = (performance.now() - t0) / 1000;
  await S.at(def.nominal);
  const t1 = performance.now();
  await cdp.send('Page.stopScreencast');
  cdp.off('Page.screencastFrame', onFrame);
  await Promise.all(writes);

  // Lista para ffmpeg: cada fotograma dura hasta que llega el siguiente.
  const first = Math.max(0, frames.findLastIndex(f => f.t <= t0));
  const kept = frames.slice(first).filter(f => f.t < t1);
  const lines = kept.map((f, i) => {
    const start = Math.max(f.t, t0), end = i + 1 < kept.length ? kept[i + 1].t : t1;
    return `file '${f.file.replaceAll('\\', '/')}'\nduration ${Math.max(0.001, (end - start) / 1000).toFixed(4)}`;
  });
  lines.push(`file '${kept[kept.length - 1].file.replaceAll('\\', '/')}'`);
  const list = path.join(dir, 'frames.txt');
  fs.writeFileSync(list, lines.join('\n') + '\n');
  const total = (t1 - t0) / 1000, out = path.join(WORK, 'scenes', scene.id + '.mp4');
  const fade = `fade=t=in:st=0:d=0.3:color=0x10253d,fade=t=out:st=${(total - 0.25).toFixed(2)}:d=0.25:color=0x10253d`;
  ffmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-vf', `fps=${FPS},scale=${WIDTH}:${HEIGHT}:flags=lanczos,${fade},format=yuv420p`,
    '-t', total.toFixed(3), '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-an', out]);
  const late = used > seconds + 0.15 ? `  ⚠ las acciones tardaron ${used.toFixed(1)} s` : '';
  console.log(`${scene.id}: ${total.toFixed(2)} s, ${kept.length} fotogramas (${(kept.length / total).toFixed(0)} fps de captura)${late}`);
  return { id: scene.id, seconds: Math.round(total * 1000) / 1000 };
}

const timeline = [];
for (const [i, scene] of script.scenes.entries()) {
  if (only.length && !only.includes(scene.id)) continue;
  timeline.push(await record(scene, durations[i].seconds));
}
if (!only.length) fs.writeFileSync(path.join(WORK, 'recorded.json'), JSON.stringify(timeline, null, 2));
await browser.close();
