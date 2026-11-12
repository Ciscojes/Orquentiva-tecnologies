import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";
import ContactForm from "./components/ContactForm";
import AccessPanel from "./components/AccessPanel";
import ServiceCards from "./components/ServiceCards";
import VideoPresentation from "./components/VideoPresentation";
import type { Language } from "./services";

// Traducciones de toda la página
const translations = {
  es: {
    navigation: ["Inicio", "Servicios", "Soluciones", "Nosotros", "Contacto"],

    navLabel: "Navegación principal",
    access: "Acceso clientes", panel: "Mi panel", menu: "Menú", back: "Volver al sitio",
    homeLabel: "Inicio de ORQENTIVA",

    tagline: "Tecnología para empresas que evolucionan",
    title: "Inteligencia que impulsa negocios.",

    description:
      "Diseñamos soluciones para atender mejor a tus clientes, simplificar tareas y organizar tu negocio. Empezamos por entender lo que necesitas.",

    explore: "Explorar servicios",
    contact: "Solicitar asesoría",

    solutionsLabel: "SOLUCIONES ORQENTIVA",
    servicesTitle: "Tecnología al servicio de tu negocio",

    servicesDescription:
      "Conoce qué puede aportar cada servicio. Evaluamos tu caso y acordamos el alcance, las integraciones y los costes antes de implementar.",


    aboutLabel: "SOBRE ORQENTIVA",
    aboutTitle: "Innovación con propósito",

    aboutText:
      "ORQENTIVA Technologies desarrolla soluciones que conectan las necesidades empresariales con la ingeniería y la inteligencia artificial.",

    contactTitle: "Transformemos tu negocio",

    contactText:
      "Conversemos sobre cómo la tecnología puede mejorar tus procesos.",

    footer: "Todos los derechos reservados.",
  },

  en: {
    navigation: ["Home", "Services", "Solutions", "About", "Contact"],

    navLabel: "Main navigation",
    access: "Client access", panel: "My dashboard", menu: "Menu", back: "Back to website",
    homeLabel: "ORQENTIVA Home",

    tagline: "Technology for evolving businesses",
    title: "Intelligence that drives business growth.",

    description:
      "We design solutions to serve your customers, simplify tasks and organize your business. We start by understanding what you need.",

    explore: "Explore services",
    contact: "Request a consultation",

    solutionsLabel: "ORQENTIVA SOLUTIONS",
    servicesTitle: "Technology that serves your business",

    servicesDescription:
      "Explore what each service can offer. We assess your needs and agree on scope, integrations and costs before implementation.",


    aboutLabel: "ABOUT ORQENTIVA",
    aboutTitle: "Purpose-driven innovation",

    aboutText:
      "ORQENTIVA Technologies creates solutions that connect business needs with software engineering and artificial intelligence.",

    contactTitle: "Let's transform your business",

    contactText: "Let's discuss how technology can improve your operations.",

    footer: "All rights reserved.",
  },
};

// Identificadores de las secciones
const anchors = ["home", "services", "solutions", "about", "contact"];
const privateAnchors = new Set(["#login", "#panel", "#access", "#client-services", "#client-hours", "#client-bookings"]);

import PublicBooking from "./components/PublicBooking";

function App() {
  const [year] = useState(() => new Date().getFullYear());
  const [hash, setHash] = useState(() => window.location.hash);
  const [hasSession, setHasSession] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  const privateView = privateAnchors.has(hash);
  const onSessionChange = useCallback((active: boolean) => {
    setHasSession(active);
    const current = window.location.hash;
    const target = active && ["#login", "#access"].includes(current) ? "#panel"
      : !active && privateAnchors.has(current) && current !== "#login" ? "#login" : null;
    if (target) {
      window.history.replaceState(null, "", target);
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    }
  }, []);

  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;
    const measure = () => document.documentElement.style.setProperty("--header-height", `${Math.ceil(header.getBoundingClientRect().height)}px`);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(header);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const navigate = () => { setHash(window.location.hash); setMenuOpen(false); };
    window.addEventListener("hashchange", navigate);
    return () => window.removeEventListener("hashchange", navigate);
  }, []);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      if (headerRef.current) document.documentElement.style.setProperty("--header-height", `${Math.ceil(headerRef.current.getBoundingClientRect().height)}px`);
      if (["#login", "#panel", "#access"].includes(hash)) window.scrollTo({top:0, behavior:"instant"});
      else document.getElementById(hash.slice(1))?.scrollIntoView();
    });
    return () => cancelAnimationFrame(frame);
  }, [hash]);

  useEffect(() => {
    if (privateView) return;
    const controller = new AbortController();
    let alive = true;
    const timeout = setTimeout(() => controller.abort(), 15000);
    fetch("/auth/me", {credentials:"same-origin", cache:"no-store", signal:controller.signal})
      .then(response => { if (alive) setHasSession(response.ok); })
      .catch(() => { if (alive) setHasSession(false); })
      .finally(() => clearTimeout(timeout));
    return () => { alive=false; clearTimeout(timeout); controller.abort(); };
  }, [privateView]);
  // Estado global del idioma de la página
  const [language, setLanguage] = useState<Language>(() => {
    try {
      const savedLanguage = localStorage.getItem("orqentiva-language");

      return savedLanguage === "en" ? "en" : "es";
    } catch {
      return "es";
    }
  });

  // Traducciones correspondientes al idioma activo
  const t = translations[language];

  // Actualizar idioma del documento y guardar preferencia
  useEffect(() => {
    document.documentElement.lang = language;

    document.title = "ORQENTIVA Technologies";

    try {
      localStorage.setItem("orqentiva-language", language);
    } catch {
      // El sitio sigue funcionando si localStorage falla
    }
  }, [language]);

  return (
    <>
      {/* CABECERA Y NAVEGACIÓN */}
      <header ref={headerRef} className="header" onKeyDown={event => {
        if (event.key === "Escape" && menuOpen) { setMenuOpen(false); menuButton.current?.focus(); }
      }}>
        <a href="#home" className="brand" aria-label={t.homeLabel}>
          <span className="brand-symbol">O</span>
          <span>ORQENTIVA</span>
        </a>

        <button ref={menuButton} type="button" className="mobile-menu-toggle" aria-expanded={menuOpen}
          aria-controls="primary-navigation" onClick={() => setMenuOpen(value => !value)}>{t.menu}</button>
        <nav id="primary-navigation" className={menuOpen ? "primary-navigation is-open" : "primary-navigation"} aria-label={t.navLabel}>
          {t.navigation.map((name, index) => (
            <a key={anchors[index]} href={`#${anchors[index]}`} onClick={() => setMenuOpen(false)}>
              {name}
            </a>
          ))}
        </nav>

        <div className="header-tools">
          <a className="header-access" href={hasSession ? "#panel" : "#login"} onClick={() => setMenuOpen(false)}>{hasSession ? t.panel : t.access}</a>
        {/* SELECTOR DE IDIOMAS */}
        <div
          className="language-switch"
          role="group"
          aria-label="Language / Idioma"
        >
          <button
            type="button"
            className={language === "es" ? "active" : ""}
            onClick={() => setLanguage("es")}
            aria-pressed={language === "es"}
          >
            ES
          </button>

          <button
            type="button"
            className={language === "en" ? "active" : ""}
            onClick={() => setLanguage("en")}
            aria-pressed={language === "en"}
          >
            EN
          </button>
        </div>
        </div>
      </header>

      <main className={privateView ? "private-main" : "public-main"}>
        {hash.startsWith("#reservar/") ? <PublicBooking key={hash} business={hash.slice("#reservar/".length)} language={language}/> : privateView ? <>
          <div className="private-breadcrumb"><a href="#home">← {t.back}</a></div>
          <AccessPanel language={language} locationHash={hash} onSessionChange={onSessionChange} />
        </> : <>
        {/* SECCIÓN PRINCIPAL */}
        <section className="hero" id="home">
          <div className="hero-content">
            <span className="eyebrow">{t.tagline}</span>

            <h1>{t.title}</h1>

            <p>{t.description}</p>

            <div className="actions">
              <a href="#services" className="btn btn-primary">
                {t.explore}
              </a>

              <a href="#contact" className="btn btn-outline">
                {t.contact}
              </a>
            </div>
          </div>

          {/* ELEMENTO VISUAL */}
          <div className="hero-art" aria-hidden="true">
            <div className="orb orb-one" />
            <div className="orb orb-two" />

            <div className="art-panel">
              <div className="panel-mark">O</div>

              <span>ORQENTIVA</span>

              <small>INTELLIGENT SYSTEMS</small>
            </div>
          </div>
        </section>

        {/* VIDEO DE PRESENTACIÓN */}
        <VideoPresentation language={language} />

        {/* SERVICIOS Y SOLUCIONES */}
        <section className="section" id="services">
          <div id="solutions" className="section-heading">
            <span className="eyebrow">{t.solutionsLabel}</span>

            <h2>{t.servicesTitle}</h2>

            <p>{t.servicesDescription}</p>
          </div>

          <ServiceCards language={language} />
        </section>

        {/* SOBRE NOSOTROS */}
        <section className="about-section" id="about">
          <span className="eyebrow">{t.aboutLabel}</span>

          <h2>{t.aboutTitle}</h2>

          <p>{t.aboutText}</p>
        </section>

        {/* CONTACTO */}
        <section className="contact-section" id="contact">
          <h2>{t.contactTitle}</h2>

          <p>{t.contactText}</p>

          <ContactForm language={language} />
        </section>
        </>}
      </main>

      {/* PIE DE PÁGINA */}
      <footer>
        <strong>ORQENTIVA Technologies</strong>

        <span>
          © {year} — {t.footer}
        </span>
      </footer>
    </>
  );
}

export default App;
