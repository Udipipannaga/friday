import { useEffect, useRef, useState } from 'react';

export type Command = {label: string; description: string; icon: string; run: () => void};

export function CommandPalette({commands, onClose}: {commands: Command[]; onClose: () => void}) {
  const [search, setSearch] = useState('');
  const [index, setIndex] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const filtered = commands.filter(c => `${c.label} ${c.description}`.toLowerCase().includes(search.toLowerCase()));
  useEffect(() => {const previous = document.activeElement as HTMLElement; return () => previous?.focus();}, []);
  return <div className="command-backdrop" onClick={onClose}><div className="command-dialog" ref={ref} role="dialog" aria-modal="true" aria-label="Quick commands" onClick={e => e.stopPropagation()} onKeyDown={e => {
    if (e.key === 'Escape') onClose();
    if (e.key === 'ArrowDown') {e.preventDefault(); setIndex(i => Math.min(i + 1, filtered.length - 1));}
    if (e.key === 'ArrowUp') {e.preventDefault(); setIndex(i => Math.max(i - 1, 0));}
    if (e.key === 'Enter' && filtered[index]) {e.preventDefault(); filtered[index].run(); onClose();}
    if (e.key === 'Tab') {const elements = ref.current?.querySelectorAll<HTMLElement>('input,button'); if (!elements?.length) return; const first = elements[0], last = elements[elements.length - 1]; if (e.shiftKey && document.activeElement === first) {e.preventDefault(); last.focus();} else if (!e.shiftKey && document.activeElement === last) {e.preventDefault(); first.focus();}}
  }}><div className="command-input"><span>⌕</span><input autoFocus aria-label="Search commands" placeholder="Where would you like to go?" value={search} onChange={e => {setSearch(e.target.value); setIndex(0);}}/><button onClick={onClose} aria-label="Close commands">Esc</button></div><div className="command-results">{filtered.map((c, i) => <button key={c.label} className={i === index ? 'command selected' : 'command'} onClick={() => {c.run(); onClose();}}><span>{c.icon}</span><div><strong>{c.label}</strong><small>{c.description}</small></div><span>↗</span></button>)}{!filtered.length && <p className="muted">No matching commands or conversations.</p>}</div><footer>↑ ↓ Navigate <span>Enter to open</span></footer></div></div>;
}

export function AmbientCore({active}: {active: boolean}) {
  const [paused, setPaused] = useState(false);
  return <button className={'ambient-core ' + (paused ? 'paused' : '') + (active ? ' working' : '')} aria-label={paused ? 'Resume visual animation' : 'Pause visual animation'} aria-pressed={paused} onClick={() => setPaused(!paused)} title="Toggle decorative animation"><span className="orbit orbit-one"/><span className="orbit orbit-two"/><span className="core-art"/><span className="core-pin"/><span className="core-caption">{paused ? 'VISUAL PAUSED' : 'F R I D A Y'}</span></button>;
}

export function CopyMessage({text}: {text: string}) {
  const [result, setResult] = useState('Copy');
  useEffect(() => {if (result === 'Copy') return; const timer = setTimeout(() => setResult('Copy'), 2500); return () => clearTimeout(timer);}, [result]);
  return <button className="message-copy" onClick={async () => {try {await navigator.clipboard.writeText(text); setResult('Copied ✓');} catch {setResult('Copy unavailable');}}}>{result}</button>;
}

export function Appearance({accent, setAccent, motion, setMotion}: {accent: string; setAccent: (v: string) => void; motion: boolean; setMotion: (v: boolean) => void}) {
  return <article className="settings-card"><h2>Make FRIDAY feel like you</h2><p className="muted">Choose your workspace accent and decorative motion. These preferences stay on this browser.</p><div className="accent-options" role="group" aria-label="Accent color">{[['mint','Glacier'],['violet','Nebula'],['amber','Solar']].map(([id,name]) => <button key={id} className={'accent-option ' + id} aria-pressed={accent === id} onClick={() => setAccent(id)}><i/>{name}{accent === id && ' ✓'}</button>)}</div><button className="motion-toggle" role="switch" aria-checked={motion} onClick={() => setMotion(!motion)}>Decorative motion <strong>{motion ? 'On' : 'Off'}</strong></button><p className="small muted">Your device’s reduced-motion preference is always respected.</p></article>;
}
