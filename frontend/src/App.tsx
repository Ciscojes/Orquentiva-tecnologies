import { useEffect, useState } from "react";
import "./App.css";

type Language = "es" | "en";

const translations = {
  es: {
    navigation: ["Inicio", "Servicios", "Soluciones", "Nosotros", "Contacto"],
    tagline: "Tecnología para empresas que evolucionan",
    title: "Inteligencia que impulsa negocios.",
    description:
      "Transformamos empresas mediante agentes de IA, automatización inteligente y plataformas digitales diseñadas para crecer.",
    explore: "Explorar servicios",
    contact: "Solicitar asesoría",
    servicesTitle: "Nuestras soluciones",
    servicesDescription:
      "Integramos inteligencia artificial, ingeniería de software y estrategia comercial.",
    services: [
      {
        name: "Agentes de IA",
        description:
          "Asistentes inteligentes que atienden consultas y ejecutan tareas empresariales.",
      },
      {
        name: "Automatización",
        description:
          "Conectamos aplicaciones y automatizamos operaciones repetitivas.",
      },
      {
        name: "Growth Partner",
        description:
          "Utilizamos tecnología y análisis de datos para impulsar el crecimiento comercial.",
      },
      {
        name: "Plataformas SaaS",
        description:
          "Desarrollamos soluciones empresariales escalables y personalizadas.",
      },
    ],
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
    tagline: "Technology for evolving businesses",
    title: "Intelligence that drives business growth.",
    description:
      "We transform businesses through AI agents, intelligent automation, and digital platforms built for growth.",
    explore: "Explore services",
    contact: "Request a consultation",
    servicesTitle: "Our solutions",
    servicesDescription:
      "We combine artificial intelligence, software engineering, and business strategy.",
    services: [
      {
        name: "AI Agents",
        description:
          "Intelligent assistants that handle inquiries and perform business tasks.",
      },
      {
        name: "Automation",
        description:
          "We connect applications and automate repetitive operations.",
      },
      {
        name: "Growth Partner",
        description:
          "We use technology and data analysis to support business growth.",
      },
      {
        name: "SaaS Platforms",
        description: "We develop scalable and customized business software.",
      },
    ],
    aboutTitle: "Purpose-driven innovation",
    aboutText:
      "ORQENTIVA Technologies creates solutions that connect business needs with software engineering and artificial intelligence.",
    contactTitle: "Let's transform your business",
    contactText: "Let's discuss how technology can improve your operations.",
    footer: "All rights reserved.",
  },
};

const serviceIcons = ["✦", "⚡", "↗", "◈"];
const anchors = ["home", "services", "solutions", "about", "contact"];

function App() {
  const [language, setLanguage] = useState<Language>(() => {
    try {
      return localStorage.getItem("orqentiva-language") === "en" ? "en" : "es";
    } catch {
      return "es";
    }
  });

  const t = translations[language];

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = "ORQENTIVA Technologies";

    try {
      localStorage.setItem("orqentiva-language", language);
    } catch {
      // La página sigue funcionando sin almacenamiento.
    }
  }, [language]);

  return (
    <>
      <header className="header">
        <a href="#home" className="brand" aria-label="ORQENTIVA Home">
          <span className="brand-symbol">O</span>
          <span>ORQENTIVA</span>
        </a>

        <nav aria-label="Main navigation">
          {t.navigation.map((name, index) => (
            <a key={anchors[index]} href={`#${anchors[index]}`}>
              {name}
            </a>
          ))}
        </nav>

        <div className="language-switch" aria-label="Language">
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

        <section className="section" id="services">
          <div id="solutions" className="section-heading">
            <span className="eyebrow">ORQENTIVA SOLUTIONS</span>
            <h2>{t.servicesTitle}</h2>
            <p>{t.servicesDescription}</p>
          </div>

          <div className="services-grid">
            {t.services.map((service, index) => (
              <article className="service-card" key={index}>
                <div className="service-icon">{serviceIcons[index]}</div>
                <h3>{service.name}</h3>
                <p>{service.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="about-section" id="about">
          <span className="eyebrow">ABOUT ORQENTIVA</span>
          <h2>{t.aboutTitle}</h2>
          <p>{t.aboutText}</p>
        </section>

        <section className="contact-section" id="contact">
          <h2>{t.contactTitle}</h2>
          <p>{t.contactText}</p>
          <a href="mailto:contacto@ejemplo.com" className="btn btn-primary">
            {t.contact}
          </a>
        </section>
      </main>

      <footer>
        <strong>ORQENTIVA Technologies</strong>
        <span>
          © {new Date().getFullYear()} — {t.footer}
        </span>
      </footer>
    </>
  );
}

export default App;
