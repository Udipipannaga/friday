import { useState, type CSSProperties } from 'react';
import { rolloutDepartments, rolloutStages, type WorkMode, type RolloutStage } from './rolloutCatalog';
import './rollout-map.css';

const modes: {id: WorkMode; label: string; explanation: string}[] = [
  {id: 'human-led', label: 'Human-led', explanation: 'A person makes and carries out the decision.'},
  {id: 'assisted', label: 'Human-assisted', explanation: 'FRIDAY may prepare a draft; a person reviews the action.'},
  {id: 'autonomous', label: 'Autonomous target', explanation: 'Unattended execution is a future goal, subject to tools, approvals and testing.'},
];

const stageLabel = (stage: RolloutStage) => stage === 'ongoing' ? 'Ongoing' : `${stage} · ${rolloutStages[stage].name}`;

export function RolloutMap({onResearch}: {onResearch: () => void}) {
  const [selectedId, setSelectedId] = useState('sales');
  const [modeFilter, setModeFilter] = useState<WorkMode | 'all'>('all');
  const [stageFilter, setStageFilter] = useState<RolloutStage | 'all'>('all');
  const [search, setSearch] = useState('');
  const selected = rolloutDepartments.find(department => department.id === selectedId) ?? rolloutDepartments[0];
  const total = rolloutDepartments.reduce((sum, department) => sum + department.jobs.length, 0);
  const matches = selected.jobs.filter(job =>
    (modeFilter === 'all' || job.mode === modeFilter) &&
    (stageFilter === 'all' || job.stage === stageFilter) &&
    job.name.toLowerCase().includes(search.trim().toLowerCase())
  );
  const counts = Object.fromEntries(modes.map(mode => [mode.id, selected.jobs.filter(job => job.mode === mode.id).length])) as Record<WorkMode, number>;

  return <div className="rollout" aria-labelledby="rollout-title">
    <div className="rollout-header"><div><p className="eyebrow">TEAM OPERATING MODEL / REFERENCE CATALOG</p><h2 id="rollout-title">The work behind the system.</h2><p>Explore the departments and rollout stages you named. These are proposed jobs and responsibility levels, not running FRIDAY agents.</p></div><strong>{total}<small>jobs catalogued</small></strong></div>
    <div className="rollout-phases" aria-label="Rollout order">{([1, 2, 3, 4] as const).map(stage => <div key={stage}><b>{stage}</b><span><strong>{rolloutStages[stage].name}</strong><small>{rolloutStages[stage].description}</small></span></div>)}</div>
    <div className="rollout-constellation" aria-label="Departments">
      <svg viewBox="0 0 1000 400" preserveAspectRatio="none" aria-hidden="true">{rolloutDepartments.map((department, index) => {
        const theta = (-150 + index * 50) * Math.PI / 180;
        const x = 500 + Math.cos(theta) * 360;
        const y = 205 + Math.sin(theta) * 145;
        return <line key={department.id} x1="500" y1="205" x2={x} y2={y}/>;
      })}</svg>
      <div className="rollout-core" aria-hidden="true"><span>F</span><strong>FRIDAY</strong><small>YOUR TEAM</small></div>
      {rolloutDepartments.map((department, index) => {
        const theta = (-150 + index * 50) * Math.PI / 180;
        const style = {'--rollout-x': `${50 + Math.cos(theta) * 36}%`, '--rollout-y': `${51.25 + Math.sin(theta) * 36.25}%`, '--rollout-accent': department.accent} as CSSProperties;
        return <button key={department.id} type="button" className={'rollout-node ' + (selected.id === department.id ? 'selected' : '')} style={style} aria-pressed={selected.id === department.id} onClick={() => {setSelectedId(department.id); setSearch(''); setModeFilter('all'); setStageFilter('all');}}><span className="rollout-node-index">{String(index + 1).padStart(2, '0')}</span><strong>{department.name}</strong><small>{department.jobs.length} named jobs</small></button>;
      })}
    </div>
    <section className="rollout-detail" style={{'--rollout-accent': selected.accent} as CSSProperties} aria-labelledby="rollout-department-title">
      <div className="rollout-department-heading"><div><p className="eyebrow">DEPARTMENT / {String(rolloutDepartments.indexOf(selected) + 1).padStart(2, '0')}</p><h3 id="rollout-department-title">{selected.name}</h3><p>{selected.summary}</p></div><span>{selected.jobs.length} catalogued jobs</span></div>
      <div className="rollout-target-note" role="note"><strong>Target allocation, not live capability.</strong> Even jobs labelled “autonomous” below are not connected to FRIDAY actions. Sending, publishing, bookings, payments and external changes require a working integration and an exact approval flow before activation.</div>
      <div className="rollout-counts">{modes.map(mode => <div key={mode.id}><span>{counts[mode.id]}</span><strong>{mode.label}</strong><small>{mode.explanation}</small></div>)}</div>
      <div className="rollout-controls"><label>Find a job<input type="search" value={search} placeholder={`Search ${selected.name.toLowerCase()}…`} onChange={event => setSearch(event.target.value)}/></label><label>Rollout stage<select value={stageFilter} onChange={event => setStageFilter(event.target.value === 'all' ? 'all' : event.target.value === 'ongoing' ? 'ongoing' : Number(event.target.value) as RolloutStage)}><option value="all">All stages</option><option value="ongoing">Ongoing</option>{([1, 2, 3, 4] as const).map(stage => <option key={stage} value={stage}>{stageLabel(stage)}</option>)}</select></label></div>
      <div className="rollout-mode-filters" role="group" aria-label="Filter target responsibility">{[{id: 'all', label: 'All jobs'}, ...modes.map(mode => ({id: mode.id, label: mode.label}))].map(option => <button key={option.id} type="button" aria-pressed={modeFilter === option.id} onClick={() => setModeFilter(option.id as WorkMode | 'all')}>{option.label}</button>)}</div>
      <div className="rollout-groups">{modes.map(mode => {
        const jobs = matches.filter(job => job.mode === mode.id);
        if (!jobs.length) return null;
        return <section key={mode.id} className={'rollout-group mode-' + mode.id}><div><h4>{mode.label}</h4><span>{jobs.length} shown</span></div><ul>{jobs.map(job => <li key={`${mode.id}-${job.name}`}><span>{job.name}</span><small>{stageLabel(job.stage)}</small><em>Planned in FRIDAY</em></li>)}</ul></section>;
      })}{matches.length === 0 && <p className="rollout-empty">No named jobs match these filters.</p>}</div>
      {selected.id === 'intelligence' && <div className="rollout-real-path"><p><strong>Working foundation:</strong> FRIDAY has a durable research project workflow. Its live model and search services still need configuration and an end-to-end run.</p><button type="button" onClick={onResearch}>Open research projects ↗</button></div>}
    </section>
    <p className="rollout-source-note">Counts come from the job names supplied for this catalog. The pasted headline totals conflict with or omit some names, so they are not used as completion metrics.</p>
  </div>;
}
