import {useEffect, useMemo, useState} from 'react';
import './study-review.css';

type HumanReview = {reference_review:{status:'verified'|'invalid'; reviewer:string; reviewed_at:string; rationale:string}|null;
  review:{score:0|1|2; reviewer:string; reviewed_at:string; rationale:string}|null};
type Case = HumanReview & {id:string; category:{name:string}; question:string; worked_solution:string;
  final_answer:string; careless_wrong_answer_and_why_it_fails:string; check_tool:string; candidate_answer:string};
type Run = {run_id:string; model_id:string; execution_path:string; cases:Case[]};

async function studyApi<T>(path:string, method='GET', body?:unknown):Promise<T> {
  const response=await fetch('/api/evaluation/study-pack'+path,{method,credentials:'include',
    headers:{'Content-Type':'application/json','X-Friday-Request':'1'},
    body:body===undefined?undefined:JSON.stringify(body)});
  const data=await response.json();
  if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:'Study review could not be saved.');
  return data as T;
}

export function StudyReview() {
  const [run,setRun]=useState<Run|null>(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [index,setIndex]=useState(0);
  const [category,setCategory]=useState('all');
  const [filter,setFilter]=useState('all');
  const [referenceStatus,setReferenceStatus]=useState<'pending'|'verified'|'invalid'>('pending');
  const [referenceNote,setReferenceNote]=useState('');
  const [score,setScore]=useState<''|'0'|'1'|'2'>('');
  const [rationale,setRationale]=useState('');
  const [notice,setNotice]=useState('');
  useEffect(()=>{let active=true;studyApi<Run>('').then(data=>{if(active){
    setRun(data);
    const first=data.cases[0];
    if(first){setReferenceStatus(first.reference_review?.status||'pending');
      setReferenceNote(first.reference_review?.rationale||'');
      setScore(first.review?String(first.review.score) as '0'|'1'|'2':'');
      setRationale(first.review?.rationale||'');}
  }})
    .catch(e=>{if(active)setError(String(e.message));});return()=>{active=false;};},[]);
  const rows=run?.cases||[];
  const current=rows[index];
  const categories=useMemo(()=>[...new Set(rows.map(row=>row.category.name))], [rows]);
  const visible=rows.filter(row=>(category==='all'||row.category.name===category) &&
    (filter==='all'||filter==='reviewed'&&!!row.review||filter==='unreviewed'&&!row.review||
      filter==='reference issue'&&row.reference_review?.status==='invalid'));
  const reviewed=rows.filter(row=>!!row.review).length;
  const invalid=rows.filter(row=>row.reference_review?.status==='invalid').length;
  const select=(position:number)=>{
    const row=rows[position];if(!row)return;
    setIndex(position);setReferenceStatus(row.reference_review?.status||'pending');
    setReferenceNote(row.reference_review?.rationale||'');
    setScore(row.review?String(row.review.score) as '0'|'1'|'2':'');
    setRationale(row.review?.rationale||'');setNotice('');
  };
  const save=async()=>{
    if(!current)return;
    if(referenceStatus==='pending'||!referenceNote.trim()) {setNotice('Check the reference with the listed tool and record what you checked.');return;}
    if(referenceStatus==='verified'&&(score===''||!rationale.trim())) {setNotice('Score the answer and explain the evidence.');return;}
    setBusy(true);setError('');setNotice('');
    try {
      const body={reference_status:referenceStatus,reference_note:referenceNote.trim(),
        score:referenceStatus==='verified'?Number(score):null,
        rationale:referenceStatus==='verified'?rationale.trim():''};
      const updated=await studyApi<HumanReview>(`/${encodeURIComponent(current.id)}/review`,'POST',body);
      setRun(previous=>previous?{...previous,cases:previous.cases.map(row=>row.id===current.id?{...row,...updated}:row)}:previous);
      setNotice(referenceStatus==='invalid'?'Reference issue saved. This answer remains unscored.':'Human review saved to FRIDAY.');
    }catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}
  };
  return <section className="study-review content-page">
    <p className="eyebrow">FRIDAY / OWNER EVALUATION</p><h1>Human review</h1>
    <p className="muted">Saved model responses are evidence of a run, not an accuracy score. Check each reference independently before grading the answer.</p>
    {error&&<div className="notice error" role="alert">{error}</div>}
    {!run?<p className="muted">Loading private study responses…</p>:<>
      <div className="study-summary"><div><strong>{rows.length}</strong><small>raw responses</small></div><div><strong>{reviewed}</strong><small>human reviewed</small></div><div><strong>{invalid}</strong><small>reference issues</small></div><div><strong>NO SCORE</strong><small>until checks finish</small></div></div>
      <p className="small muted">Model: {run.model_id} · Collection path: {run.execution_path} · Reviews are saved on FRIDAY’s server. The responses are never part of the public frontend bundle.</p>
      <div className="study-layout"><aside className="study-sidebar">
        <label>Category<select value={category} onChange={e=>setCategory(e.target.value)}><option value="all">All categories</option>{categories.map(name=><option key={name}>{name}</option>)}</select></label>
        <label>Show<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All</option><option value="unreviewed">Unreviewed</option><option value="reviewed">Reviewed</option><option value="reference issue">Reference issue</option></select></label>
        <div className="study-case-list" aria-label="Study cases">{visible.map(row=>{const position=rows.indexOf(row);return <button type="button" key={row.id} className={(position===index?'active ':'')+(row.review?'reviewed ':row.reference_review?.status==='invalid'?'invalid':'')} onClick={()=>select(position)}>{row.id}</button>;})}</div>
        <a className="study-export" href="/api/evaluation/study-pack/export" download>Export private review JSONL ↓</a>
        <p className="small muted">Export includes all 140 raw answers and your recorded checks. Keep it private. No scored report is generated here.</p>
      </aside><article className="study-case">{current&&<>
        <p className="eyebrow">{current.category.name} · {index+1} OF {rows.length} · {current.id}</p><h2>{current.question}</h2>
        <div className="study-pair"><section><h3>Worked reference · verify first</h3><p>{current.worked_solution}</p><h3>Final answer</h3><p>{current.final_answer}</p><h3>Careless answer</h3><p>{current.careless_wrong_answer_and_why_it_fails}</p><p className="study-tool">Check with: {current.check_tool}</p></section>
          <section><h3>Saved model response · ungraded</h3><p>{current.candidate_answer}</p></section></div>
        <div className="study-form"><label>Reference check<select value={referenceStatus} onChange={e=>{const value=e.target.value as typeof referenceStatus;setReferenceStatus(value);if(value==='invalid')setScore('');}}><option value="pending">Not checked</option><option value="verified">I checked the reference; sound</option><option value="invalid">Reference has an error</option></select></label>
          <label>What did you check or find?<textarea value={referenceNote} maxLength={2000} rows={3} onChange={e=>setReferenceNote(e.target.value)} placeholder="Calculation, assumptions, units, or discrepancy"/></label>
          {referenceStatus==='verified'&&<><fieldset><legend>Model answer assessment</legend>{([['0','Incorrect'],['1','Partly correct'],['2','Correct with units and conditions']] as const).map(([value,label])=><label key={value}><input type="radio" name="study-score" value={value} checked={score===value} onChange={()=>setScore(value)}/>{value} · {label}</label>)}</fieldset>
            <label>Specific evidence for this score<textarea value={rationale} maxLength={2000} rows={3} onChange={e=>setRationale(e.target.value)} placeholder="Which steps, values, and units are right or wrong?"/></label></>}
          <div className="study-actions"><button type="button" onClick={()=>select((index-1+rows.length)%rows.length)}>← Previous</button><button type="button" disabled={busy} onClick={()=>void save()}>Save human review</button><button type="button" onClick={()=>select((index+1)%rows.length)}>Next →</button></div>
          {notice&&<p className="small" role="status">{notice}</p>}</div>
      </>}</article></div>
    </>}
  </section>;
}
