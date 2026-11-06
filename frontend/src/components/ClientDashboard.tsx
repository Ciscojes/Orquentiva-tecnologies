import { useEffect, useState, type FormEvent } from "react";
import KnowledgeEditor from "./KnowledgeEditor";
import type { Language } from "../services";

type Service = {id:number; name:string; price_crc:number; duration_minutes:number|null; is_active:boolean};
type Day = {weekday:number; is_closed:boolean; opens_at:string|null; closes_at:string|null};
type Hours = {configured:boolean; days:Day[]};
type Booking = {id:number; customer_name:string; starts_at:string; professional_id?:number; service_id?:number};
type Dashboard = {team:Member[]; booking_enabled:boolean; business:{id:string; name:string; time_zone:string}; services:Service[]; hours:Hours; appointments:Booking[]};
type Props = {language:Language; onSessionEnded:()=>void};
const copy = {
  es: {
    title:"Mi negocio", intro:"Organiza tus servicios, horarios de atención y reservas.", refresh:"Actualizar datos", loading:"Cargando tu negocio…",
    catalog:"Servicios", hours:"Horario de atención", bookings:"Reservas registradas", zone:"Hora de Costa Rica (UTC−06:00)",
    noServices:"Todavía no tienes servicios. Crea el primero.", active:"Activo", inactive:"Inactivo", undefined:"Por definir", minutes:"min", edit:"Editar", new:"Nuevo servicio",
    create:"Crear servicio", editTitle:"Editar servicio", name:"Nombre del servicio", price:"Precio en colones (CRC)", duration:"Duración en minutos", enabled:"Servicio activo",
    save:"Guardar cambios", saving:"Guardando…", cancel:"Cancelar edición", serviceSaved:"Servicio guardado.",
    invalidService:"Revisa nombre, precio entero y duración de 5 a 480 minutos.", error:"No se pudo completar la operación. Actualiza los datos para comprobar el estado antes de reintentar.",
    missing:"El servicio ya no está disponible. Actualiza los datos.", retry:"Volver a cargar", notConfigured:"Todavía no has guardado un horario de atención.",
    hoursHelp:"Configura un intervalo por día. Los cambios no modifican las reservas ya registradas.", closed:"Cerrado", opens:"Apertura", closes:"Cierre", saveHours:"Guardar horario",
    hoursSaved:"Horario guardado.", invalidHours:"Cada día abierto necesita una apertura anterior al cierre, dentro del mismo día.",
    days:["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"],
    noBookings:"Todavía no hay reservas registradas.", customer:"Cliente", date:"Fecha y hora", reference:"Referencia", readOnly:"Consulta de reservas existentes. La creación y modificación de citas se incorporarán en un próximo incremento.",
    countServices:"servicios en el catálogo", countBookings:"reservas registradas", currencyHelp:"Importe entero, sin decimales.", durationHelp:"Define el tiempo real del servicio; los anteriores no tienen duración asignada.",
  },
  en: {
    title:"My business", intro:"Organize your services, opening hours and bookings.", refresh:"Refresh data", loading:"Loading your business…",
    catalog:"Services", hours:"Opening hours", bookings:"Recorded bookings", zone:"Costa Rica time (UTC−06:00)",
    noServices:"No services yet. Create your first one.", active:"Active", inactive:"Inactive", undefined:"Not set", minutes:"min", edit:"Edit", new:"New service",
    create:"Create service", editTitle:"Edit service", name:"Service name", price:"Price in colones (CRC)", duration:"Duration in minutes", enabled:"Active service",
    save:"Save changes", saving:"Saving…", cancel:"Cancel editing", serviceSaved:"Service saved.",
    invalidService:"Check the name, whole-number price and duration of 5–480 minutes.", error:"The operation could not be completed. Refresh the data to check the current state before trying again.",
    missing:"This service is no longer available. Refresh the data.", retry:"Reload", notConfigured:"You have not saved opening hours yet.",
    hoursHelp:"Set one interval per day. Changes do not modify bookings already recorded.", closed:"Closed", opens:"Opening", closes:"Closing", saveHours:"Save opening hours",
    hoursSaved:"Opening hours saved.", invalidHours:"Each open day needs an opening time before its closing time, within the same day.",
    days:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    noBookings:"No bookings recorded yet.", customer:"Customer", date:"Date and time", reference:"Reference", readOnly:"View existing bookings. Creating and modifying appointments will be added in a future increment.",
    countServices:"services in your catalog", countBookings:"recorded bookings", currencyHelp:"Whole amount, without decimals.", durationHelp:"Set the actual service duration; existing services do not have a duration assigned.",
  },
};
type Message = "error"|"missing"|"invalidService"|"invalidHours"|"serviceSaved"|"hoursSaved"|null;
class ApiError extends Error {status:number; constructor(status:number) {super("Request failed");this.status=status;}}
async function request(path:string, options:RequestInit={}) {
  const response = await fetch(`/client/${path}`, {credentials:"same-origin",cache:"no-store",...options,
    headers:{"Content-Type":"application/json",...options.headers},signal:options.signal??AbortSignal.timeout(15000)});
  if (!response.ok) throw new ApiError(response.status);
  return response.json();
}
function unauthorized(error:unknown) {return error instanceof ApiError && [401,403].includes(error.status);}
function errorMessage(error:unknown, invalid:Message):Message {
  return error instanceof ApiError ? error.status===422?invalid:error.status===404?"missing":"error":"error";
}
function Feedback({message,language}:{message:Message;language:Language}) {
  const success = message === "serviceSaved" || message === "hoursSaved";
  return message && <p className={success?"dashboard-success":"dashboard-error"} role={success?"status":"alert"}>{copy[language][message]}</p>;
}

export default function ClientDashboard({language,onSessionEnded}:Props) {
  const t=copy[language];
  const [data,setData]=useState<Dashboard|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState(false);
  const [reload,setReload]=useState(0);
  const [editing,setEditing]=useState<number|null>(null);
  const [serviceMessage,setServiceMessage]=useState<Message>(null);
  const [pending,setPending]=useState(0);
  const saving=pending>0;
  const markBusy=(busy:boolean)=>setPending(count=>count+(busy?1:-1));
  useEffect(()=>{
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),15000);
    let alive=true;
    request("dashboard",{signal:controller.signal}).then(value=>{if(alive)setData(value);}).catch(failure=>{
      if(!alive)return;
      if(unauthorized(failure))onSessionEnded(); else setError(true);
    }).finally(()=>{clearTimeout(timeout);if(alive)setLoading(false);});
    return()=>{alive=false;clearTimeout(timeout);controller.abort();};
  },[reload,onSessionEnded]);
  const locale=language==="es"?"es-CR":"en-US";
  const money=new Intl.NumberFormat(locale,{style:"currency",currency:"CRC",maximumFractionDigits:0});
  return <div className="admin-dashboard client-dashboard" aria-labelledby="client-title">
    <header className="dashboard-heading"><div><span className="eyebrow">{t.title}</span><h3 id="client-title">{data?.business.name??t.title}</h3>{data?.booking_enabled&&<p>{t.intro}</p>}</div>
      <button className="dashboard-secondary" disabled={loading||saving} onClick={()=>{setLoading(true);setError(false);setEditing(null);setServiceMessage(null);setReload(value=>value+1);}}>{t.refresh}</button></header>
    {loading?<p role="status">{t.loading}</p>:error||!data?<p className="dashboard-error" role="alert">{t.error}</p>:!data.booking_enabled?<p>{language==="es"?"Tu cuenta está activa. Contacta con ORQENTIVA para gestionar tus servicios contratados.":"Your account is active. Contact ORQENTIVA to manage your contracted services."}</p>:<>
      <p className="dashboard-count">{data.services.length} {t.countServices} · {data.appointments.length} {t.countBookings}</p>
      <div className="client-section-links"><a href="#client-services">{t.catalog}</a><a href="#client-hours">{t.hours}</a><a href="#client-bookings">{t.bookings}</a></div>
      <section id="client-services" className="dashboard-card" aria-labelledby="client-services-title"><h4 id="client-services-title">{t.catalog}</h4>
        <div className="dashboard-layout"><div>{data.services.length===0?<p>{t.noServices}</p>:<ul className="business-list client-services">{data.services.map(service=><li key={service.id}>
          <div><strong>{service.name}</strong><small>{money.format(service.price_crc)} · {service.duration_minutes===null?t.undefined:`${service.duration_minutes} ${t.minutes}`}</small>
            <span className={`business-badge ${service.is_active?"is-active":"is-inactive"}`}>{service.is_active?t.active:t.inactive}</span></div>
          <button className="dashboard-secondary" disabled={saving} onClick={()=>{setEditing(service.id);setServiceMessage(null);}}>{t.edit}<span className="sr-only">: {service.name}</span></button>
        </li>)}</ul>}</div>
        <div><ServiceEditor key={editing??"new"} language={language} service={data.services.find(service=>service.id===editing)} onSessionEnded={onSessionEnded}
          onBusy={markBusy} onCancel={()=>{setEditing(null);setServiceMessage(null);}}
          onSaved={service=>{setData(previous=>previous?{...previous,services:previous.services.some(item=>item.id===service.id)?previous.services.map(item=>item.id===service.id?service:item):[...previous.services,service]}:previous);setEditing(null);setServiceMessage("serviceSaved");}} />
          <Feedback message={serviceMessage} language={language}/></div>
        </div>
      </section>
      <HoursEditor key={reload} hours={data.hours} language={language} onSessionEnded={onSessionEnded} onBusy={markBusy}
        onSaved={hours=>setData(previous=>previous?{...previous,hours}:previous)}/>
      <KnowledgeEditor language={language} onSessionEnded={onSessionEnded}/>
      <Team data={data} language={language} onSessionEnded={onSessionEnded} onSaved={member=>setData(prev=>prev?{...prev,team:[...prev.team.filter(m=>m.id!==member.id),member].sort((a,b)=>a.id-b.id)}:prev)}/>
      <section id="client-bookings" className="dashboard-card" aria-labelledby="client-bookings-title"><h4 id="client-bookings-title">{t.bookings}</h4>
        <p>{t.zone}</p>
        {data.appointments.length===0?<p>{t.noBookings}</p>:<Agenda data={data} language={language}/>}
      </section>
    </>}
  </div>;
}

function ServiceEditor({language,service,onSessionEnded,onSaved,onBusy,onCancel}:Props & {service?:Service;onSaved:(value:Service)=>void;onBusy:(value:boolean)=>void;onCancel:()=>void}) {
  const t=copy[language];
  const [name,setName]=useState(service?.name??"");
  const [price,setPrice]=useState(service?String(service.price_crc):"");
  const [duration,setDuration]=useState(service?.duration_minutes?String(service.duration_minutes):"");
  const [active,setActive]=useState(service?.is_active??true);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState<Message>(null);
  async function save(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();if(busy)return;
    if(!name.trim()||price===""||duration===""||!Number.isInteger(Number(price))||!Number.isInteger(Number(duration))){setMessage("invalidService");return;}
    setBusy(true);onBusy(true);setMessage(null);
    try {
      const value=await request(service?`services/${service.id}`:"services",{method:service?"PUT":"POST",body:JSON.stringify({name:name.trim(),price_crc:Number(price),duration_minutes:Number(duration),is_active:active})});
      setName("");setPrice("");setDuration("");setActive(true);onSaved(value);
    } catch(error){if(unauthorized(error))onSessionEnded();else setMessage(errorMessage(error,"invalidService"));}
    finally{setBusy(false);onBusy(false);}
  }
  return <form className="client-service-editor" onSubmit={save} aria-busy={busy}><h5>{service?t.editTitle:t.new}</h5><fieldset className="dashboard-fields" disabled={busy}>
    <label htmlFor="service-name">{t.name}</label><input id="service-name" value={name} onChange={e=>setName(e.target.value)} required maxLength={150}/>
    <label htmlFor="service-price">{t.price}</label><input id="service-price" type="number" value={price} onChange={e=>setPrice(e.target.value)} required min={0} max={10000000} step={1} aria-describedby="service-price-help"/>
    <small id="service-price-help">{t.currencyHelp}</small>
    <label htmlFor="service-duration">{t.duration}</label><input id="service-duration" type="number" value={duration} onChange={e=>setDuration(e.target.value)} required min={5} max={480} step={1} aria-describedby="service-duration-help"/>
    <small id="service-duration-help">{t.durationHelp}</small>
    <label className="client-checkbox"><input type="checkbox" checked={active} onChange={e=>setActive(e.target.checked)}/>{t.enabled}</label>
    <button className="btn btn-primary" type="submit">{busy?t.saving:service?t.save:t.create}</button>
    {service&&<button className="dashboard-secondary" type="button" onClick={onCancel}>{t.cancel}</button>}
  </fieldset><Feedback message={message} language={language}/></form>;
}

function HoursEditor({language,hours,onSessionEnded,onBusy,onSaved}:Props & {hours:Hours;onBusy:(value:boolean)=>void;onSaved:(value:Hours)=>void}) {
  const t=copy[language];
  const [days,setDays]=useState<Day[]>(hours.days);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState<Message>(null);
  function change(weekday:number,update:Partial<Day>) {setDays(previous=>previous.map(day=>day.weekday===weekday?{...day,...update}:day));setMessage(null);}
  async function save(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(busy)return;
    if(days.some(day=>!day.is_closed&&(!day.opens_at||!day.closes_at||day.opens_at>=day.closes_at))){setMessage("invalidHours");return;}
    setBusy(true);onBusy(true);setMessage(null);
    try {
      const value=await request("hours",{method:"PUT",body:JSON.stringify({days:days.map(day=>day.is_closed?{...day,opens_at:null,closes_at:null}:day)})});
      setDays(value.days);onSaved(value);setMessage("hoursSaved");
    }catch(error){if(unauthorized(error))onSessionEnded();else setMessage(errorMessage(error,"invalidHours"));}
    finally{setBusy(false);onBusy(false);}
  }
  return <section id="client-hours" className="dashboard-card" aria-labelledby="client-hours-title"><h4 id="client-hours-title">{t.hours}</h4><p>{t.zone}</p><p>{t.hoursHelp}</p>
    {!hours.configured&&<p className="dashboard-confirm">{t.notConfigured}</p>}
    <form onSubmit={save} aria-busy={busy}><fieldset className="dashboard-fields" disabled={busy}>
      <WeekFields days={days} busy={busy} language={language} prefix="day" change={change}/>
      <button className="btn btn-primary client-save-hours" type="submit">{busy?t.saving:t.saveHours}</button>
    </fieldset><Feedback message={message} language={language}/></form>
  </section>;
}

function WeekFields({days,busy,language,prefix,change}:{days:Day[];busy:boolean;language:Language;prefix:string;change:(weekday:number,update:Partial<Day>)=>void}){
  const t=copy[language];
  return <div className="client-hours-grid">{days.map(day=><fieldset key={day.weekday} className="client-day"><legend>{t.days[day.weekday]}</legend>
        <label className="client-checkbox"><input id={`${prefix}-${day.weekday}-closed`} type="checkbox" checked={day.is_closed} onChange={e=>change(day.weekday,{is_closed:e.target.checked})}/>{t.closed}</label>
        <label htmlFor={`${prefix}-${day.weekday}-open`}>{t.opens}</label><input id={`${prefix}-${day.weekday}-open`} type="time" step={60} value={day.opens_at??""} required={!day.is_closed} disabled={day.is_closed||busy} onChange={e=>change(day.weekday,{opens_at:e.target.value||null})}/>
        <label htmlFor={`${prefix}-${day.weekday}-close`}>{t.closes}</label><input id={`${prefix}-${day.weekday}-close`} type="time" step={60} value={day.closes_at??""} required={!day.is_closed} disabled={day.is_closed||busy} onChange={e=>change(day.weekday,{closes_at:e.target.value||null})}/>
      </fieldset>)}</div>;
}

type Member = {id:number; name:string; service_ids:number[]; days:Day[]};
function Team({data,language,onSaved,onSessionEnded}:Props & {data:Dashboard;onSaved:(m:Member)=>void}){
  const es=language==="es";
  const [editing,setEditing]=useState<Member|null>(null);
  const [busy,setBusy]=useState(false);
  const [failed,setFailed]=useState(false);
  function editMember(m:Member){setEditing({...m});setFailed(false);}
  function change(weekday:number,update:Partial<Day>){
    if(editing)setEditing({...editing,days:editing.days.map(d=>d.weekday===weekday?{...d,...update}:d)});
  }
  async function save(e:FormEvent){
    e.preventDefault();if(!editing||busy)return;
    setBusy(true);setFailed(false);
    try{
      const {id,name,service_ids,days}=editing;
      const member=await request(id?"team/"+id:"team",{method:id?"PUT":"POST",body:JSON.stringify({name,service_ids,
        days:days.map(d=>d.is_closed?{...d,opens_at:null,closes_at:null}:d)})});
      onSaved(member);setEditing(null);
    }catch(error){if(unauthorized(error))onSessionEnded();else setFailed(true);}finally{setBusy(false);}
  }
  return <section className="dashboard-card"><h4>{es?"Mi equipo":"My team"}</h4>
    <ul className="business-list">{data.team.map(m=><li key={m.id}>{m.name}<button className="dashboard-secondary" disabled={busy} onClick={()=>editMember(m)}>{copy[language].edit}</button></li>)}</ul>
    <button className="dashboard-secondary" disabled={busy} onClick={()=>editMember({id:0,name:"",service_ids:[],days:data.hours.days})}>{es?"Añadir profesional":"Add professional"}</button>
    {editing&&<form onSubmit={save}><fieldset className="dashboard-fields" disabled={busy}>
      <label>{es?"Nombre público del profesional":"Public professional name"}<input required maxLength={100} value={editing.name} onChange={e=>setEditing({...editing,name:e.target.value})}/></label>
      <fieldset><legend>{copy[language].catalog}</legend>{data.services.map(s=><label key={s.id} className="client-checkbox"><input type="checkbox" checked={editing.service_ids.includes(s.id)} onChange={e=>setEditing({...editing,service_ids:e.target.checked?[...editing.service_ids,s.id]:editing.service_ids.filter(id=>id!==s.id)})}/>{s.name}</label>)}</fieldset>
      <WeekFields days={editing.days} prefix="member" language={language} busy={busy} change={change}/>
      <button className="btn btn-primary">{copy[language].save}</button><button type="button" className="dashboard-secondary" onClick={()=>setEditing(null)}>{copy[language].cancel}</button>
      {failed&&<p role="alert">{copy[language].error}</p>}
    </fieldset></form>}
    <p><a href={"#reservar/"+data.business.id}>{es?"Abrir enlace de reservas para compartir":"Open shareable booking link"}</a></p>
  </section>;
}
function Agenda({data,language}:{data:Dashboard;language:Language}){
  const groups=new Map<string,Booking[]>();
  for(const b of data.appointments)groups.set(b.starts_at,[...(groups.get(b.starts_at)??[]),b]);
  const columns:{id:number|null;name:string}[]=data.team.map(({id,name})=>({id,name}));
  if(data.appointments.some(b=>!b.professional_id))columns.push({id:null,name:language==="es"?"Sin asignar":"Unassigned"});
  const date=new Intl.DateTimeFormat(language,{timeZone:data.business.time_zone,dateStyle:"medium",timeStyle:"short"});
  return <div className="client-table-wrapper" tabIndex={0}><table className="client-bookings-table team-agenda"><thead><tr><th>{copy[language].date}</th>{columns.map(p=><th key={p.id??0}>{p.name}</th>)}</tr></thead><tbody>
    {[...groups].map(([stamp,rows])=><tr key={stamp}><th scope="row">{date.format(new Date(stamp))}</th>{columns.map(p=>{
      const b=rows.find(b=>(b.professional_id??null)===p.id);
      return <td key={p.id??0} className={b?"booked":"empty"}>{b?<><b className="mobile-person">{p.name} · </b>{b.customer_name} {data.services.find(s=>s.id===b.service_id)?.name}</>:"—"}</td>;
    })}</tr>)}</tbody></table></div>;
}
