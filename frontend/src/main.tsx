import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Markdown from 'react-markdown';
import './style.css';
import './experience.css';
import { AccessGate, AccessControl } from './Access';
import { Cinematic } from './Cinematic';
import { AmbientCore, Appearance, CommandPalette, CopyMessage, type Command } from './Experience';

type User = {is_owner: boolean; email: string; jobs_today: number; daily_job_limit: number};
type Status = {chat_configured: boolean; research_configured: boolean; model: string; provider: string; missing: string[]; capabilities: Record<string, string>};
type Conversation = {id: string; title: string};
type Message = {id: string; role: string; text: string};
type Job = {id: string; goal: string; kind: string; status: string; stage: string; partial: string; error: string; attempts: number; created: number};
type Detail = Job & {plan: string[]; events: {id: number; text: string; created: number}[]; sources: {position: number; url: string; title: string; error: string}[]; artifact: string | null; usage: {input_tokens: number | null; output_tokens: number | null; status: string; model: string} | null};
const terminal = (j: Job) => ['succeeded', 'failed', 'cancelled'].includes(j.status);

async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const res = await fetch('/api' + path, {method, credentials: 'include', headers: {'Content-Type': 'application/json', 'X-Friday-Request': '1'}, body: body === undefined ? undefined : JSON.stringify(body)});
  const data = await res.json();
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check the entered values.');
  return data as T;
}

function RichText({text}: {text: string}) {
  return <div className="markdown"><Markdown components={{a: ({href, children}) => <a href={href} target="_blank" rel="noreferrer noopener">{children}</a>, img: () => <span>[External image omitted]</span>}}>{text}</Markdown></div>;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [view, setView] = useState('home');
  const [chats, setChats] = useState<Conversation[]>([]);
  const [chatId, setChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatJobs, setChatJobs] = useState<Job[]>([]);
  const [projects, setProjects] = useState<Job[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [draft, setDraft] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [connected, setConnected] = useState(true);
  const [menu, setMenu] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [projectFilter, setProjectFilter] = useState('all');
  const [accent, setAccent] = useState(() => {try {return localStorage.getItem('friday-accent') || 'mint';} catch {return 'mint';}});
  const [motion, setMotion] = useState(() => {try {return localStorage.getItem('friday-motion') !== 'off';} catch {return true;}});
  useEffect(() => {document.documentElement.dataset.accent = accent; document.documentElement.dataset.motion = motion ? 'on' : 'off'; try {localStorage.setItem('friday-accent', accent); localStorage.setItem('friday-motion', motion ? 'on' : 'off');} catch { /* Preferences still work in memory. */ }}, [accent, motion]);
  useEffect(() => {const handler = (e: KeyboardEvent) => {if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {e.preventDefault(); setCommandOpen(v => !v);} if (e.key === 'Escape') {setCommandOpen(false); setMenu(false);}}; window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);}, []);

  useEffect(() => { api<User>('/me').then(setUser).catch(() => {}).finally(() => setLoading(false)); }, []);
  useEffect(() => {
    if (!user) return;
    let alive = true;
    const refresh = async () => {
      try {
        const [cs, ps, st] = await Promise.all([api<Conversation[]>('/conversations'), api<Job[]>('/projects'), api<Status>('/status')]);
        if (alive) {setChats(cs); setProjects(ps); setStatus(st); setConnected(true);}
      } catch { if (alive) setConnected(false); }
    };
    void refresh(); const timer = window.setInterval(refresh, 3000);
    return () => { alive = false; clearInterval(timer); };
  }, [user]);
  useEffect(() => {
    if (!chatId || !user) {setMessages([]); setChatJobs([]); return;}
    let alive = true;
    setMessages([]); setChatJobs([]);
    const refresh = async () => {
      try {
        const c = await api<{messages: Message[]; jobs: Job[]}>(`/conversations/${chatId}`);
        if (alive) { setMessages(c.messages); setChatJobs(c.jobs); }
      } catch (e) {if (alive) setError((e as Error).message);}
    };
    void refresh(); const timer = window.setInterval(refresh, 1000);
    return () => {alive = false; clearInterval(timer);};
  }, [chatId, user]);
  useEffect(() => {
    if (!projectId || !user) {setDetail(null); return;}
    let alive = true; setDetail(null);
    const refresh = async () => {
      try {const d = await api<Detail>(`/jobs/${projectId}`); if (alive) setDetail(d);}
      catch (e) {if (alive) setError((e as Error).message);}
    };
    void refresh(); const timer = window.setInterval(refresh, 1500);
    return () => {alive = false; clearInterval(timer);};
  }, [projectId, user]);

  async function act(fn: () => Promise<void>) {
    setBusy(true); setError('');
    try {await fn();} catch (e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function send(e?: React.FormEvent, retryText?: string) {
    e?.preventDefault(); const text = retryText || draft; if (!text.trim()) return;
    await act(async () => {
      let id = chatId;
      if (!id) {const c = await api<Conversation>('/conversations', 'POST', {}); id = c.id; setChatId(id);}
      const j = await api<Job>(`/conversations/${id}/messages`, 'POST', {text, request_key: crypto.randomUUID()});
      setChatJobs([j]); setDraft('');
      const c = await api<{messages: Message[]; jobs: Job[]}>(`/conversations/${id}`); setMessages(c.messages); setChatJobs(c.jobs);
      setUser(await api<User>('/me'));
    });
  }
  async function research(e?: React.FormEvent, retryText?: string) {
    e?.preventDefault(); const text = retryText || query; if (!text.trim()) return;
    await act(async () => {
      const j = await api<Job>('/projects', 'POST', {text, request_key: crypto.randomUUID()});
      setProjectId(j.id); setQuery(''); setProjects(p => [j, ...p]); setUser(await api<User>('/me'));
    });
  }
  const activeChat = chatJobs.find(j => !terminal(j));
  const latestChat = chatJobs[0];
  const changeView = (v: string) => {setView(v); setError(''); setMenu(false);};
  const commands: Command[] = [
    {label:'Command center', description:'Your private operations console', icon:'◈', run:() => changeView('home')},
    {label:'New conversation', description:'Start a fresh thread', icon:'＋', run:() => {setChatId(null); setDraft(''); changeView('chat');}},
    {label:'Research projects', description:'Follow evidence and background activity', icon:'◎', run:() => changeView('projects')},
    {label:'Appearance & settings', description:'Accent, motion, account and service setup', icon:'⚙', run:() => changeView('settings')},
    {label:'Capabilities', description:'See what is implemented and planned', icon:'◇', run:() => changeView('skills')},
    {label:focusMode ? 'Leave focus mode' : 'Enter focus mode', description:'Toggle the desktop sidebar', icon:'◫', run:() => setFocusMode(v => !v)},
    ...chats.map(c => ({label:c.title, description:'Saved conversation', icon:'◌', run:() => {setChatId(c.id); changeView('chat');}})),
  ];
  const filteredProjects = projects.filter(p => projectFilter === 'all' || (projectFilter === 'active' ? !terminal(p) : p.status === projectFilter));
  const errorBanner = error && <div className="notice error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>;

  if (loading) return <div className="loading">Opening FRIDAY…</div>;
  if (!user) return <AccessGate onLogin={() => {void api<User>('/me').then(setUser);}}/>;

  return <div className={"app-shell " + (focusMode ? "focus-mode" : "")}>{commandOpen && <CommandPalette commands={commands} onClose={() => setCommandOpen(false)}/>}<aside className={menu ? 'sidebar open' : 'sidebar'}><div className="brand"><span className="logo">F</span> FRIDAY <span className="version">01</span></div><button className="new-chat" onClick={() => {setChatId(null); setDraft(''); changeView('chat');}}>＋ New conversation</button><button className="quick-command" onClick={() => setCommandOpen(true)}><span>⌕ Quick commands</span><kbd>Ctrl K</kbd></button><nav>{[['home','◈','Command center'],['chat','◌','Conversations'],['projects','▦','Research projects'],['skills','◇','Capabilities'],['settings','⚙','Settings']].map(([id, icon, label]) => <button key={id} className={view === id ? 'nav active' : 'nav'} onClick={() => changeView(id)}><span>{icon}</span>{label}{id === 'projects' && projects.filter(p => !terminal(p)).length > 0 && <b>{projects.filter(p => !terminal(p)).length}</b>}</button>)}</nav><div className="history"><p className="eyebrow">YOUR CONVERSATIONS</p><input className="search" aria-label="Search conversations" placeholder="Search conversations…" value={filter} onChange={e => setFilter(e.target.value)}/>{chats.filter(c => c.title.toLowerCase().includes(filter.toLowerCase())).map(c => <button className={chatId === c.id && view === 'chat' ? 'history-item selected' : 'history-item'} key={c.id} onClick={() => {setChatId(c.id); changeView('chat');}}>{c.title}</button>)}{!chats.length && <p className="small muted">Your conversations will appear here.</p>}</div><div className="profile"><span className="avatar">A</span><div><strong>{user.is_owner ? 'Owner · Adithya' : 'Team member'}</strong><small>{user.email}</small></div></div></aside><div className="workspace"><header><div><button className="mobile-menu" aria-label="Toggle navigation" onClick={() => setMenu(!menu)}>☰</button><strong>{view === 'home' ? 'FRIDAY / Command' : view === 'chat' ? 'Conversation' : view === 'projects' ? 'Research workspace' : view === 'skills' ? 'What FRIDAY can do' : 'Your settings'}</strong><span className="header-sep">/</span><span className="muted">{user.is_owner ? 'Owner access' : 'Team access'}</span></div><div className="header-tools"><button className="focus-button" aria-pressed={focusMode} onClick={() => setFocusMode(v => !v)}>{focusMode ? "Show sidebar" : "Focus mode"}</button><button className="command-trigger" onClick={() => setCommandOpen(true)} aria-label="Open quick commands">⌕ <kbd>Ctrl K</kbd></button><span className="connection"><i className={connected ? '' : 'offline'}/>{connected ? 'Connected' : 'Reconnecting'}</span></div></header>{errorBanner}<main className={'main ' + view}>
    {view === 'home' && <Cinematic onChat={() => {setChatId(null); changeView('chat');}} onResearch={() => changeView('projects')} onSettings={() => changeView('settings')} onProject={id => {setProjectId(id); changeView('projects');}} projects={projects} conversations={chats.length} configured={!!status?.chat_configured} motion={motion}/>}
    {view === 'chat' && <><div className="conversation-scroll">{!messages.length && !activeChat ? <div className="welcome"><AmbientCore active={projects.some(p => !terminal(p))}/><div className="workspace-pill"><i/>{status?.chat_configured ? "YOUR WORKSPACE IS READY" : "YOUR WORKSPACE · MODEL SETUP NEEDED"}</div><p className="eyebrow">YOUR PERSONAL INTELLIGENCE SPACE</p><h1>What’s on your mind?</h1><p className="muted">A thought, a plan, a question worth exploring.<br/>Let’s give it somewhere to go.</p><div className="live-summary"><button onClick={() => setCommandOpen(true)}><strong>{chats.length}</strong> saved conversations</button><button onClick={() => changeView("projects")}><strong>{projects.filter(p => !terminal(p)).length}</strong> active projects</button></div><div className="suggestions"><button onClick={() => setDraft('Help me turn my idea into a practical plan.')}><span>↗</span><strong>Shape an idea</strong><small>Find a useful next step</small></button><button onClick={() => {setQuery('Compare the benefits and limitations of '); changeView('projects');}}><span>◎</span><strong>Explore a question</strong><small>Research with real sources</small></button><button onClick={() => setDraft('Help me write a clear first draft. Ask what I want to communicate.')}><span>✎</span><strong>Start a draft</strong><small>Give your thoughts a form</small></button></div></div> : <div className="messages">{messages.map(m => <article className={'message ' + m.role} key={m.id}><div className="message-label">{m.role === 'user' ? 'YOU' : 'FRIDAY'}</div><RichText text={m.text}/><CopyMessage text={m.text}/></article>)}{activeChat && <article className="message assistant"><div className="message-label">FRIDAY · {activeChat.status === 'queued' ? 'WAITING FOR WORKER' : 'RESPONDING'}</div>{activeChat.partial ? <RichText text={activeChat.partial}/> : <p className="muted">{activeChat.stage === 'plan' ? 'Request saved. Waiting for the worker…' : 'Working on your response…'}</p>}</article>}{latestChat && ['failed','cancelled'].includes(latestChat.status) && <div className="notice"><strong>{latestChat.status === 'failed' ? 'Response could not be completed' : 'Response stopped'}</strong><p>{latestChat.error || 'A request already sent to the provider may still incur usage.'}</p><button disabled={busy || !!activeChat} onClick={() => void send(undefined, latestChat.goal)}>Try again as a new request</button></div>}</div>}</div><div className="composer-area">{status && !status.chat_configured && <div className="setup-inline">◈ Model connection needed. <button onClick={() => changeView('settings')}>View setup</button></div>}<div className="prompt-chips"><span>Try a starting point</span>{["Plan my day", "Explain a concept", "Brainstorm ideas"].map(prompt => <button key={prompt} onClick={() => setDraft(prompt + ". Ask me a question to get started.")}>{prompt}</button>)}</div><form className="composer" onSubmit={send}><textarea aria-label="Message FRIDAY" placeholder="Message FRIDAY…" value={draft} onChange={e => setDraft(e.target.value)} maxLength={8000} rows={3} onKeyDown={e => {if (e.key === 'Enter' && !e.shiftKey) {e.preventDefault(); if (!busy && !activeChat) void send();}}}/><div className="composer-bottom"><span><i className={status?.chat_configured ? 'model-dot ready' : 'model-dot'}/>{status?.chat_configured ? status.model : 'Connect a model'} <b className="draft-count">{draft.length}/8000</b></span>{activeChat ? <button type="button" className="send" onClick={() => void act(async () => {await api(`/jobs/${activeChat.id}/cancel`, 'POST');})}>■ Stop</button> : <button className="send" disabled={busy || !draft.trim()}>Send ↑</button>}</div></form><p className="composer-note">FRIDAY can make mistakes. Review important information. Long-term memory is not yet enabled.</p></div></>}
    {view === 'projects' && <div className="projects-layout"><section className="project-list"><p className="eyebrow">FROM QUESTION TO EVIDENCE</p><h1>Research, in motion.</h1><p className="muted">Start a bounded research task. Return to sources, progress, and a saved report.</p><form onSubmit={research}><label>What would you like to understand?<textarea rows={4} maxLength={2000} value={query} onChange={e => setQuery(e.target.value)} placeholder="Enter a question, scope, and what the report should focus on…" required/></label><button className="primary" disabled={busy || !query.trim()}>Start research ↗</button></form><p className="small muted">Up to 5 pages · Source-linked report · Runs on the server</p><div className="project-filters" role="group" aria-label="Filter projects">{[["all","All"],["active","Active"],["succeeded","Complete"],["failed","Failed"]].map(([id,label]) => <button key={id} aria-pressed={projectFilter === id} onClick={() => setProjectFilter(id)}>{label}</button>)}</div><div className="project-cards">{filteredProjects.length === 0 && <p className="filter-empty">{projects.length ? "No projects in this view." : "Your first research project starts above."}</p>}{filteredProjects.map(p => <button key={p.id} className={'project-card ' + (projectId === p.id ? 'selected' : '')} onClick={() => setProjectId(p.id)}><span className={'badge ' + p.status}>{p.status}</span><strong>{p.goal}</strong><small>{new Date(p.created * 1000).toLocaleString()}</small></button>)}</div></section><section className="project-detail">{!detail ? <div className="empty"><span>◎</span><h2>A place for the whole picture.</h2><p className="muted">Choose a project to see its evidence,<br/>activity, and results.</p></div> : <><div className="detail-top"><span className={'badge ' + detail.status}>{detail.status}</span>{!terminal(detail) && <button onClick={() => void act(async () => {await api(`/jobs/${detail.id}/cancel`, 'POST');})}>Cancel project</button>}</div><h2>{detail.goal}</h2>{detail.error && <div className="notice error">{detail.error}</div>}<h3>Research plan</h3><ol className="plan">{detail.plan.length ? detail.plan.map(x => <li key={x}>{x}</li>) : <li>Waiting for the worker to save the plan.</li>}</ol><h3>Activity</h3><ul className="timeline">{detail.events.map(e => <li key={e.id}><time>{new Date(e.created * 1000).toLocaleTimeString()}</time><span>{e.text}</span></li>)}</ul>{detail.sources.length > 0 && <><h3>Sources inspected</h3><div className="sources">{detail.sources.map(s => <div key={s.position}><b>[{s.position}]</b><div>{s.url.startsWith('https://') ? <a href={s.url} target="_blank" rel="noreferrer noopener">{s.title}</a> : s.title}<small>{s.error || 'Page text retrieved'}</small></div></div>)}</div></>}{detail.artifact && <><div className="report-heading"><h3>Your report</h3><a className="button" href={`/api/jobs/${detail.id}/report`}>Download .md ↓</a></div><div className="report"><RichText text={detail.artifact}/></div></>}{detail.usage && <p className="small muted">Model: {detail.usage.model} · Usage: {detail.usage.status} · Input tokens {detail.usage.input_tokens ?? 'unknown'} · Output tokens {detail.usage.output_tokens ?? 'unknown'}</p>}{detail.status === 'failed' && <button disabled={busy} onClick={() => void research(undefined, detail.goal)}>Retry as a new project</button>}</>}</section></div>}
    {view === 'skills' && <section className="content-page"><p className="eyebrow">BUILT IN STAGES. LABELED HONESTLY.</p><h1>A growing set of abilities.</h1><p className="muted">This first milestone focuses on conversations and source-based research.<br/>Future capabilities are listed here as planned, not working tools.</p><div className="capability-grid">{[['Persistent conversations','Implemented','Accounts, saved history, bounded context, and a replaceable model adapter. Live AI requires credentials.'],['Background research','Implemented','Durable jobs, public-page retrieval, activity logs, cancellation, and cited Markdown reports. Live services require credentials.'],['Voice & personal memory','Planned','Push-to-talk, speech playback, and memories you can inspect, edit, and delete.'],['Computer use & coding','Planned','Isolated browser and coding workers, scoped permissions, diffs, and test results.'],['Business & creative skills','Planned','Document tools, marketing, sales, operations, support, and service integrations.'],['Mobile & physical devices','Planned','Shared backend for Android, iOS, glasses, a watch, and constrained robot connections.']].map(([title, state, desc]) => <article className="capability" key={title}><span className={'badge ' + (state === 'Implemented' ? 'succeeded' : '')}>{state}</span><h2>{title}</h2><p className="muted">{desc}</p></article>)}</div><div className="notice">Approvals for sending, purchasing, and booking will be introduced with those tools. This milestone has no such action tools.</div></section>}
    {view === 'settings' && <section className="content-page settings-page"><p className="eyebrow">YOUR WORKSPACE, UNDER YOUR CONTROL</p><h1>Settings</h1>{user.is_owner && <AccessControl/>}<Appearance accent={accent} setAccent={setAccent} motion={motion} setMotion={setMotion}/><article className="settings-card"><h2>Profile</h2><p>{user.email}</p><p className="small muted">FRIDAY account · Email ownership is not yet verified · Google sign-in is not connected</p><button onClick={() => void act(async () => {await api('/auth/logout', 'POST'); setUser(null); setChatId(null); setProjectId(null); setChats([]); setMessages([]); setProjects([]); setStatus(null);})}>Sign out</button></article><article className="settings-card"><h2>Model & research services</h2><p>Provider: <strong>{status?.provider}</strong> · Model: <strong>{status?.model}</strong></p><p className="muted">Provider access is infrastructure. FRIDAY does not own the third-party model or claim equivalent performance to another AI product.</p>{status?.missing.length ? <div className="notice">Set these variables in the server’s <code>.env</code> file and restart the API and workers: <strong>{status.missing.join(', ')}</strong>. Never enter API keys in chat.</div> : <div className="notice">Credentials are configured. This does not confirm provider access or model quality; run a live conversation and research task.</div>}</article><article className="settings-card"><h2>Usage & execution</h2><p><strong>{user.jobs_today} / {user.daily_job_limit}</strong> jobs submitted today (UTC quota day).</p><p className="muted">Limits are enforced on the server. Each job makes at most one model call, with a bounded output. These are application limits, not an exact provider spending cap.</p><p className="small muted">The server and worker must stay running. Cloud hosting is not yet deployed; local jobs pause while this computer is off.</p></article><article className="settings-card"><h2>Privacy & memory</h2><p className="muted">Conversation history and project evidence are saved in the FRIDAY database. Chat context is bounded to the most recent 20 messages and 30,000 characters. Long-term memory, account export/deletion, and session management are later milestones.</p></article></section>}
  </main></div></div>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
