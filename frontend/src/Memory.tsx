import React, { useEffect, useState } from 'react';
import './memory.css';

type MemoryItem = {id: string; label: string; content: string; origin: string; created: number; updated: number};

async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api' + path, {method, credentials: 'include',
    headers: {'Content-Type': 'application/json', 'X-Friday-Request': '1'},
    body: body === undefined ? undefined : JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Memory request failed.');
  return result as T;
}

export function MemoryPage() {
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [label, setLabel] = useState('');
  const [content, setContent] = useState('');
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {setItems(await request<MemoryItem[]>('/memories')); setError('');}
    catch (cause) {setError((cause as Error).message);}
    finally {setLoading(false);}
  };
  useEffect(() => {void refresh();}, []);

  const clear = () => {setEditing(null); setLabel(''); setContent('');};
  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!label.trim() || !content.trim() || busy) return;
    setBusy(true); setError('');
    try {
      await request(editing ? `/memories/${editing}/update` : '/memories', 'POST', {label, content});
      clear(); await refresh();
    } catch (cause) {setError((cause as Error).message);}
    finally {setBusy(false);}
  };
  const remove = async (item: MemoryItem) => {
    if (!window.confirm(`Delete “${item.label}” from FRIDAY memory? Future chats will not receive it.`)) return;
    setBusy(true); setError('');
    try {await request(`/memories/${item.id}/delete`, 'POST'); if (editing === item.id) clear(); await refresh();}
    catch (cause) {setError((cause as Error).message);}
    finally {setBusy(false);}
  };

  return <section className="memory-page content-page">
    <p className="eyebrow">FRIDAY / PERSONAL MEMORY</p>
    <h1>What should FRIDAY remember?</h1>
    <p className="muted">Only items you save here are added to later chats. You can change or remove them at any time. Conversation history and company records stay separate.</p>
    <div className="memory-status"><span>{items.length} / 50 saved</span><a href="/api/memories/export" download="friday-memories.json">Export JSON ↓</a></div>
    {error && <div className="notice error" role="alert">{error}</div>}
    <form className="memory-form" onSubmit={save}>
      <h2>{editing ? 'Edit memory' : 'Save a memory'}</h2>
      <label>Label<input value={label} onChange={e => setLabel(e.target.value)} maxLength={80} placeholder="Example: How I like project updates" required/></label>
      <label>What to remember<textarea value={content} onChange={e => setContent(e.target.value)} maxLength={500} rows={3} placeholder="Write a fact or preference you want available in later chats." required/></label>
      <p className="small muted">Do not save passwords, API keys, card numbers or bank details. Memory may be outdated; check important facts.</p>
      <div className="memory-actions"><button className="primary" disabled={busy || !label.trim() || !content.trim()}>{editing ? 'Save changes' : 'Remember this'}</button>{editing && <button type="button" onClick={clear}>Cancel edit</button>}</div>
    </form>
    <div className="memory-list" aria-live="polite">
      {loading && <p className="muted">Loading your memories…</p>}
      {!loading && items.length === 0 && <p className="muted">Nothing saved yet. FRIDAY uses your conversation history until you add an explicit memory.</p>}
      {items.map(item => <article className="memory-card" key={item.id}>
        <div><strong>{item.label}</strong><p>{item.content}</p><small>Saved by you · Updated {new Date(item.updated * 1000).toLocaleString()}</small></div>
        <div className="memory-actions"><button disabled={busy} onClick={() => {setEditing(item.id); setLabel(item.label); setContent(item.content);}}>Edit</button><button disabled={busy} onClick={() => void remove(item)}>Delete</button></div>
      </article>)}
    </div>
    <p className="small muted">Deletion removes an item from future chat retrieval. A reply already in progress may have received it. Existing conversation messages and database backups are separate records.</p>
  </section>;
}

