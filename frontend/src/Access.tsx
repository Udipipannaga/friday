import {useEffect, useState} from 'react';
import {FridayFiberLogo} from './FridayFiberLogo';

async function call(path: string, body?: unknown) {
  const response = await fetch('/api' + path, {
    method: body ? 'POST' : 'GET',
    credentials: 'include',
    headers: {'Content-Type': 'application/json', 'X-Friday-Request': '1'},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Check your entries.');
  return data;
}

export function AccessGate({onLogin}: {onLogin: () => void}) {
  const [token] = useState(() => new URLSearchParams(location.hash.slice(1)).get('invite') || '');
  const [mode, setMode] = useState(token ? 'invite' : 'login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {if (token) history.replaceState(null, '', location.pathname + location.search);}, [token]);

  return <div className="access-gate">
    <div className="gate-identity"><p className="eyebrow">PRIVATE INTELLIGENCE SYSTEM / F-01</p><FridayFiberLogo size={180} className="gate-fiber-logo"/><h1>FRIDAY</h1><p>One command center.<br/>Access by invitation.</p></div>
    <section className="gate-form"><p className="eyebrow">IDENTITY CHECKPOINT</p><h2>{mode === 'request' ? 'Request clearance' : mode === 'invite' ? 'Activate your access' : 'Welcome back'}</h2><p className="muted">{mode === 'request' ? 'Leave your email for the owner to review.' : mode === 'invite' ? 'Use the invited email and choose your own password.' : 'Owner and approved team members only.'}</p>
      <form onSubmit={async event => {
        event.preventDefault(); setBusy(true); setMessage('');
        try {
          if (mode === 'request') {
            const result = await call('/access/request', {email});
            setMessage(result.message);
          } else {
            await call(mode === 'invite' ? '/access/accept' : '/auth/login', {email, password, ...(mode === 'invite' ? {token} : {})});
            onLogin();
          }
        } catch (error) {setMessage((error as Error).message);}
        finally {setBusy(false);}
      }}>
        <label>Email<input type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)}/></label>
        {mode !== 'request' && <label>Password<input type="password" autoComplete={mode === 'invite' ? 'new-password' : 'current-password'} minLength={12} maxLength={128} required value={password} onChange={event => setPassword(event.target.value)}/></label>}
        <button className="primary full" disabled={busy}>{busy ? 'Processing…' : mode === 'request' ? 'Submit access request' : mode === 'invite' ? 'Activate access' : 'Enter command center'}</button>
      </form>
      <p role="status">{message}</p>
      {mode !== 'invite' && <button className="text-button" onClick={() => {setMode(mode === 'login' ? 'request' : 'login'); setMessage('');}}>{mode === 'login' ? 'Need access? Request approval' : 'Already approved? Sign in'}</button>}
      <p className="small muted">Owner sessions stay signed in for up to 90 days on this browser. Signing out or clearing cookies requires signing in again.</p>
    </section>
  </div>;
}

type Entry = {id: string; email: string; status: string; created: number};

export function AccessControl({onPendingCount}: {onPendingCount?: (count: number) => void}) {
  const [rows, setRows] = useState<Entry[]>([]);
  const [message, setMessage] = useState('');
  const [invite, setInvite] = useState('');
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const result = await call('/access') as Entry[];
    setRows(result);
    onPendingCount?.(result.filter(row => row.status === 'pending').length);
  }

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const result = await call('/access') as Entry[];
        if (active) {
          setRows(result);
          onPendingCount?.(result.filter(row => row.status === 'pending').length);
        }
      } catch (error) {if (active) setMessage((error as Error).message);}
    };
    void load();
    const timer = window.setInterval(load, 15000);
    return () => {active = false; window.clearInterval(timer);};
  }, [onPendingCount]);

  const pending = rows.filter(row => row.status === 'pending');
  const reviewed = rows.filter(row => row.status !== 'pending');

  async function review(row: Entry, action: 'approve' | 'deny' | 'revoke') {
    setBusy(true); setMessage(''); setInvite('');
    try {
      const result = await call('/access/' + row.id + '/review', {action});
      if (result.invitation) setInvite(result.invitation);
      await refresh();
    } catch (error) {setMessage((error as Error).message);}
    finally {setBusy(false);}
  }

  function renderRow(row: Entry) {
    return <div className="access-row" key={row.id}>
      <div><strong>{row.email}</strong><p className="small">{row.status} · {new Date(row.created * 1000).toLocaleString()}</p></div>
      <div>
        {row.status === 'accepted'
          ? <button type="button" disabled={busy} onClick={() => void review(row, 'revoke')}>Revoke access</button>
          : <><button type="button" disabled={busy} onClick={() => void review(row, 'approve')}>{row.status === 'invited' ? 'Issue new link' : 'Approve / issue link'}</button>{['pending', 'invited'].includes(row.status) && <button type="button" disabled={busy} onClick={() => void review(row, 'deny')}>Deny</button>}</>}
      </div>
    </div>;
  }

  return <article className="settings-card">
    <p className="eyebrow">OWNER CONTROL</p><h2>Access requests</h2>
    <p className="muted">Review each email. Approval creates a single-use link valid for 48 hours; send it privately yourself. Emails are self-reported, so confirm the person before sharing access.</p>
    <button type="button" onClick={() => void refresh().catch(error => setMessage(error.message))}>Refresh requests</button>
    <p role="status">{message}</p>
    {invite && <div className="notice"><label>Invitation to send privately<input readOnly value={invite} onFocus={event => event.target.select()}/></label><button type="button" onClick={() => void navigator.clipboard.writeText(invite).then(() => setMessage('Invitation copied.')).catch(() => setMessage('Select and copy the link manually.'))}>Copy invitation</button><p>No email has been sent automatically.</p></div>}
    <h3>Pending · {pending.length}</h3>
    {pending.length ? pending.map(renderRow) : <p>No pending requests.</p>}
    {reviewed.length > 0 && <><h3>Earlier decisions</h3>{reviewed.map(renderRow)}</>}
  </article>;
}
