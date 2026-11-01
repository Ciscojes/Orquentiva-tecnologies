import { useState, type FormEvent } from "react";

type Language = "es" | "en";

type Props = {
  language: Language;
};

const translations = {
  es: {
    title: "Hablemos de tu proyecto",
    name: "Nombre completo",
    email: "Correo electrónico",
    company: "Empresa",
    message: "Cuéntanos sobre tu proyecto",
    submit: "Validar información",
    success:
      "Formulario validado correctamente. El envío estará disponible próximamente.",
  },
  en: {
    title: "Let's discuss your project",
    name: "Full name",
    email: "Email address",
    company: "Company",
    message: "Tell us about your project",
    submit: "Validate information",
    success: "Form validated successfully. Submission will be available soon.",
  },
};

export default function ContactForm({ language }: Props) {
  const t = translations[language];

  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    message: "",
  });

  const [validated, setValidated] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!form.name.trim() || !form.email.trim() || !form.message.trim()) {
      setValidated(false);
      return;
    }

    setValidated(true);
  }

  return (
    <form className="contact-form" onSubmit={handleSubmit}>
      <h3>{t.title}</h3>

      <label htmlFor="contact-name">{t.name}</label>
      <input
        id="contact-name"
        type="text"
        required
        minLength={2}
        maxLength={100}
        value={form.name}
        onChange={(e) => {
          setValidated(false);
          setForm({ ...form, name: e.target.value });
        }}
      />

      <label htmlFor="contact-email">{t.email}</label>
      <input
        id="contact-email"
        type="email"
        required
        value={form.email}
        onChange={(e) => {
          setValidated(false);
          setForm({ ...form, email: e.target.value });
        }}
      />

      <label htmlFor="contact-company">{t.company}</label>
      <input
        id="contact-company"
        type="text"
        value={form.company}
        onChange={(e) => {
          setValidated(false);
          setForm({ ...form, company: e.target.value });
        }}
      />

      <label htmlFor="contact-message">{t.message}</label>
      <textarea
        id="contact-message"
        required
        minLength={10}
        rows={4}
        value={form.message}
        onChange={(e) => {
          setValidated(false);
          setForm({ ...form, message: e.target.value });
        }}
      />

      <button className="btn btn-primary" type="submit">
        {t.submit}
      </button>

      {validated && (
        <p className="form-success" role="status">
          {t.success}
        </p>
      )}
    </form>
  );
}
