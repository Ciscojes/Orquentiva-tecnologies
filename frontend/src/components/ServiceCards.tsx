import { services, type Language } from "../services";

const labels = {
  es: { example: "Un ejemplo en tu negocio", more: "Conocer el servicio", contact: "Solicitar asesoría", problem: "Qué problema aborda", includes: "Qué puede incluir", benefits: "Qué puede aportar", process: "Cómo trabajamos", audience: "Para quién es", scope: "Alcance de la propuesta", next: "Cuéntanos tu necesidad y elige este servicio en el formulario. Revisaremos el alcance para preparar una propuesta." },
  en: { example: "An example for your business", more: "Explore this service", contact: "Request a consultation", problem: "The problem it addresses", includes: "What it can include", benefits: "Potential benefits", process: "How we work", audience: "Who it is for", scope: "Proposal scope", next: "Tell us what you need and select this service in the form. We will review the scope to prepare a proposal." },
};
const icons = { agents: "✦", automation: "⚡", growth: "↗", saas: "◈" };

export default function ServiceCards({ language }: { language: Language }) {
  const t = labels[language];
  return (
    <div className="services-grid">
      {services[language].map(service => (
        <article className="service-card" key={service.id} aria-labelledby={`title-${service.id}`}>
          <div className="service-icon" aria-hidden="true">{icons[service.id]}</div>
          <h3 id={`title-${service.id}`}>{service.name}</h3>
          <p className="service-subtitle">{service.subtitle}</p>
          <p>{service.description}</p>
          <div className="service-example"><strong>{t.example}</strong><p>{service.example}</p></div>
          <details className="service-details">
            <summary>{t.more}<span className="sr-only">: {service.name}</span></summary>
            <div className="service-detail-content">
              <h4>{t.problem}</h4><p>{service.problem}</p>
              <h4>{t.includes}</h4><ul>{service.includes.map(item => <li key={item}>{item}</li>)}</ul>
              <h4>{t.benefits}</h4><p>{service.benefits}</p>
              <h4>{t.process}</h4><ol>{service.steps.map(step => <li key={step}>{step}</li>)}</ol>
              <h4>{t.audience}</h4><p>{service.audience}</p>
              <h4>{t.scope}</h4><p>{service.scope}</p>
              <p className="service-next">{t.next}</p>
            </div>
          </details>
          <a href="#contact" className="btn btn-primary service-cta">{t.contact}<span className="sr-only">: {service.name}</span></a>
        </article>
      ))}
    </div>
  );
}
