import { useEffect, useState } from "react";
import "./App.css";
import ContactForm from "./components/ContactForm";
import AccessPanel from "./components/AccessPanel";
import ServiceCards from "./components/ServiceCards";
import type { Language } from "./services";

// Traducciones de toda la página
const translations = {
  es: {
    navigation: ["Inicio", "Servicios", "Soluciones", "Nosotros", "Contacto", "Acceso"],

    navLabel: "Navegación principal",
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
    navigation: ["Home", "Services", "Solutions", "About", "Contact", "Sign in"],

    navLabel: "Main navigation",
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
const anchors = ["home", "services", "solutions", "about", "contact", "access"];

function App() {
  const [year] = useState(() => new Date().getFullYear());
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
      <header className="header">
        <a href="#home" className="brand" aria-label={t.homeLabel}>
          <span className="brand-symbol">O</span>
          <span>ORQENTIVA</span>
        </a>

        <nav aria-label={t.navLabel}>
          {t.navigation.map((name, index) => (
            <a key={anchors[index]} href={`#${anchors[index]}`}>
              {name}
            </a>
          ))}
        </nav>

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
      </header>

      <main>
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
        <AccessPanel language={language} />
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
