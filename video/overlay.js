// Capa visual de la grabación: cursor, resaltados, zoom, títulos y cartelas.
// Se inyecta en la página durante la grabación; no forma parte de la aplicación.
(() => {
  if (window.__v) return;
  const TEAL = '#36c6c0', NAVY = '#10253d';
  // La página se amplía con zoom CSS para que el texto se lea en pantallas pequeñas; la capa visual no se amplía.
  const Z = window.__V_PAGE_ZOOM || 1;
  const css = `
  html { scroll-behavior: auto !important; overflow-x: hidden; zoom: ${Z}; }
  ::-webkit-scrollbar { display: none; }
  #v-layer, #v-layer * { box-sizing: border-box; font-family: Inter, Arial, sans-serif; }
  #v-layer { position: fixed; left: 0; top: 0; width: 1920px; height: 1080px; zoom: ${1 / Z}; z-index: 2147483000; pointer-events: none; }
  #v-cursor { position: fixed; left: 0; top: 0; width: 34px; height: 34px; opacity: 0; transition: opacity .25s;
    filter: drop-shadow(0 3px 5px rgba(0,0,0,.35)); will-change: transform; z-index: 30; }
  #v-cursor.on { opacity: 1; }
  .v-ripple { position: fixed; width: 18px; height: 18px; margin: -9px 0 0 -9px; border-radius: 50%;
    border: 3px solid ${TEAL}; background: ${TEAL}55; animation: v-ripple .55s ease-out forwards; z-index: 29; }
  @keyframes v-ripple { to { transform: scale(4.2); opacity: 0; } }
  #v-spot { position: fixed; border-radius: 16px; border: 4px solid ${TEAL}; opacity: 0;
    box-shadow: 0 0 0 4000px rgba(9,26,44,.55), 0 0 34px ${TEAL}88;
    transition: opacity .35s ease, left .45s ease, top .45s ease, width .45s ease, height .45s ease; z-index: 10; }
  #v-spot.on { opacity: 1; }
  #v-chip { position: fixed; left: 36px; top: 150px; max-width: 370px; padding: 16px 22px 18px; border-radius: 20px;
    background: ${NAVY}; color: #fff; box-shadow: 0 10px 30px rgba(9,26,44,.35); border: 1px solid #ffffff22;
    border-left: 6px solid ${TEAL}; opacity: 0; transform: translateX(-24px);
    transition: opacity .4s ease, transform .4s ease; z-index: 20; }
  #v-chip.on { opacity: 1; transform: none; }
  #v-chip b { display: block; color: ${TEAL}; font-size: 17px; font-weight: 700; letter-spacing: .14em;
    text-transform: uppercase; margin-bottom: 6px; white-space: nowrap; }
  #v-chip span { display: block; font-size: 28px; line-height: 1.15; font-weight: 700; }
  #v-stage { position: fixed; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; z-index: 15; }
  #v-stage.bg { background: radial-gradient(1200px 700px at 70% 30%, #1b3d5c 0%, ${NAVY} 60%, #0b1c30 100%); }
  #v-stage.dim { background: rgba(9,26,44,.72); }
  #v-stage { transition: background .4s ease; }
  .v-el { position: absolute; opacity: 0; transform: translateY(26px) scale(.98);
    transition: opacity .5s ease, transform .5s cubic-bezier(.2,.8,.2,1); }
  .v-el.on { opacity: 1; transform: none; }
  .v-el.out { opacity: 0; transform: translateY(-18px); }
  .v-eyebrow { color: ${TEAL}; font-size: 22px; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }
  .v-h1 { color: #fff; font-size: 92px; line-height: 1.05; font-weight: 800; letter-spacing: -.02em; }
  .v-h2 { color: #fff; font-size: 60px; line-height: 1.1; font-weight: 800; letter-spacing: -.01em; }
  .v-sub { color: #c9d6e2; font-size: 30px; line-height: 1.4; }
  .v-bubble { background: #fff; color: ${NAVY}; border-radius: 22px 22px 22px 6px; padding: 20px 26px;
    font-size: 28px; font-weight: 500; box-shadow: 0 16px 40px rgba(0,0,0,.28); white-space: nowrap; }
  .v-bubble small { display: block; margin-top: 8px; font-size: 18px; color: #c2410c; font-weight: 700;
    letter-spacing: .04em; text-transform: uppercase; }
  .v-pill { background: ${NAVY}; border: 1px solid #ffffff40; color: #fff; border-radius: 999px;
    padding: 14px 28px; font-size: 28px; font-weight: 600; white-space: nowrap; box-shadow: 0 10px 26px rgba(9,26,44,.35); }
  .v-row { left: 0; right: 0; display: flex; justify-content: center; gap: 18px; }
  .v-row > * { opacity: 0; animation: v-in .5s cubic-bezier(.2,.8,.2,1) forwards; animation-delay: var(--d, 0s); }
  @keyframes v-in { from { opacity: 0; transform: translateY(22px); } to { opacity: 1; transform: none; } }
  .v-center { left: 0; right: 0; display: flex; justify-content: center; text-align: center; }
  .v-pill.accent { background: ${TEAL}; border-color: ${TEAL}; color: ${NAVY}; }
  .v-benefit { width: 520px; background: #fff; border-radius: 24px; padding: 34px 34px 36px;
    box-shadow: 0 24px 60px rgba(0,0,0,.35); color: ${NAVY}; }
  .v-benefit i { display: grid; place-items: center; width: 64px; height: 64px; border-radius: 18px;
    background: ${TEAL}; color: ${NAVY}; margin-bottom: 22px; }
  .v-benefit i svg { width: 36px; height: 36px; fill: none; stroke: ${NAVY}; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
  .v-benefit h3 { margin: 0 0 10px; font-size: 34px; line-height: 1.15; font-weight: 800; }
  .v-benefit p { margin: 0; font-size: 23px; line-height: 1.4; color: #47607a; }
  .v-logo { display: flex; align-items: center; gap: 22px; color: #fff; font-size: 54px; font-weight: 800; letter-spacing: .08em; }
  .v-logo em { display: grid; place-items: center; width: 92px; height: 92px; border-radius: 24px;
    border: 4px solid ${TEAL}; color: ${TEAL}; font-style: normal; font-size: 54px; }
  .v-phone { width: 400px; height: 740px; border-radius: 52px; background: #0b1c30; padding: 14px;
    box-shadow: 0 30px 70px rgba(0,0,0,.45), 0 0 0 2px #ffffff22; }
  .v-phone-screen { height: 100%; border-radius: 40px; background: #eef3f8; overflow: hidden; display: flex; flex-direction: column; }
  .v-phone-top { display: flex; align-items: center; gap: 14px; padding: 26px 22px 16px; background: ${NAVY}; color: #fff; }
  .v-phone-top i { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 50%; background: ${TEAL};
    color: ${NAVY}; font-style: normal; font-weight: 800; font-size: 22px; }
  .v-phone-top strong { display: block; font-size: 21px; }
  .v-phone-top small { display: block; font-size: 15px; color: #b9c9d8; }
  .v-phone-body { flex: 1; display: flex; flex-direction: column; gap: 14px; padding: 22px 18px; }
  .v-phone-body p { margin: 0; max-width: 82%; padding: 13px 16px; font-size: 19px; line-height: 1.32; border-radius: 18px;
    opacity: 0; animation: v-in .45s cubic-bezier(.2,.8,.2,1) forwards; animation-delay: var(--d, 0s); }
  .v-phone-body .me { align-self: flex-end; background: ${NAVY}; color: #fff; border-bottom-right-radius: 5px; }
  .v-phone-body .bot { align-self: flex-start; background: #fff; color: ${NAVY}; border-bottom-left-radius: 5px;
    box-shadow: 0 2px 8px rgba(16,37,61,.12); }
  .v-note { color: #9fb3c6; font-size: 22px; }
  .v-cta { background: ${TEAL}; color: ${NAVY}; border-radius: 18px; padding: 22px 44px; font-size: 36px; font-weight: 800; }
  `;
  const ARROW = `<svg viewBox="0 0 24 24" width="34" height="34"><path d="M4 2.5v17.2l4.7-4.3 3 6.6 2.9-1.3-3-6.5h6.4z" fill="#fff" stroke="${NAVY}" stroke-width="1.4" stroke-linejoin="round"/></svg>`;
  let layer, cursor, spot, chip, stage, cur = { tx: 0, ty: 0, s: 1 };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  function boot() {
    if (layer) return;
    const style = document.createElement('style');
    style.textContent = css;
    document.documentElement.appendChild(style);
    layer = document.createElement('div');
    layer.id = 'v-layer';
    layer.innerHTML = `<div id="v-spot"></div><div id="v-stage"></div><div id="v-chip"><b></b><span></span></div><div id="v-cursor">${ARROW}</div>`;
    document.documentElement.appendChild(layer);
    [spot, stage, chip, cursor] = ['v-spot', 'v-stage', 'v-chip', 'v-cursor'].map(id => document.getElementById(id));
    window.addEventListener('mousemove', e => { cursor.style.transform = `translate3d(${e.clientX - 5}px, ${e.clientY - 3}px, 0)`; }, true);
    window.addEventListener('mousedown', e => {
      const r = document.createElement('div');
      r.className = 'v-ripple';
      r.style.left = e.clientX + 'px';
      r.style.top = e.clientY + 'px';
      layer.appendChild(r);
      setTimeout(() => r.remove(), 600);
    }, true);
  }
  if (document.body) boot(); else document.addEventListener('DOMContentLoaded', boot);
  const ease = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  window.__v = {
    cursor(on) { boot(); cursor.classList.toggle('on', on); },
    // Título breve de la escena: aparece unos segundos y se retira para no tapar la interfaz.
    chip(label, title, ms = 3400) {
      boot();
      chip.querySelector('b').textContent = label;
      chip.querySelector('span').textContent = title;
      chip.classList.add('on');
      clearTimeout(chip._t);
      chip._t = setTimeout(() => chip.classList.remove('on'), ms);
    },
    chipHide() { chip?.classList.remove('on'); },
    spot(x, y, w, h) {
      boot();
      const fresh = !spot.classList.contains('on');
      if (fresh) spot.style.transition = 'opacity .35s ease';
      Object.assign(spot.style, { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px' });
      if (fresh) { void spot.offsetWidth; }
      spot.classList.add('on');
      if (fresh) setTimeout(() => { spot.style.transition = ''; }, 400);
    },
    spotHide() { spot?.classList.remove('on'); },
    // Acerca la página dejando el punto (fx, fy) del viewport cerca del centro.
    zoom(fx, fy, s, ms = 900) {
      const b = document.body, W = innerWidth, H = innerHeight;
      // (fx, fy) llega en coordenadas de pantalla; se convierte a coordenadas de la página sin zoom.
      // El desplazamiento del body se expresa en px de la página ampliada (1 px = Z px de pantalla).
      const px = ((fx + scrollX) / Z - cur.tx) / cur.s, py = ((fy + scrollY) / Z - cur.ty) / cur.s;
      let tx = (W / 2 + scrollX) / Z - s * px, ty = (H / 2 + scrollY) / Z - s * py;
      tx = Math.min(0, Math.max((W / Z) * (1 - s), tx));
      ty = Math.min(scrollY / Z, ty);
      b.style.transformOrigin = '0 0';
      b.style.transition = `transform ${ms}ms cubic-bezier(.45,0,.2,1)`;
      b.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`;
      cur = { tx, ty, s };
      return sleep(ms + 60);
    },
    zoomReset(ms = 800) {
      const b = document.body;
      b.style.transition = `transform ${ms}ms cubic-bezier(.45,0,.2,1)`;
      b.style.transform = 'translate(0px, 0px) scale(1)';
      cur = { tx: 0, ty: 0, s: 1 };
      return sleep(ms + 60).then(() => { b.style.transform = ''; b.style.transition = ''; });
    },
    scrollTo(y, ms = 900) {
      const from = scrollY, max = document.documentElement.scrollHeight - innerHeight;
      const to = Math.max(0, Math.min(max, y)), start = performance.now();
      if (Math.abs(to - from) < 2) return Promise.resolve();
      return new Promise(done => {
        const step = now => {
          const t = Math.min(1, (now - start) / ms);
          window.scrollTo(0, from + (to - from) * ease(t));
          if (t < 1) requestAnimationFrame(step); else done();
        };
        requestAnimationFrame(step);
      });
    },
    stage(mode) { boot(); stage.className = mode || ''; },
    // Añade un elemento a la cartela. style: posición CSS; devuelve su id.
    add(id, cls, html, style, delay = 0) {
      boot();
      const el = document.createElement('div');
      el.className = 'v-el ' + cls;
      el.dataset.id = id;
      el.innerHTML = html;
      Object.assign(el.style, style);
      stage.appendChild(el);
      setTimeout(() => el.classList.add('on'), 30 + delay);
    },
    remove(id) {
      stage.querySelectorAll(id ? `[data-id="${id}"]` : '.v-el').forEach(el => { el.classList.add('out'); setTimeout(() => el.remove(), 520); });
    },
    clear() { if (stage) { stage.innerHTML = ''; stage.className = ''; } spot?.classList.remove('on'); chip?.classList.remove('on'); },
  };
})();
