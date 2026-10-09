import {useEffect, useState} from 'react';
import './operating-desk.css';

type Company = {id:string; name:string; offer:string; audience:string; channel:string; money_rules:string};
type Person = {id:string; role:string; name:string; published_video_title:string; video_verified_at:number|null;
  open_loop:string; last_contact_at:number|null; joined_at:number|null; join_evidence:string; opted_out:boolean; paid_on_time:string};
type Job = {id:string; title:string; creator_id:string; brief:string; sample_fee:string; created:number};
type Draft = {id:string; tool:string; draft:string; status:string; created:number; result:{model_called?:boolean}};
type Desk = {company:Company; people:Person[]; jobs:Job[]; drafts:Draft[]};
type Tool = 'match'|'draft_outreach'|'chase_silent'|'draft_invoice'|'weekly_note';

async function api<T>(path:string, method='GET', body?:unknown):Promise<T> {
  const response = await fetch('/api/operating'+path, {method, credentials:'include',
    headers:{'Content-Type':'application/json','X-Friday-Request':'1'},
    body:body === undefined ? undefined : JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'The desk could not save this change.');
  return data as T;
}

export function OperatingDesk() {
  const [companies,setCompanies] = useState<Company[]>([]);
  const [companyId,setCompanyId] = useState('');
  const [desk,setDesk] = useState<Desk|null>(null);
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const [companyName,setCompanyName] = useState('');
  const [notes,setNotes] = useState({offer:'',audience:'',channel:'',money_rules:''});
  const [person,setPerson] = useState({role:'creator',name:'',published_video_title:'',published_video_url:'',
    video_verified:false,open_loop:'',join_evidence:''});
  const [job,setJob] = useState({creator_id:'',title:'',brief:'',creator_confirmation:'',sample_scope:'',
    sample_fee:'',sample_deadline:'',invoice_amount:''});
  const [tool,setTool] = useState<Tool>('weekly_note');
  const [personId,setPersonId] = useState('');
  const [jobId,setJobId] = useState('');

  const refresh = async (id:string) => {
    const loaded = await api<Desk>(`/companies/${id}`);
    setDesk(loaded);
    setNotes({offer:loaded.company.offer,audience:loaded.company.audience,
      channel:loaded.company.channel,money_rules:loaded.company.money_rules});
  };
  useEffect(() => {let active=true; api<Company[]>('/companies').then(rows => {
    if (!active) return; setCompanies(rows); if (rows.length) setCompanyId(rows[0].id);
  }).catch(e => {if(active) setError(String(e.message));}); return () => {active=false;};}, []);
  useEffect(() => {if(companyId) void refresh(companyId).catch(e => setError(String(e.message)));}, [companyId]);
  const act = async (run:()=>Promise<void>) => {setBusy(true);setError('');try{await run();}catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}};
  const creators = desk?.people.filter(p=>p.role==='creator') || [];
  const editors = desk?.people.filter(p=>p.role==='editor') || [];

  return <section className="operating-desk content-page">
    <p className="eyebrow">FRIDAY / PRIVATE OPERATIONS</p><h1>Company desks</h1>
    <p className="muted">Read the record, then draft. FRIDAY never sends messages, changes prices, or moves money here.</p>
    {error && <div className="notice error" role="alert">{error}</div>}
    <div className="desk-tabs" role="tablist" aria-label="Company desks">
      {companies.map(c=><button key={c.id} role="tab" aria-selected={companyId===c.id} className={companyId===c.id?'active':''} onClick={()=>setCompanyId(c.id)}>{c.name}</button>)}
    </div>
    <form className="desk-inline" onSubmit={e=>{e.preventDefault();void act(async()=>{
      const created=await api<Company>('/companies','POST',{name:companyName});
      setCompanies(v=>[...v,created]);setCompanyId(created.id);setCompanyName('');
    });}}><label>Add another company when named<input value={companyName} onChange={e=>setCompanyName(e.target.value)} maxLength={120} placeholder="Company name"/></label><button disabled={busy||!companyName.trim()}>Create desk</button></form>
    {desk && <>
      <div className="desk-grid">
        <article className="desk-card"><h2>{desk.company.name} facts</h2><p className="small muted">Only owner-supplied notes are treated as company facts. Leave UNKNOWN where a fact is missing.</p>
          <form onSubmit={e=>{e.preventDefault();void act(async()=>{await api(`/companies/${companyId}/notes`,'PUT',notes);await refresh(companyId);});}}>
            {(['offer','audience','channel','money_rules'] as const).map(key=><label key={key}>{key.replace('_',' ')}<textarea rows={2} maxLength={2000} value={notes[key]} onChange={e=>setNotes(v=>({...v,[key]:e.target.value}))}/></label>)}
            <button disabled={busy}>Save company facts</button>
          </form>
        </article>
        <article className="desk-card"><h2>Person record</h2><p className="small muted">Record only what you know. Video verification and creator joins are your attestations, not FRIDAY research.</p>
          <form onSubmit={e=>{e.preventDefault();void act(async()=>{
            await api(`/companies/${companyId}/people`,'POST',person);
            setPerson({role:'creator',name:'',published_video_title:'',published_video_url:'',video_verified:false,open_loop:'',join_evidence:''});
            await refresh(companyId);
          });}}>
            <label>Role<select value={person.role} onChange={e=>setPerson(v=>({...v,role:e.target.value}))}><option value="creator">Creator</option><option value="editor">Editor</option><option value="other">Other</option></select></label>
            <label>Name<input required maxLength={120} value={person.name} onChange={e=>setPerson(v=>({...v,name:e.target.value}))}/></label>
            {person.role==='creator' && <><label>Published video title<input maxLength={240} value={person.published_video_title} onChange={e=>setPerson(v=>({...v,published_video_title:e.target.value}))}/></label>
              <label>Published video HTTPS URL<input type="url" value={person.published_video_url} onChange={e=>setPerson(v=>({...v,published_video_url:e.target.value}))}/></label>
              <label className="desk-check"><input type="checkbox" checked={person.video_verified} onChange={e=>setPerson(v=>({...v,video_verified:e.target.checked}))}/> I checked that this video was published by this creator</label>
              <label>Join evidence, if this creator became a user<input maxLength={1000} value={person.join_evidence} onChange={e=>setPerson(v=>({...v,join_evidence:e.target.value}))} placeholder="UNKNOWN until confirmed"/></label></>}
            <label>Open loop<input maxLength={1000} value={person.open_loop} onChange={e=>setPerson(v=>({...v,open_loop:e.target.value}))}/></label>
            <button disabled={busy||!person.name.trim()}>Save person</button>
          </form>
        </article>
      </div>
      <article className="desk-card"><h2>People & memory</h2><div className="desk-list">{desk.people.length===0?<p className="muted">No people recorded yet.</p>:desk.people.map(p=><div key={p.id}><strong>{p.name}</strong><span>{p.role} · paid on time: {p.paid_on_time} · open loop: {p.open_loop||'UNKNOWN'}</span><small>{p.video_verified_at?'Published video owner-verified':'Video unverified'} · {p.joined_at?'Creator join recorded':'No join recorded'} · {p.last_contact_at?'Last contact recorded':'No contact recorded'}</small><button disabled={busy} onClick={()=>void act(async()=>{await api(`/companies/${companyId}/people/${p.id}`,'PATCH',{record_contact_now:true});await refresh(companyId);})}>Record that I contacted them</button></div>)}</div></article>
      <article className="desk-card"><h2>Real creator job</h2><p className="small muted">Record a job only after a creator has confirmed a brief. This is an owner attestation. Sample terms and invoice amount are immutable here once saved.</p>
        <form className="desk-job-form" onSubmit={e=>{e.preventDefault();void act(async()=>{
          await api(`/companies/${companyId}/jobs`,'POST',job);
          setJob({creator_id:'',title:'',brief:'',creator_confirmation:'',sample_scope:'',sample_fee:'',sample_deadline:'',invoice_amount:''});await refresh(companyId);
        });}}>
          <label>Creator<select required value={job.creator_id} onChange={e=>setJob(v=>({...v,creator_id:e.target.value}))}><option value="">Select a recorded creator</option>{creators.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
          <label>Job title<input required maxLength={240} value={job.title} onChange={e=>setJob(v=>({...v,title:e.target.value}))}/></label>
          <label>Creator brief<textarea required maxLength={4000} value={job.brief} onChange={e=>setJob(v=>({...v,brief:e.target.value}))}/></label>
          <label>How the creator confirmed this job<input required maxLength={1000} value={job.creator_confirmation} onChange={e=>setJob(v=>({...v,creator_confirmation:e.target.value}))}/></label>
          <label>Approved sample scope<input maxLength={1000} value={job.sample_scope} onChange={e=>setJob(v=>({...v,sample_scope:e.target.value}))}/></label>
          <label>Approved sample fee<input maxLength={80} value={job.sample_fee} onChange={e=>setJob(v=>({...v,sample_fee:e.target.value}))}/></label>
          <label>Sample deadline<input maxLength={80} value={job.sample_deadline} onChange={e=>setJob(v=>({...v,sample_deadline:e.target.value}))}/></label>
          <label>Already agreed invoice amount<input maxLength={80} value={job.invoice_amount} onChange={e=>setJob(v=>({...v,invoice_amount:e.target.value}))}/></label>
          <button disabled={busy||!creators.length}>Record creator job</button>
        </form>
        <div className="desk-list">{desk.jobs.map(j=><div key={j.id}><strong>{j.title}</strong><span>Creator brief recorded · {j.sample_fee||'Sample fee UNKNOWN'}</span></div>)}</div>
      </article>
      <article className="desk-card"><h2>Draft-only tools</h2><p className="small muted">These tools use validated templates and saved records. They do not call the model or take external action. If Settings has no configured model, they return NOT_RUN.</p>
        <form className="desk-tool-form" onSubmit={e=>{e.preventDefault();void act(async()=>{
          const result=await api<Draft|{status:'NOT_RUN'}>(`/companies/${companyId}/tools/${tool}`,'POST',{
            request_key:crypto.randomUUID(),person_id:personId||null,job_id:jobId||null});
          if(result.status==='NOT_RUN'){setError('NOT_RUN — configure a model in FRIDAY Settings.');return;}
          await refresh(companyId);
        });}}>
          <label>Tool<select value={tool} onChange={e=>setTool(e.target.value as Tool)}><option value="match">Match</option><option value="draft_outreach">Draft outreach</option><option value="chase_silent">Chase silent</option><option value="draft_invoice">Draft invoice</option><option value="weekly_note">Weekly note</option></select></label>
          <label>Person<select value={personId} onChange={e=>setPersonId(e.target.value)}><option value="">No person</option>{[...creators,...editors,...desk.people.filter(p=>p.role==='other')].map(p=><option key={p.id} value={p.id}>{p.name} · {p.role}</option>)}</select></label>
          <label>Job<select value={jobId} onChange={e=>setJobId(e.target.value)}><option value="">No job</option>{desk.jobs.map(j=><option key={j.id} value={j.id}>{j.title}</option>)}</select></label>
          <button disabled={busy}>Create owner-review draft</button>
        </form>
      </article>
      <article className="desk-card"><h2>Draft log</h2><p className="small muted">Request, tool result and draft are saved. Every customer-visible item stays pending your review. There is no send or pay action.</p>
        <div className="desk-list">{desk.drafts.length===0?<p className="muted">No draft runs yet.</p>:desk.drafts.map(d=><div key={d.id}><small>{new Date(d.created*1000).toLocaleString()} · {d.tool} · {d.status}</small><p>{d.draft}</p><small>Validated template · model called: {String(d.result.model_called)}</small></div>)}</div>
      </article>
    </>}
  </section>;
}
