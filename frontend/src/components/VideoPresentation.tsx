import { useCallback, useEffect, useRef, useState } from "react";
import presentation from "../assets/presentacion.json";
import type { Language } from "../services";

// Los archivos los genera "npm run video" (carpeta video/) y se sirven desde frontend/public.
const VIDEO = "/presentacion.mp4";
const POSTER = "/presentacion-poster.jpg";
const SUBTITLES = { es: "/presentacion.es.vtt", en: "/presentacion.en.vtt" };

const copy = {
  es: {
    eyebrow: "MIRA CÓMO FUNCIONA",
    title: "ORQENTIVA en menos de 90 segundos",
    text: "Qué es, cómo se ve por dentro y qué aporta a tu negocio. Elige un capítulo para ir directo a lo que te interesa.",
    play: "Reproducir el video de presentación",
    chapters: "Capítulos del video",
    note: "Con subtítulos. Los datos que aparecen son de demostración.",
  },
  en: {
    eyebrow: "SEE HOW IT WORKS",
    title: "ORQENTIVA in under 90 seconds",
    text: "What it is, what it looks like inside and what it brings to your business. Pick a chapter to jump straight to it.",
    play: "Play the presentation video",
    chapters: "Video chapters",
    note: "Video in Spanish with English subtitles. All data shown is demo data.",
  },
};

const clock = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;

export default function VideoPresentation({ language }: Readonly<{ language: Language }>) {
  const t = copy[language];
  const { chapters, duration } = presentation;
  // El video no se descarga hasta que el visitante lo pide: antes solo hay una imagen ligera.
  const [started, setStarted] = useState(false);
  const [active, setActive] = useState(chapters[0].id);
  const video = useRef<HTMLVideoElement>(null);
  const startAt = useRef(0);

  // Muestra solo los subtítulos del idioma elegido en la página. Se repite al cargar y al
  // reproducir porque el navegador puede activar por su cuenta la pista de su propio idioma.
  const syncSubtitles = useCallback(() => {
    for (const track of Array.from(video.current?.textTracks ?? [])) track.mode = track.language === language ? "showing" : "disabled";
  }, [language]);
  useEffect(syncSubtitles, [syncSubtitles, started]);

  function open(start: number) {
    const element = video.current;
    if (!element) {
      startAt.current = start;
      setStarted(true);
      return;
    }
    element.currentTime = start;
    void element.play();
  }

  function onReady() {
    const element = video.current;
    syncSubtitles();
    if (element && startAt.current > 0) {
      element.currentTime = startAt.current;
      startAt.current = 0;
    }
  }

  function onTime() {
    const time = video.current?.currentTime ?? 0;
    const current = chapters.findLast(chapter => time >= chapter.start - 0.05) ?? chapters[0];
    setActive(current.id);
  }

  return (
    <section className="video-section" id="video" aria-labelledby="video-title">
      <div className="section-heading">
        <span className="eyebrow">{t.eyebrow}</span>
        <h2 id="video-title">{t.title}</h2>
        <p>{t.text}</p>
      </div>

      <div className="video-player">
        <div className="video-frame">
          {started ? (
            <video ref={video} controls autoPlay playsInline preload="metadata" poster={POSTER}
              onLoadedMetadata={onReady} onPlaying={syncSubtitles} onTimeUpdate={onTime} aria-label={t.title}>
              <source src={VIDEO} type="video/mp4" />
              <track kind="captions" src={SUBTITLES.es} srcLang="es" label="Español" default={language === "es"} />
              <track kind="captions" src={SUBTITLES.en} srcLang="en" label="English" default={language === "en"} />
            </video>
          ) : (
            <button type="button" className="video-poster" onClick={() => open(0)} aria-label={t.play}>
              <img src={POSTER} alt="" width={1280} height={720} loading="lazy" decoding="async" />
              <span className="video-play" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="34" height="34"><path d="M8 5.5v13l11-6.5z" fill="currentColor" /></svg>
              </span>
              <span className="video-length" aria-hidden="true">{clock(duration)}</span>
            </button>
          )}
        </div>

        <nav className="video-chapters" aria-label={t.chapters}>
          {chapters.map((chapter, index) => (
            <button type="button" key={chapter.id} onClick={() => open(chapter.start)}
              className={started && active === chapter.id ? "video-chapter is-active" : "video-chapter"}
              aria-current={started && active === chapter.id ? "true" : undefined}>
              <span className="video-chapter-number" aria-hidden="true">{index + 1}</span>
              <span className="video-chapter-name">{chapter[language]}</span>
              <span className="video-chapter-time">{clock(chapter.start)}</span>
            </button>
          ))}
        </nav>
        <p className="video-note">{t.note}</p>
      </div>
    </section>
  );
}
