import { useState, type FormEvent } from "react";

type Props = { language: "es" | "en" };
const translations = {
  es: {
    title: "Hablemos de tu proyecto", name: "Nombre completo", email: "Correo electrónico",
    company: "Empresa (opcional)", service: "Servicio de interés", message: "Cuéntanos sobre tu proyecto",
    services: ["Agentes de IA", "Automatización", "Growth Partner", "Plataformas SaaS"],
    choose: "Selecciona un servicio", submit: "Enviar solicitud", sending: "Enviando…",
    success: "Recibimos tu solicitud. Gracias por contactarnos.",
    error: "No pudimos confirmar el envío. Comprueba tu conexión e inténtalo de nuevo.",
    invalid: "Revisa los campos: nombre de 2 a 100 caracteres y mensaje de 10 a 2000.",
    limited: "Espera un minuto antes de enviar otra solicitud.",
    privacy: "Usaremos tu nombre, correo y los datos de esta solicitud para responder a tu consulta comercial. Evita incluir información sensible.",
  },
  en: {
    title: "Let's discuss your project", name: "Full name", email: "Email address",
    company: "Company (optional)", service: "Service of interest", message: "Tell us about your project",
    services: ["AI Agents", "Automation", "Growth Partner", "SaaS Platforms"],
    choose: "Choose a service", submit: "Send request", sending: "Sending…",
    success: "We received your request. Thank you for contacting us.",
    error: "We could not confirm submission. Check your connection and try again.",
    invalid: "Check the fields: name must have 2–100 characters and message 10–2000.",
    limited: "Wait a minute before sending another request.",
    privacy: "We will use your name, email and request details to respond to your business inquiry. Please avoid including sensitive information.",
  },
};
const serviceValues = ["agents", "automation", "growth", "saas"];
const emptyForm = { name: "", email: "", company: "", service: "", message: "" };

export default function ContactForm({ language }: Props) {
  const t = translations[language];
  const [form, setForm] = useState(emptyForm);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<"success" | "error" | "invalid" | "limited" | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending) return;
    const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()]));
    if (payload.name.length < 2 || payload.message.length < 10) {
      setResult("invalid"); return;
    }
    setSending(true);
    setResult(null);
    try {
      const response = await fetch("/leads", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload), signal: AbortSignal.timeout(15000),
      });
      if (response.status === 201) {
        const body = await response.json();
        if (body.status !== "created") throw new Error("Unexpected response");
        setResult("success"); setForm(emptyForm);
      } else {
        setResult(response.status === 429 ? "limited" : response.status === 422 ? "invalid" : "error");
      }
    } catch {
      setResult("error");
    } finally {
      setSending(false);
    }
  }
  function update(key: keyof typeof form, value: string) {
    setForm(previous => ({ ...previous, [key]: value })); setResult(null);
  }
  return (
    <form className="contact-form" onSubmit={handleSubmit} aria-busy={sending}>
      <h3>{t.title}</h3>
      <label htmlFor="contact-name">{t.name}</label>
      <input id="contact-name" autoComplete="name" required minLength={2} maxLength={100}
        disabled={sending} value={form.name} onChange={e => update("name", e.target.value)} />
      <label htmlFor="contact-email">{t.email}</label>
      <input id="contact-email" autoComplete="email" type="email" required maxLength={254}
        disabled={sending} value={form.email} onChange={e => update("email", e.target.value)} />
      <label htmlFor="contact-company">{t.company}</label>
      <input id="contact-company" autoComplete="organization" maxLength={150}
        disabled={sending} value={form.company} onChange={e => update("company", e.target.value)} />
      <label htmlFor="contact-service">{t.service}</label>
      <select id="contact-service" required disabled={sending} value={form.service} onChange={e => update("service", e.target.value)}>
        <option value="">{t.choose}</option>
        {serviceValues.map((value, index) => <option key={value} value={value}>{t.services[index]}</option>)}
      </select>
      <label htmlFor="contact-message">{t.message}</label>
      <textarea id="contact-message" required minLength={10} maxLength={2000} rows={4}
        disabled={sending} value={form.message} onChange={e => update("message", e.target.value)} />
      <p id="contact-privacy">{t.privacy}</p>
      <button className="btn btn-primary" type="submit" disabled={sending} aria-describedby="contact-privacy">
        {sending ? t.sending : t.submit}
      </button>
      {result && <p className={result === "success" ? "form-success" : "form-error"}
        role={result === "success" ? "status" : "alert"}>{t[result]}</p>}
    </form>
  );
}
