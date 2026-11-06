import {useEffect,useState,type FormEvent} from "react";
import type {Language} from "../services";

type Doc={id:number;title:string;body:string;published:boolean};
const blank:Doc={id:0,title:"",body:"",published:false};
export default function KnowledgeEditor({language,onSessionEnded}:{language:Language;onSessionEnded:()=>void}){
  const es=language==="es";
  const [docs,setDocs]=useState<Doc[]>([]);
  const [draft,setDraft]=useState<Doc>(blank);
  const [busy,setBusy]=useState(false);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState(false);
  const [saved,setSaved]=useState(false);
  const [reload,setReload]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    fetch("/client/documents",{signal:controller.signal,cache:"no-store"}).then(async r=>{
      if([401,403].includes(r.status)){onSessionEnded();return;}
      if(!r.ok)throw Error();
      const values:Doc[]=await r.json();
      if(!controller.signal.aborted)setDocs(values);
    }).catch(()=>{if(!controller.signal.aborted)setError(true);})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[onSessionEnded,reload]);
  function edit(value:Doc){setDraft(value);setSaved(false);}
  async function save(e:FormEvent){
    e.preventDefault();if(busy)return;
    setError(false);setSaved(false);setBusy(true);
    try{
      const {id,...body}=draft;
      const r=await fetch("/client/documents"+(id?"/"+id:""),{method:id?"PUT":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),signal:AbortSignal.timeout(15000)});
      if([401,403].includes(r.status)){onSessionEnded();return;}
      if(!r.ok)throw Error();
      const result:Doc=await r.json();
      setDocs(prev=>id?prev.map(d=>d.id===id?result:d):[...prev,result]);setDraft(result);setSaved(true);
    }catch{setError(true);}finally{setBusy(false);}
  }
  return <section className="dashboard-card"><h4>{es?"Documentos del negocio":"Business documents"}</h4>
    <p>{es?"El chat puede citar los documentos publicados. Escribe una regla por párrafo y guarda solo información para tus clientes.":"The chat can quote published documents. Write one rule per paragraph and include only customer-facing information."}</p>
    {error&&<p role="alert">{es?"No se pudo completar la operación.":"The operation failed."} <button type="button" onClick={()=>{setLoading(true);setError(false);setReload(n=>n+1);}}>{es?"Actualizar lista":"Reload list"}</button></p>}
    {loading?<p>{es?"Cargando…":"Loading…"}</p>:<form onSubmit={save}><fieldset disabled={busy} className="dashboard-fields">
      <label>{es?"Documento":"Document"}<select value={draft.id} onChange={e=>edit(docs.find(d=>d.id===Number(e.target.value))??blank)}><option value={0}>{es?"Crear documento":"New document"}</option>{docs.map(d=><option value={d.id} key={d.id}>{d.title} · {d.published?(es?"Publicado":"Published"):(es?"Borrador":"Draft")}</option>)}</select></label>
      <label>{es?"Título del documento":"Document title"}<input required maxLength={120} value={draft.title} onChange={e=>edit({...draft,title:e.target.value})}/></label>
      <label>{es?"Contenido":"Content"}<textarea required rows={5} maxLength={6000} value={draft.body} onChange={e=>edit({...draft,body:e.target.value})}/></label>
      <label className="client-checkbox"><input type="checkbox" checked={draft.published} onChange={e=>edit({...draft,published:e.target.checked})}/>{es?"Publicar para consultas del chat":"Publish for chat answers"}</label>
      <button className="btn btn-primary" disabled={!draft.title.trim()||!draft.body.trim()}>{es?"Guardar documento":"Save document"}</button>
      {saved&&<p role="status">{es?"Documento guardado.":"Document saved."}</p>}
    </fieldset></form>}
  </section>;
}
