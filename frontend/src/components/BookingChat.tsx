import { useRef, useState, type FormEvent } from "react";
import type { Language } from "../services";

type Draft = {step:string;clock?:string|null};
type Proposal = {service_id:number;professional_id:number;customer_name:string;starts_at:string;customer_contact?:string};
type Reply = {draft:Draft;reply:string;options:string[];proposal:Proposal|null};
type Source = {title:string;paragraph:number;quote:string};
type Knowledge = {kind:'knowledge';reply:string;sources:Source[];generated?:boolean};
type Line = {agent:boolean;text:string;sources?:Source[];generated?:boolean};
const copy = {
  es:{title:"Reservar por chat",intro:"Dime qué servicio buscas, con quién y qué día. Por ejemplo: «Quiero un corte con Ana el sábado a las 10».",
    input:"Tu mensaje",send:"Enviar",yes:"Confirmar cita",restart:"Empezar de nuevo",choose:"Elige una opción",ok:"Cita confirmada.",
    conflict:"Ese turno acaba de ocuparse.",error:"No pude completar la solicitud.",retry:"Reintentar",agent:"Asistente",you:"Tú",pending:"Consultando…"},
  en:{title:"Book by chat",intro:"Tell me the service, professional and day. For example: “A haircut with Ana on Saturday at 10”.",
    input:"Your message",send:"Send",yes:"Confirm appointment",restart:"Start over",choose:"Choose an option",ok:"Appointment confirmed.",
    conflict:"That time was just taken.",error:"The request could not be completed.",retry:"Retry",agent:"Assistant",you:"You",pending:"Checking…"}
};
export default function BookingChat({business,language}:{business:string;language:Language}){
  const t=copy[language];
  const [mode,setMode]=useState<'booking'|'knowledge'>('booking');
  const [lines,setLines]=useState<Line[]>([]);
  const [turn,setTurn]=useState<Reply|null>(null);
  const [input,setInput]=useState("");
  const [busy,setBusy]=useState(false);
  const [done,setDone]=useState(false);
  const [failed,setFailed]=useState(false);
  const key=useRef("");
  const inFlight=useRef(false);
  const last=useRef("");
  const endpoint="/book/"+encodeURIComponent(business);
  function append(agent:boolean,text:string,sources?:Source[],generated?:boolean){setLines(prev=>[...prev,{agent,text,sources,generated}]);}
  function restart(){setLines([]);setTurn(null);setDone(false);setFailed(false);setInput("");key.current="";}
  async function post(url:string,body:unknown){
    return fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),signal:AbortSignal.timeout(15000)});
  }
  async function send(message:string,retry=false){
    message=message.trim();
    if(!message||inFlight.current||done)return;
    inFlight.current=true;setBusy(true);setFailed(false);last.current=message;
    if(!retry)append(false,message);
    setInput("");
    try{
      let draft=turn?.draft;
      const affirmative=/^(sí|si|confirmo|confirmar cita|yes|confirm|confirm appointment)[.!]?$/i.test(message);
      if(mode==='booking'&&turn?.proposal&&affirmative){
        const response=await post(endpoint,{...turn.proposal,request_key:key.current});
        if(response.ok){append(true,t.ok);setDone(true);return;}
        if(response.status!==409)throw Error();
        append(true,t.conflict);draft={...turn.draft,clock:null};message="";
      }else if(mode==='booking'&&/^(no|cancelar|cancel|empezar de nuevo|start over)[.!]?$/i.test(message)){
        restart();return;
      }
      const response=await post(endpoint+"/chat",{message,language,mode,...(draft?{draft}:{})});
      if(!response.ok)throw Error();
      const next:Reply|Knowledge=await response.json();
      if('kind' in next){append(true,next.reply,next.sources,next.generated);setMode('knowledge');return;}
      if(next.proposal)key.current=crypto.randomUUID();
      setTurn(next);append(true,next.reply);
    }catch{setFailed(true);}finally{inFlight.current=false;setBusy(false);}
  }
  function submit(e:FormEvent){e.preventDefault();void send(input);}
  return <details className="booking-chat"><summary>{t.title}</summary><label>{language==='es'?'Quiero':'I want to'}<select value={mode} disabled={busy||done} onChange={e=>{setMode(e.target.value as 'booking'|'knowledge');setInput('');setFailed(false);}}><option value="booking">{t.title}</option><option value="knowledge">{language==='es'?'Consultar información del negocio':'Ask about the business'}</option></select></label>
    <p>{mode==='booking'?t.intro:language==='es'?'Pregunta por las políticas o condiciones publicadas por este negocio.':'Ask about policies or terms published by this business.'}</p>
    <div role="log" aria-live="polite">{lines.map((line,i)=><div key={i}><p><strong>{line.agent?t.agent:t.you}: </strong>{line.text}</p>{line.generated&&<p className="chat-sources-note">{language==='es'?'Respuesta redactada con IA a partir de:':'AI-written answer based on:'}</p>}{line.sources?.map((s,j)=><blockquote key={j}>{s.quote}<footer>{s.title} · {language==='es'?'párrafo':'paragraph'} {s.paragraph}</footer></blockquote>)}</div>)}</div>
    {failed&&<p role="alert">{t.error} <button disabled={busy} onClick={()=>void send(last.current,true)}>{t.retry}</button></p>}
    {busy&&<p role="status">{t.pending}</p>}
    {!done&&<form onSubmit={submit}><fieldset disabled={busy} className="dashboard-fields">
      {mode==='booking'&&!!turn?.options.length&&<label>{t.choose}<select value="" onChange={e=>void send(e.target.value)}><option value="">{t.choose}</option>{turn.options.map((option,i)=><option key={i}>{option}</option>)}</select></label>}
      <label>{t.input}<input maxLength={350} value={input} onChange={e=>setInput(e.target.value)}/></label>
      <button className="dashboard-secondary" disabled={!input.trim()}>{t.send}</button>
      {mode==='booking'&&turn?.proposal&&<button className="btn btn-primary" type="button" onClick={()=>void send(t.yes)}>{t.yes}</button>}
    </fieldset></form>}
    {!!lines.length&&<button className="dashboard-secondary" disabled={busy} onClick={restart}>{t.restart}</button>}
  </details>;
}
