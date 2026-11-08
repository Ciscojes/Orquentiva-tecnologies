import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import AdminDashboard from "./AdminDashboard";
import ClientDashboard from "./ClientDashboard";
import type { Language } from "../services";

type Account = { id: number; email: string; role: "super_admin" | "business_admin"; business_id: string | null };
const text = {
  es: {
    title: "Acceso a ORQENTIVA", intro: "Ingresa con la cuenta asignada a tu negocio.",
    email: "Correo electrónico", password: "Contraseña", login: "Iniciar sesión", logout: "Cerrar sesión", busy: "Procesando…",
    checking: "Comprobando sesión…", invalid: "Correo o contraseña incorrectos.", limited: "Demasiados intentos. Espera un minuto antes de volver a intentarlo.",
    error: "No se pudo completar la operación. Comprueba la conexión e inténtalo de nuevo.", blocked: "El acceso no está habilitado para esta dirección. Contacta con el administrador.",
    welcome: "Sesión iniciada", admin: "Administrador de ORQENTIVA", business: "Administrador de negocio", company: "Empresa",
    next: "Tu acceso está verificado. Las herramientas de gestión de tu panel se incorporarán en el siguiente incremento.",
    retry: "Comprobar sesión", help: "¿Todavía no tienes cuenta?", consultation: "Solicitar asesoría", signedOut: "Has cerrado la sesión.",
  },
  en: {
    title: "Access ORQENTIVA", intro: "Sign in with the account assigned to your business.",
    email: "Email address", password: "Password", login: "Sign in", logout: "Sign out", busy: "Processing…",
    checking: "Checking session…", invalid: "Incorrect email or password.", limited: "Too many attempts. Wait a minute before trying again.",
    error: "The operation could not be completed. Check your connection and try again.", blocked: "Access is not enabled for this address. Contact the administrator.",
    welcome: "Signed in", admin: "ORQENTIVA administrator", business: "Business administrator", company: "Business",
    next: "Your access is verified. Dashboard management tools will be added in the next increment.",
    retry: "Check session", help: "Don’t have an account yet?", consultation: "Request a consultation", signedOut: "You have signed out.",
  },
};
type Notice = "invalid" | "limited" | "error" | "blocked" | "signedOut" | null;

async function authFetch(path: string, options: RequestInit = {}) {
  return fetch(`/auth/${path}`, { credentials: "same-origin", cache: "no-store", ...options, signal: AbortSignal.timeout(15000) });
}
async function readAccount(response: Response): Promise<Account> {
  const account = await response.json();
  if (typeof account.id !== "number" || typeof account.email !== "string" ||
      !["super_admin", "business_admin"].includes(account.role)) throw new Error("Invalid account response");
  return account;
}

export default function AccessPanel({ language, locationHash, onSessionChange }: { language: Language; locationHash: string; onSessionChange: (active: boolean) => void }) {
  const t = text[language];
  const [account, setAccount] = useState<Account | null>(null);
  const [checking, setChecking] = useState(true);
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState<Notice>(null);
  const sequence = useRef(0);
  const welcome = useRef<HTMLHeadingElement>(null);
  const endSession = useCallback(() => { setAccount(null); setNotice("blocked"); }, []);

  useEffect(() => {
    let mounted = true;
    const ticket = ++sequence.current;
    authFetch("me").then(async response => {
      const value = response.ok ? await readAccount(response) : null;
      if (!mounted || ticket !== sequence.current) return;
      setAccount(value);
      if (!response.ok && response.status !== 401) setNotice("error");
    }).catch(() => {
      if (mounted && ticket === sequence.current) setNotice("error");
    }).finally(() => {
      if (mounted && ticket === sequence.current) setChecking(false);
    });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!checking) onSessionChange(account !== null);
  }, [account, checking, locationHash, onSessionChange]);

  useEffect(() => {
    if (account) welcome.current?.focus();
    else if (!checking) document.getElementById("access-title")?.focus({preventScroll:true});
  }, [account, checking]);

  async function refreshSession() {
    if (busy) return;
    ++sequence.current;
    setBusy(true); setNotice(null);
    try {
      const response = await authFetch("me");
      if (response.ok) setAccount(await readAccount(response));
      else { setAccount(null); if (response.status !== 401) setNotice("error"); }
    } catch { setNotice("error"); }
    finally { setBusy(false); }
  }

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    ++sequence.current;
    setBusy(true); setNotice(null);
    try {
      const response = await authFetch("login", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({email: email.trim(), password}) });
      if (response.ok) setAccount(await readAccount(response));
      else setNotice(response.status === 401 ? "invalid" : response.status === 429 ? "limited" : response.status === 403 ? "blocked" : "error");
    } catch { setNotice("error"); }
    finally { setPassword(""); setBusy(false); }
  }

  async function logout() {
    if (busy) return;
    ++sequence.current;
    setBusy(true); setNotice(null);
    try {
      const response = await authFetch("logout", {method: "POST"});
      if (!response.ok) throw new Error("Logout failed");
      setAccount(null); setEmail(""); setPassword(""); setNotice("signedOut");
    } catch { setNotice("error"); }
    finally { setBusy(false); }
  }

  return <section className="access-section" id="access" aria-labelledby="access-title">
    <h1 id="access-title" tabIndex={-1}>{t.title}</h1><p>{t.intro}</p>
    {checking ? <p role="status">{t.checking}</p> : account ?
      <><div className="access-card" aria-busy={busy}>
        <h3 ref={welcome} tabIndex={-1}>{t.welcome}</h3>
        <p>{account.email}</p><p><strong>{account.role === "super_admin" ? t.admin : t.business}</strong></p>
        {account.business_id && <p>{t.company}: {account.business_id}</p>}
        <button className="btn btn-primary" onClick={logout} disabled={busy}>{busy ? t.busy : t.logout}</button>
        <button className="access-retry" onClick={refreshSession} disabled={busy}>{t.retry}</button>
      </div>{account.role === "super_admin" && <AdminDashboard key={account.id} language={language} onSessionEnded={endSession} />}{account.role === "business_admin" && <ClientDashboard key={account.id} language={language} onSessionEnded={endSession} />}</> :
      <form className="contact-form" onSubmit={login} aria-busy={busy}>
        <label htmlFor="login-email">{t.email}</label>
        <input id="login-email" type="email" autoComplete="username" required maxLength={254} value={email} onChange={e => setEmail(e.target.value)} disabled={busy} />
        <label htmlFor="login-password">{t.password}</label>
        <input id="login-password" type="password" autoComplete="current-password" required maxLength={128} value={password} onChange={e => setPassword(e.target.value)} disabled={busy} />
        <button type="submit" disabled={busy}>{busy ? t.busy : t.login}</button>
        <p className="access-help">{t.help} <a href="#contact">{t.consultation}</a></p>
        {notice === "error" && <button type="button" onClick={refreshSession} disabled={busy}>{t.retry}</button>}
      </form>}
    {notice && <p className={notice === "signedOut" ? "access-success" : "access-error"} role={notice === "signedOut" ? "status" : "alert"}>{t[notice]}</p>}
  </section>;
}
