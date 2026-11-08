import { useEffect, useState, type FormEvent } from "react";
import type { Language } from "../services";

type Business = { id: string; name: string; is_active: boolean; booking_enabled: boolean };
type BusinessUser = { id: number; email: string; is_active: boolean };
type Props = { language: Language; onSessionEnded: () => void };
const copy = {
  es: {
    title: "Panel de administración", intro: "Gestiona los negocios y sus accesos a ORQENTIVA.",
    businesses: "Negocios", loading: "Cargando…", refresh: "Actualizar lista", empty: "Todavía no hay negocios. Crea el primero para comenzar.",
    active: "Activo", inactive: "Inactivo", manage: "Gestionar", selected: "Seleccionado", create: "Crear negocio", id: "Identificador del negocio", name: "Nombre del negocio",
    idHelp: "Usa minúsculas, números y guiones; por ejemplo, barberia-centro. Este identificador no se modifica después.",
    save: "Crear negocio", saving: "Guardando…", error: "No se pudo completar la operación. Actualiza la lista para comprobar el estado antes de reintentar.",
    duplicateBusiness: "Ese identificador ya existe. Elige otro o selecciona el negocio existente.", invalid: "Revisa los datos. El nombre es obligatorio y la contraseña debe tener entre 12 y 128 caracteres.",
    businessCreated: "Negocio creado.", choose: "Selecciona un negocio para gestionar su estado y sus usuarios.",
    access: "Acceso del negocio", enable: "Activar negocio", disable: "Desactivar negocio", confirm: "Confirmar desactivación", cancel: "Cancelar",
    warning: "Se cerrarán las sesiones de este negocio y sus usuarios no podrán entrar. Sus servicios y reservas se conservarán.",
    disabledHelp: "Este negocio está desactivado. Sus usuarios podrán iniciar sesión cuando lo actives de nuevo.",
    enabled: "Negocio activado. Sus usuarios ya pueden iniciar sesión.", disabled: "Negocio desactivado. Se cerraron sus sesiones.",
    users: "Administradores del negocio", noUsers: "Este negocio todavía no tiene cuentas de acceso.",
    newUser: "Crear cuenta de cliente", email: "Correo electrónico", password: "Contraseña inicial", repeat: "Repite la contraseña",
    passwordHelp: "Entre 12 y 128 caracteres. Comunícala al titular por un canal privado; no se envía por correo automáticamente.",
    createUser: "Crear cuenta", userCreated: "Cuenta creada y asignada a este negocio.", duplicateUser: "Ese correo ya tiene una cuenta. No se ha modificado ni trasladado.",
    mismatch: "Las contraseñas no coinciden.", unavailable: "El negocio ya no está disponible. Actualiza la lista.",
    total: "negocios registrados", status: "Estado", accountState: "Cuenta", retry: "Volver a cargar usuarios",
  },
  en: {
    title: "Administration dashboard", intro: "Manage businesses and their access to ORQENTIVA.",
    businesses: "Businesses", loading: "Loading…", refresh: "Refresh list", empty: "No businesses yet. Create the first one to get started.",
    active: "Active", inactive: "Inactive", manage: "Manage", selected: "Selected", create: "Create business", id: "Business identifier", name: "Business name",
    idHelp: "Use lowercase letters, numbers and hyphens; for example, downtown-barbershop. This identifier cannot be changed later.",
    save: "Create business", saving: "Saving…", error: "The operation could not be completed. Refresh the list to check the current state before trying again.",
    duplicateBusiness: "That identifier already exists. Choose another or select the existing business.", invalid: "Check the fields. A name is required and passwords must contain 12–128 characters.",
    businessCreated: "Business created.", choose: "Select a business to manage its status and users.",
    access: "Business access", enable: "Activate business", disable: "Deactivate business", confirm: "Confirm deactivation", cancel: "Cancel",
    warning: "This business's sessions will be closed and its users will be unable to sign in. Services and bookings will be preserved.",
    disabledHelp: "This business is inactive. Its users will be able to sign in after you activate it again.",
    enabled: "Business activated. Its users can now sign in.", disabled: "Business deactivated. Its sessions have been closed.",
    users: "Business administrators", noUsers: "This business does not have any accounts yet.",
    newUser: "Create client account", email: "Email address", password: "Initial password", repeat: "Repeat password",
    passwordHelp: "Use 12–128 characters. Share it with the account holder through a private channel; no email is sent automatically.",
    createUser: "Create account", userCreated: "Account created and assigned to this business.", duplicateUser: "That email already has an account. It has not been changed or moved.",
    mismatch: "Passwords do not match.", unavailable: "The business is no longer available. Refresh the list.",
    total: "registered businesses", status: "Status", accountState: "Account", retry: "Reload users",
  },
};
type Message = "error" | "invalid" | "duplicateBusiness" | "businessCreated" | "enabled" | "disabled" | "userCreated" | "duplicateUser" | "mismatch" | "unavailable" | null;
const successes = new Set(["businessCreated", "enabled", "disabled", "userCreated"]);

class ApiError extends Error { status: number; constructor(status: number) { super("Request failed"); this.status = status; } }
async function adminRequest(path: string, options: RequestInit = {}) {
  const response = await fetch(`/admin/businesses${path}`, {
    credentials: "same-origin", cache: "no-store", ...options,
    headers: {"Content-Type": "application/json", ...options.headers},
    signal: options.signal ?? AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new ApiError(response.status);
  return response.json();
}
function classify(error: unknown, duplicate: Message = "error"): Message {
  if (!(error instanceof ApiError)) return "error";
  return error.status === 409 ? duplicate : error.status === 422 ? "invalid" : error.status === 404 ? "unavailable" : "error";
}
function sessionLost(error: unknown) { return error instanceof ApiError && (error.status === 401 || error.status === 403); }
function Feedback({ message, language }: {message: Message; language: Language}) {
  return message && <p className={successes.has(message) ? "dashboard-success" : "dashboard-error"} role={successes.has(message) ? "status" : "alert"}>{copy[language][message]}</p>;
}

export default function AdminDashboard({ language, onSessionEnded }: Props) {
  const t = copy[language];
  const [agenda,setAgenda]=useState(false);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reload, setReload] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<Message>(null);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    let alive = true;
    adminRequest("", {signal:controller.signal}).then(data => {
      if (alive) { setBusinesses(data); setSelected(previous => data.some((item: Business) => item.id === previous) ? previous : null); }
    }).catch(error => {
      if (!alive) return;
      if (sessionLost(error)) onSessionEnded();
      else setLoadError(true);
    }).finally(() => { clearTimeout(timeout); if (alive) setLoading(false); });
    return () => { alive = false; clearTimeout(timeout); controller.abort(); };
  }, [reload, onSessionEnded]);

  async function createBusiness(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    if (!name.trim()) { setMessage("invalid"); return; }
    setSaving(true); setMessage(null);
    try {
      const business = await adminRequest("", {method:"POST", body:JSON.stringify({id:id.trim(), name:name.trim(), booking_enabled:agenda})});
      setBusinesses(previous => [...previous, business].sort((a,b) => a.name.localeCompare(b.name)));
      setAgenda(false); setSelected(business.id); setId(""); setName(""); setMessage("businessCreated");
    } catch (error) {
      if (sessionLost(error)) onSessionEnded();
      else setMessage(classify(error, "duplicateBusiness"));
    } finally { setSaving(false); }
  }
  const business = businesses.find(item => item.id === selected);
  return <div className="admin-dashboard" aria-labelledby="admin-title">
    <header className="dashboard-heading"><div><span className="eyebrow">ORQENTIVA</span><h3 id="admin-title">{t.title}</h3><p>{t.intro}</p></div>
      <button type="button" className="dashboard-secondary" disabled={loading || saving} onClick={() => { setLoading(true); setLoadError(false); setReload(value => value + 1); }}>{t.refresh}</button></header>
    {loading ? <p role="status">{t.loading}</p> : loadError ? <p role="alert" className="dashboard-error">{t.error}</p> : <>
      <p className="dashboard-count">{businesses.length} {t.total}</p>
      <div className="dashboard-layout">
        <section className="dashboard-card" aria-labelledby="business-list-title"><h4 id="business-list-title">{t.businesses}</h4>
          {businesses.length === 0 ? <p>{t.empty}</p> : <ul className="business-list">{businesses.map(item => <li key={item.id}>
            <div><strong>{item.name}</strong><small>{item.id}</small><span className={`business-badge ${item.is_active ? "is-active" : "is-inactive"}`}>{item.is_active ? t.active : t.inactive}</span></div>
            <button type="button" className="dashboard-secondary" aria-pressed={selected === item.id} onClick={() => setSelected(item.id)}>{selected === item.id ? t.selected : t.manage}<span className="sr-only">: {item.name}</span></button>
          </li>)}</ul>}
        </section>
        <section className="dashboard-card" aria-labelledby="business-create-title"><h4 id="business-create-title">{t.create}</h4>
          <form onSubmit={createBusiness} aria-busy={saving}><fieldset disabled={saving} className="dashboard-fields">
            <label htmlFor="business-id">{t.id}</label><input id="business-id" value={id} onChange={e=>setId(e.target.value)} required maxLength={50} pattern="[a-z0-9][a-z0-9\-]*" aria-describedby="business-id-help" autoCapitalize="none" autoComplete="off" />
            <label><input type="checkbox" checked={agenda} onChange={e=>setAgenda(e.target.checked)}/> {language==="es"?"Incluir agenda de citas":"Include appointment scheduling"}</label>
            <small id="business-id-help">{t.idHelp}</small>
            <label htmlFor="business-name">{t.name}</label><input id="business-name" value={name} onChange={e=>setName(e.target.value)} required maxLength={150} autoComplete="organization" />
            <button className="btn btn-primary" type="submit">{saving ? t.saving : t.save}</button>
          </fieldset></form><Feedback message={message} language={language} />
        </section>
      </div>
      {business ? <BusinessManager key={business.id} business={business} language={language} onSessionEnded={onSessionEnded}
        onChange={updated => setBusinesses(previous => previous.map(item => item.id === updated.id ? updated : item))} /> : <p>{t.choose}</p>}
    </>}
  </div>;
}

function BusinessManager({ business, language, onChange, onSessionEnded }: Props & {business: Business; onChange: (value: Business) => void}) {
  const t = copy[language];
  const [users, setUsers] = useState<BusinessUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reload, setReload] = useState(0);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [message, setMessage] = useState<Message>(null);
  const endpoint = `/${encodeURIComponent(business.id)}`;
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    let alive = true;
    adminRequest(`${endpoint}/users`, {signal:controller.signal}).then(data => {if (alive) setUsers(data);}).catch(error => {
      if (!alive) return;
      if (sessionLost(error)) onSessionEnded(); else setLoadError(true);
    }).finally(() => {clearTimeout(timeout); if (alive) setLoading(false);});
    return () => {alive = false; clearTimeout(timeout); controller.abort();};
  }, [endpoint, reload, onSessionEnded]);

  async function changeState(active: boolean) {
    if (busy) return;
    setBusy(true); setMessage(null);
    try {
      const updated = await adminRequest(endpoint, {method:"PATCH", body:JSON.stringify({is_active:active})});
      onChange(updated); setConfirm(false); setMessage(active ? "enabled" : "disabled");
    } catch(error) {if (sessionLost(error)) onSessionEnded(); else setMessage(classify(error));}
    finally {setBusy(false);}
  }
  async function addUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    if (password !== repeat) {setMessage("mismatch"); return;}
    if (!password.trim()) {setMessage("invalid"); return;}
    setBusy(true); setMessage(null);
    try {
      const user = await adminRequest(`${endpoint}/users`, {method:"POST", body:JSON.stringify({email:email.trim(),password})});
      setUsers(previous => [...previous,user].sort((a,b) => a.email.localeCompare(b.email)));
      setEmail(""); setMessage("userCreated");
    } catch(error) {if (sessionLost(error)) onSessionEnded(); else setMessage(classify(error,"duplicateUser"));}
    finally {setPassword(""); setRepeat(""); setBusy(false);}
  }
  return <section className="dashboard-card business-manager" aria-labelledby="business-manager-title" aria-busy={busy}>
    <h4 id="business-manager-title">{business.name}</h4>
    <label><input type="checkbox" checked={business.booking_enabled} disabled={busy} onChange={async event=>{
      const enabled=event.target.checked;
      setBusy(true); setMessage(null);
      try {onChange(await adminRequest(endpoint+"/agenda",{method:"PUT",body:JSON.stringify({booking_enabled:enabled})}));}
      catch(error){if(sessionLost(error))onSessionEnded();else setMessage(classify(error));}
      finally{setBusy(false);}
    }}/> {language==="es"?"Agenda de citas habilitada":"Appointment scheduling enabled"}</label>
    <div className="business-access"><div><strong>{t.access}</strong><p>{t.status}: {business.is_active ? t.active : t.inactive}</p></div>
      <button type="button" disabled={busy} className={business.is_active ? "dashboard-danger" : "btn btn-primary"}
        onClick={() => business.is_active ? setConfirm(true) : changeState(true)}>{business.is_active ? t.disable : t.enable}</button></div>
    {confirm && business.is_active && <div className="dashboard-confirm" role="group" aria-label={t.confirm}>
      <p>{t.warning}</p><button type="button" className="dashboard-danger" disabled={busy} onClick={()=>changeState(false)}>{t.confirm}</button>
      <button type="button" className="dashboard-secondary" disabled={busy} onClick={()=>setConfirm(false)}>{t.cancel}</button>
    </div>}
    {!business.is_active && <p className="dashboard-confirm">{t.disabledHelp}</p>}
    <Feedback message={message} language={language} />
    <div className="dashboard-layout">
      <section aria-labelledby="business-users-title"><h5 id="business-users-title">{t.users}</h5>
        {loading ? <p role="status">{t.loading}</p> : loadError ? <><p className="dashboard-error" role="alert">{t.error}</p><button className="dashboard-secondary" onClick={()=>{setLoading(true); setLoadError(false); setReload(value=>value+1);}}>{t.retry}</button></> :
          users.length === 0 ? <p>{t.noUsers}</p> : <ul className="business-users">{users.map(user=><li key={user.id}><strong>{user.email}</strong><span>{t.accountState}: {user.is_active ? t.active : t.inactive}</span></li>)}</ul>}
      </section>
      <section aria-labelledby="business-user-create-title"><h5 id="business-user-create-title">{t.newUser}</h5>
        <form onSubmit={addUser}><fieldset className="dashboard-fields" disabled={busy || loading || loadError}>
          <label htmlFor="business-user-email">{t.email}</label><input id="business-user-email" type="email" autoComplete="off" value={email} onChange={e=>setEmail(e.target.value)} required maxLength={254} />
          <label htmlFor="business-user-password">{t.password}</label><input id="business-user-password" type="password" autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={12} maxLength={128} aria-describedby="business-password-help" />
          <small id="business-password-help">{t.passwordHelp}</small>
          <label htmlFor="business-user-repeat">{t.repeat}</label><input id="business-user-repeat" type="password" autoComplete="new-password" value={repeat} onChange={e=>setRepeat(e.target.value)} required minLength={12} maxLength={128} />
          <button className="btn btn-primary" type="submit">{busy ? t.saving : t.createUser}</button>
        </fieldset></form>
      </section>
    </div>
  </section>;
}
