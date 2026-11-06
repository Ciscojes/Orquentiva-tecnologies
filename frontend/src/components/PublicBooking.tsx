import { useEffect, useState, type FormEvent } from "react";
import type { Language } from "../services";

type Catalog = {name:string; services:{id:number;name:string;duration_minutes:number}[]; team:{id:number;name:string;service_ids:number[]}[]};
const copy = {
  es:{
    "title": "Reservar una cita",
    "service": "Servicio",
    "professional": "Profesional",
    "any": "Cualquiera disponible",
    "day": "Fecha",
    "time": "Horario (Costa Rica)",
    "customer": "Tu nombre",
    "confirm": "Confirmar reserva",
    "choose": "Elige un turno",
    "empty": "No hay turnos disponibles.",
    "success": "Tu cita está confirmada.",
    "retry": "Consultar de nuevo",
    "unavailable": "La agenda no está disponible.",
    "conflict": "El turno ya no está disponible. Elige otro.",
    "failure": "No se pudo confirmar. Reintenta con los mismos datos.",
    "loading": "Cargando…",
    "noServices": "Este negocio todavía no ofrece servicios para reservar."
},
  en:{
    "title": "Book an appointment",
    "service": "Service",
    "professional": "Professional",
    "any": "Anyone available",
    "day": "Date",
    "time": "Time (Costa Rica)",
    "customer": "Your name",
    "confirm": "Confirm booking",
    "choose": "Choose a time",
    "empty": "No available times.",
    "success": "Your booking is confirmed.",
    "retry": "Check again",
    "unavailable": "Scheduling is unavailable.",
    "conflict": "That time is no longer available. Choose another.",
    "failure": "Confirmation failed. Retry with the same details.",
    "loading": "Loading…",
    "noServices": "This business has no services available to book yet."
}
};
export default function PublicBooking({business,language}:{business:string;language:Language}){
  const t=copy[language];
  const [catalog,setCatalog]=useState<Catalog|null>(null);
  const [service,setService]=useState("");
  const [person,setPerson]=useState("");
  const [day,setDay]=useState("");
  const [stamp,setStamp]=useState("");
  const [name,setName]=useState("");
  const [slots,setSlots]=useState<string[]>([]);
  const [loading,setLoading]=useState(false);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState<keyof typeof copy.es|null>(null);
  const [retry,setRetry]=useState(0);
  const [catalogRetry,setCatalogRetry]=useState(0);
  const [key,setKey]=useState(()=>crypto.randomUUID());
  const [assigned,setAssigned]=useState<number|null>(null);
  const path="/book/"+encodeURIComponent(business);
  useEffect(()=>{
    const controller=new AbortController();
    fetch(path,{signal:controller.signal}).then(async r=>{if(!r.ok)throw Error(); const data:Catalog=await r.json();
      if(!controller.signal.aborted){setCatalog(data);setService(String(data.services[0]?.id??""));}}).catch(()=>{if(!controller.signal.aborted)setMessage("unavailable");});
    return ()=>controller.abort();
  },[path,catalogRetry]);
  useEffect(()=>{
    if(!service||!day)return;
    const controller=new AbortController();
    const params=new URLSearchParams({service_id:service,day});
    if(person)params.set("professional_id",person);
    fetch(path+"/availability?"+params,{signal:controller.signal}).then(async r=>{if(!r.ok)throw Error();const data=await r.json();
      if(!controller.signal.aborted)setSlots(data);}).catch(()=>{if(!controller.signal.aborted)setMessage("unavailable");})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[path,service,day,person,retry]);
  function reset(){setLoading(true);setSlots([]);setStamp("");setMessage(null);setKey(crypto.randomUUID());}
  async function submit(e:FormEvent){
    e.preventDefault();if(!stamp||busy)return;
    setBusy(true);setMessage(null);
    try{
      const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},signal:AbortSignal.timeout(15000),
        body:JSON.stringify({service_id:Number(service),professional_id:person?Number(person):null,starts_at:stamp,customer_name:name,request_key:key})});
      if(r.status===409){reset();setMessage("conflict");setRetry(n=>n+1);return;}
      if(!r.ok)throw Error();
      const result=await r.json();setAssigned(result.professional_id);setMessage("success");
    }catch{setMessage("failure");}finally{setBusy(false);}
  }
  const time=(s:string)=>new Intl.DateTimeFormat(language,{timeZone:"America/Costa_Rica",hour:"2-digit",minute:"2-digit"}).format(new Date(s));
  return <section className="dashboard-card booking-public"><h1>{t.title}</h1><h2>{catalog?.name}</h2>
    {message!==null&&<p role="status">{t[message]} {assigned&&<strong>{day} · {time(stamp)} · {catalog?.team.find(p=>p.id===assigned)?.name}</strong>}</p>}
    {message==="unavailable"&&<button onClick={()=>{setMessage(null);if(!catalog)setCatalogRetry(n=>n+1);else setRetry(n=>n+1);}}>{t.retry}</button>}
    {!catalog&&message===null&&<p>{t.loading}</p>}
    {catalog&&!catalog.services.length&&<p>{t.noServices}</p>}
    {catalog&&catalog.services.length>0&&!assigned&&<form onSubmit={submit}><fieldset disabled={busy} className="dashboard-fields">
      <label>{t.service}<select value={service} onChange={e=>{reset();setPerson("");setService(e.target.value);}}>{catalog.services.map(s=><option key={s.id} value={s.id}>{s.name} · {s.duration_minutes} min</option>)}</select></label>
      <label>{t.professional}<select value={person} onChange={e=>{reset();setPerson(e.target.value);}}><option value="">{t.any}</option>{catalog.team.filter(p=>p.service_ids.includes(Number(service))).map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
      <label>{t.day}<input type="date" required value={day} onChange={e=>{reset();setDay(e.target.value);}}/></label>
      {day&&<label>{t.time}<select required disabled={loading} value={stamp} onChange={e=>{setStamp(e.target.value);setKey(crypto.randomUUID());}}><option value="">{loading?t.loading:slots.length?t.choose:t.empty}</option>{slots.map(s=><option key={s} value={s}>{time(s)}</option>)}</select></label>}
      <label>{t.customer}<input required maxLength={100} value={name} onChange={e=>{setName(e.target.value);setKey(crypto.randomUUID());}}/></label>
      <button className="btn btn-primary" disabled={!stamp||!name.trim()||loading}>{t.confirm}</button>
    </fieldset></form>}</section>;
}
