import { useState, type CSSProperties, type FormEvent } from 'react';
import './capability-map.css';
import { RolloutMap } from './RolloutMap';

type ServiceStatus = {
  chat_configured: boolean;
  research_configured: boolean;
  capabilities: Record<string, string>;
};

type Availability = 'active' | 'setup' | 'configured' | 'planned' | 'not-trained' | 'checking';
type Action = 'chat' | 'research' | 'settings';
type Capability = {
  id: string;
  title: string;
  summary: string;
  detail: string;
  phase: 'active' | 'service' | 'planned' | 'not-trained';
  key?: string;
  service?: 'chat' | 'research';
  action?: Action;
  actionLabel?: string;
  reference?: { label: string; url: string };
};
type Department = {
  id: string;
  title: string;
  description: string;
  symbol: string;
  color: string;
  x: number;
  y: number;
  capabilities: Capability[];
};

const departments: Department[] = [
  {
    id: 'dialogue', title: 'Dialogue', description: 'Conversation and thought', symbol: '◌', color: '#69e5e6', x: 500, y: 78,
    capabilities: [
      {id: 'saved-chat', title: 'Saved conversations', summary: 'History that survives a browser session.', detail: 'Conversation containers and messages live in FRIDAY’s database and can be reopened from the sidebar.', phase: 'active', key: 'persistent_chat', action: 'chat', actionLabel: 'Open conversations'},
      {id: 'model-replies', title: 'Model replies', summary: 'Responses through a replaceable provider.', detail: 'FRIDAY queues a chat request and saves its output. The selected provider needs service setup, and configuration alone does not prove that a live model call succeeds.', phase: 'service', key: 'persistent_chat', service: 'chat', action: 'chat', actionLabel: 'Open conversation'},
      {id: 'planning', title: 'Planning companion', summary: 'Turn a goal into the next steps.', detail: 'Planning is currently a use of the configured chat model, not a separate autonomous planner or task executor.', phase: 'service', key: 'persistent_chat', service: 'chat', action: 'chat', actionLabel: 'Start planning'},
    ],
  },
  {
    id: 'investigation', title: 'Investigation', description: 'Evidence and learning', symbol: '⌕', color: '#8dc7ff', x: 755, y: 155,
    capabilities: [
      {id: 'research', title: 'Background research', summary: 'A durable, source-based investigation.', detail: 'The worker searches, reads up to five public HTTPS pages, records activity, and saves a cited Markdown report. A configured model and search service are required to run a new project.', phase: 'service', key: 'research', service: 'research', action: 'research', actionLabel: 'Open research'},
      {id: 'evidence', title: 'Evidence & reports', summary: 'Sources, activity and saved output.', detail: 'Existing project records, inspected sources, activity events and reports can be reopened. New evidence requires the research services to be configured.', phase: 'active', key: 'research', action: 'research', actionLabel: 'View projects'},
      {id: 'physics-check', title: 'Lift / weight check', summary: 'A bounded, deterministic physics calculation.', detail: 'This checks the static lift equation against weight for supplied values. It is a calculator, not a trained physics model, flight simulator, or airworthiness verdict.', phase: 'active', key: 'physics_lift_checker'},
      {id: 'physics-library', title: 'Physics knowledge', summary: 'Search trusted open material before answering.', detail: 'A licensed physics library, source indexing, and retrieval are not installed. This is the proposed first step toward domain-grounded physics answers.', phase: 'planned'},
      {id: 'physics-training', title: 'Physics model training', summary: 'Worked problems and solver-graded evaluation.', detail: 'FRIDAY has no trained physics checkpoint. A future run needs licensed worked examples, a held-out test set, unit and numeric checks, and recorded results. A prompt or document upload is not training.', phase: 'not-trained'},
    ],
  },
  {
    id: 'engineering', title: 'Engineering', description: 'Code and controlled tools', symbol: '⌘', color: '#b9a1ff', x: 840, y: 345,
    capabilities: [
      {id: 'coding', title: 'Isolated coding workspace', summary: 'Scoped file access, diffs and tests.', detail: 'No isolated coding runtime, repository authorization flow, or reviewed patch workflow is active in FRIDAY.', phase: 'planned'},
      {id: 'computer-use', title: 'Browser & computer use', summary: 'Explicit permissions and observable actions.', detail: 'FRIDAY does not currently control a browser or computer. This will need isolated execution, approval boundaries, and an auditable activity record.', phase: 'planned', key: 'computer_use'},
    ],
  },
  {
    id: 'perception', title: 'Perception', description: 'Voice, camera and context', symbol: '◐', color: '#8ce9c3', x: 715, y: 520,
    capabilities: [
      {id: 'voice', title: 'Browser voice', summary: 'Speak and hear replies in supported browsers.', detail: 'Push-to-talk recognition sends the final transcript to saved chat. Browser speech synthesis reads completed replies. The browser may use its own speech service, and live AI answers still require a configured model. Microphone and spoken-output hardware have not been verified on every device.', phase: 'active', key: 'voice', action: 'chat', actionLabel: 'Open voice chat'},
      {id: 'jester', title: 'JESTER gesture reference', summary: 'Inspiration for a hands-on display.', detail: 'JESTER demonstrates camera hand tracking and a three-dimensional scene. FRIDAY does not yet use a camera or gesture control, and no JESTER code or assets were copied.', phase: 'planned', reference: {label: 'View JESTER repository', url: 'https://github.com/heeelol/jester'}},
      {id: 'visionclaw', title: 'VisionClaw reference', summary: 'Candidate for wearable vision input.', detail: 'The linked VisionClaw project is a reference to evaluate. FRIDAY has no camera stream, device pairing, or image-grounded response workflow yet.', phase: 'planned', reference: {label: 'View VisionClaw repository', url: 'https://github.com/sseanliu/VisionClaw'}},
    ],
  },
  {
    id: 'operations', title: 'Operations', description: 'Long-running work and oversight', symbol: '↗', color: '#f3ca82', x: 500, y: 570,
    capabilities: [
      {id: 'jobs', title: 'Durable project jobs', summary: 'Work continues away from the browser.', detail: 'Research jobs are stored in the database and executed by a worker. You can leave and return to inspect a job; a new run still needs configured services.', phase: 'active', key: 'research', action: 'research', actionLabel: 'View project queue'},
      {id: 'activity', title: 'Activity & cancellation', summary: 'Inspect progress and stop queued work.', detail: 'Research projects expose saved activity events, execution state, cancellation, and report output when a run succeeds.', phase: 'active', key: 'research', action: 'research', actionLabel: 'Inspect activity'},
      {id: 'approvals', title: 'Action approvals', summary: 'Review consequential steps first.', detail: 'There are no sending, purchasing or booking tools in this milestone. Approval gates for those future actions are not active.', phase: 'planned'},
    ],
  },
  {
    id: 'workflows', title: 'Workflows', description: 'Business and specialist skills', symbol: '◇', color: '#ffa67e', x: 285, y: 520,
    capabilities: [
      {id: 'business', title: 'Specialist skills', summary: 'Marketing, sales and operations.', detail: 'Specialist skill execution, domain-specific artifacts and service accounts are future stages. A capability listing is not an executable skill.', phase: 'planned', key: 'business_integrations'},
      {id: 'n8n', title: 'n8n automation', summary: 'Reviewable triggers and actions.', detail: 'No n8n instance or workflow is connected to this FRIDAY deployment. Any future automation should be scoped to an approved account and action.', phase: 'planned'},
      {id: 'integrations', title: 'Service integrations', summary: 'Connect the tools your team uses.', detail: 'FRIDAY has no connected email, calendar, CRM or advertising service. Access, usage and approval controls must precede service actions.', phase: 'planned', key: 'business_integrations'},
    ],
  },
  {
    id: 'stewardship', title: 'Stewardship', description: 'Identity, memory and limits', symbol: '▣', color: '#ff9daf', x: 160, y: 345,
    capabilities: [
      {id: 'access', title: 'Owner & team access', summary: 'Private accounts and controlled entry.', detail: 'The owner account and invitation-only access flow are built in. Owner controls are available in Settings.', phase: 'active', action: 'settings', actionLabel: 'Open access controls'},
      {id: 'limits', title: 'Usage limits', summary: 'Bounded job requests.', detail: 'The server counts submitted jobs against a daily quota. This is not a provider-level spending cap.', phase: 'active', action: 'settings', actionLabel: 'View usage'},
      {id: 'memory', title: 'User-controlled memory', summary: 'Inspect, correct and delete what is kept.', detail: 'FRIDAY saves conversation history, but does not have a separate long-term personal memory store or memory controls yet.', phase: 'planned', key: 'memory'},
    ],
  },
  {
    id: 'extensions', title: 'Extensions', description: 'Apps and physical devices', symbol: '◎', color: '#8dc2ed', x: 245, y: 155,
    capabilities: [
      {id: 'windows', title: 'Windows companion', summary: 'A local bridge to the desktop.', detail: 'The current web app opens on Windows. A native Windows companion and local computer permissions are not implemented.', phase: 'planned'},
      {id: 'mobile', title: 'Android & iOS apps', summary: 'FRIDAY beyond the browser.', detail: 'Native mobile apps and secure mobile sessions are planned. Today FRIDAY is a responsive web app.', phase: 'planned', key: 'mobile_apps'},
      {id: 'wearables', title: 'Glasses, watch & robot', summary: 'Future connected devices.', detail: 'No glasses, watch or robot device is paired. Future connections need device identity, constrained permissions and live validation.', phase: 'planned', key: 'device_pairing'},
    ],
  },
];

const labels: Record<Availability, string> = {
  active: 'Active', setup: 'Setup required', configured: 'Configured · verify', planned: 'In development', 'not-trained': 'Not trained', checking: 'Checking',
};

function availability(item: Capability, status: ServiceStatus | null, connected: boolean): Availability {
  if (item.phase === 'planned') return 'planned';
  if (item.phase === 'not-trained') return 'not-trained';
  if (!connected || !status) return 'checking';
  if (item.key && !status.capabilities?.[item.key]?.startsWith('implemented')) return 'planned';
  if (item.phase === 'active') return 'active';
  return status[item.service === 'research' ? 'research_configured' : 'chat_configured'] ? 'configured' : 'setup';
}

function departmentStyle(department: Department): CSSProperties {
  return {'--sector-accent': department.color} as CSSProperties;
}

function pointStyle(x: number, y: number, width: number, height: number): CSSProperties {
  return {left: `${x / width * 100}%`, top: `${y / height * 100}%`};
}

const detailPoints: Record<number, {x: number; y: number}[]> = {
  2: [{x: 170, y: 135}, {x: 530, y: 390}],
  3: [{x: 350, y: 105}, {x: 165, y: 390}, {x: 535, y: 390}],
  4: [{x: 165, y: 120}, {x: 535, y: 120}, {x: 165, y: 410}, {x: 535, y: 410}],
  5: [{x: 350, y: 63}, {x: 150, y: 135}, {x: 550, y: 135}, {x: 170, y: 410}, {x: 530, y: 410}],
};

type PhysicsResult = {
  lift: {value: number; unit: string};
  weight: {value: number; unit: string};
  margin: {value: number; unit: string};
  supports_weight: boolean;
  scope: string;
};

function PhysicsCalculator() {
  const [values, setValues] = useState({mass: '0.25', wingArea: '0.12', speed: '6', density: '1.2', coefficient: '0.8'});
  const [result, setResult] = useState<PhysicsResult | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const fields = [
    {key: 'mass', label: 'Mass (kg)'},
    {key: 'wingArea', label: 'Wing area (m²)'},
    {key: 'speed', label: 'Air speed (m/s)'},
    {key: 'density', label: 'Air density (kg/m³)'},
    {key: 'coefficient', label: 'Lift coefficient (CL)'},
  ] as const;

  async function check(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError(''); setResult(null);
    try {
      const response = await fetch('/api/physics/check', {
        method: 'POST', credentials: 'include',
        headers: {'Content-Type': 'application/json', 'X-Friday-Request': '1'},
        body: JSON.stringify({
          mass: {value: Number(values.mass), unit: 'kg'},
          wing_area: {value: Number(values.wingArea), unit: 'm2'},
          air_speed: {value: Number(values.speed), unit: 'm/s'},
          air_density: {value: Number(values.density), unit: 'kg/m3'},
          lift_coefficient: Number(values.coefficient),
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Check the numeric inputs and try again.');
      setResult(data as PhysicsResult);
    } catch (cause) {setError((cause as Error).message || 'The check is unavailable.');}
    finally {setBusy(false);}
  }

  return <form className="atlas-physics" onSubmit={event => void check(event)}>
    <h4>Try a static lift check</h4>
    <div className="atlas-physics-fields">{fields.map(field => <label key={field.key}>{field.label}<input type="number" inputMode="decimal" min="0.000001" step="any" required value={values[field.key]} onChange={event => setValues(current => ({...current, [field.key]: event.target.value}))}/></label>)}</div>
    <button className="atlas-open" type="submit" disabled={busy}>{busy ? 'Checking…' : 'Calculate lift ↗'}</button>
    {error && <p className="atlas-physics-error" role="alert">{error}</p>}
    {result && <div className="atlas-physics-result" role="status"><strong>{result.supports_weight ? 'Lift meets weight at these inputs' : 'Lift is below weight at these inputs'}</strong><span>Lift {result.lift.value.toFixed(3)} {result.lift.unit} · Weight {result.weight.value.toFixed(3)} {result.weight.unit}</span><span>Margin {result.margin.value.toFixed(3)} {result.margin.unit}</span><small>{result.scope}</small></div>}
  </form>;
}

export function CapabilityMap({status, connected, motion, onChat, onResearch, onSettings}: {
  status: ServiceStatus | null;
  connected: boolean;
  motion: boolean;
  onChat: () => void;
  onResearch: () => void;
  onSettings: () => void;
}) {
  const [departmentId, setDepartmentId] = useState<string | null>(null);
  const [capabilityId, setCapabilityId] = useState<string | null>(null);
  const [directory, setDirectory] = useState(false);
  const [rolloutOpen, setRolloutOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'setup' | 'planned'>('all');
  const selectedDepartment = departments.find(d => d.id === departmentId);
  const selectedCapability = selectedDepartment?.capabilities.find(c => c.id === capabilityId) ?? selectedDepartment?.capabilities[0];
  const allCapabilities = departments.flatMap(department => department.capabilities.map(capability => ({department, capability})));
  const counts = allCapabilities.reduce<Record<Availability, number>>((result, {capability}) => {
    result[availability(capability, status, connected)] += 1;
    return result;
  }, {active: 0, setup: 0, configured: 0, planned: 0, 'not-trained': 0, checking: 0});
  const filtered = allCapabilities.filter(({department, capability}) => {
    const state = availability(capability, status, connected);
    const matchesState = filter === 'all' || (filter === 'planned' ? state === 'planned' || state === 'not-trained' : filter === 'active' ? state === 'active' || state === 'configured' : state === 'setup');
    const matchesSearch = `${department.title} ${capability.title} ${capability.summary}`.toLowerCase().includes(search.trim().toLowerCase());
    return matchesState && matchesSearch;
  });

  function openDepartment(department: Department, capability?: Capability) {
    setDepartmentId(department.id);
    setCapabilityId(capability?.id ?? department.capabilities[0].id);
    setDirectory(false);
    setRolloutOpen(false);
  }

  function navigateDepartment(direction: number) {
    const current = departments.findIndex(d => d.id === departmentId);
    openDepartment(departments[(current + direction + departments.length) % departments.length]);
  }

  function runAction(action: Action) {
    if (action === 'chat') onChat();
    else if (action === 'research') onResearch();
    else onSettings();
  }

  function capabilityButton(capability: Capability, point: {x: number; y: number}, index: number) {
    const state = availability(capability, status, connected);
    return <button
      key={capability.id}
      type="button"
      className={'atlas-satellite ' + (selectedCapability?.id === capability.id ? 'selected' : '') + ' state-' + state}
      style={pointStyle(point.x, point.y, 700, 530)}
      aria-pressed={selectedCapability?.id === capability.id}
      onClick={() => setCapabilityId(capability.id)}
    ><span className="atlas-satellite-number">{String(index + 1).padStart(2, '0')}</span><strong>{capability.title}</strong><small>{labels[state]}</small></button>;
  }

  const selectedState = selectedCapability ? availability(selectedCapability, status, connected) : null;
  const selectedAction = selectedCapability?.action && selectedState && !['planned', 'not-trained', 'checking'].includes(selectedState)
    ? selectedState === 'setup' ? 'settings' : selectedCapability.action : null;

  return <section className={'capability-map ' + (!motion ? 'still' : '') + (rolloutOpen ? ' show-rollout' : '')} aria-labelledby="atlas-title">
    <div className="atlas-topline"><span>FRIDAY / SYSTEM ATLAS</span><span>OWNER-GOVERNED CAPABILITIES</span></div>
    <div className="atlas-intro"><div><p className="eyebrow">A MAP OF WHAT EXISTS — AND WHAT COMES NEXT</p><h1 id="atlas-title">Your FRIDAY systems.</h1><p>Explore each sector, inspect its real state, and open the workflows that are available now.</p></div><div className="atlas-top-actions"><button type="button" className={rolloutOpen ? 'selected' : ''} aria-pressed={rolloutOpen} onClick={() => {setRolloutOpen(true); setDirectory(false); setDepartmentId(null);}}>◎ Team rollout</button><button type="button" className={directory ? 'selected' : ''} aria-pressed={directory} onClick={() => {setDirectory(true); setRolloutOpen(false);}}>☷ Directory</button>{(departmentId || directory || rolloutOpen) && <button type="button" onClick={() => {setRolloutOpen(false); setDirectory(false); setDepartmentId(null); setCapabilityId(null);}}>↶ Overview</button>}</div></div>
    <div className="atlas-legend" aria-label="Capability status legend"><span><i className="state-active"/> {counts.active} active</span><span><i className="state-configured"/> {counts.configured} configured · verify</span><span><i className="state-setup"/> {counts.setup} setup required</span><span><i className="state-planned"/> {counts.planned + counts['not-trained']} in development / not trained</span></div>

    {rolloutOpen && <RolloutMap onResearch={onResearch}/>}

    {directory ? <div className="atlas-directory"><div className="atlas-directory-top"><div><p className="eyebrow">SYSTEM DIRECTORY</p><h2>Every capability, by sector.</h2></div><label>Search capabilities<input type="search" placeholder="Find a capability or sector…" value={search} onChange={e => setSearch(e.target.value)}/></label></div><div className="atlas-filters" role="group" aria-label="Filter capabilities">{([['all', 'All'], ['active', 'Active / configured'], ['setup', 'Needs setup'], ['planned', 'In development']] as const).map(([id, name]) => <button type="button" key={id} aria-pressed={filter === id} onClick={() => setFilter(id)}>{name}</button>)}</div><div className="atlas-directory-grid">{filtered.map(({department, capability}) => {const state = availability(capability, status, connected); return <button key={capability.id} type="button" style={departmentStyle(department)} onClick={() => openDepartment(department, capability)}><span>{department.symbol} &nbsp;{department.title}</span><strong>{capability.title}</strong><small>{capability.summary}</small><em className={'atlas-status state-' + state}>{labels[state]}</em></button>;})}{filtered.length === 0 && <p className="atlas-empty">No capabilities match that search and filter.</p>}</div></div> : selectedDepartment ? <div className="atlas-detail" style={departmentStyle(selectedDepartment)}><div className="atlas-detail-heading"><button type="button" onClick={() => {setDepartmentId(null); setCapabilityId(null);}}>← All sectors</button><div><span className="eyebrow">SECTOR {String(departments.indexOf(selectedDepartment) + 1).padStart(2, '0')} / {String(departments.length).padStart(2, '0')}</span><h2>{selectedDepartment.title}</h2><p>{selectedDepartment.description}</p></div><div className="atlas-stepper"><button type="button" aria-label="Previous sector" onClick={() => navigateDepartment(-1)}>←</button><button type="button" aria-label="Next sector" onClick={() => navigateDepartment(1)}>→</button></div></div><div className="atlas-detail-layout"><div className="atlas-detail-orbit" aria-label={`${selectedDepartment.title} capability map`}><div className="atlas-detail-rings" aria-hidden="true"/><svg aria-hidden="true" className="atlas-detail-lines" viewBox="0 0 700 530" preserveAspectRatio="none">{selectedDepartment.capabilities.map((capability, index) => {const point = detailPoints[selectedDepartment.capabilities.length][index]; return <line key={capability.id} x1="350" y1="265" x2={point.x} y2={point.y}/>;})}</svg><div className="atlas-department-core"><span>{selectedDepartment.symbol}</span><strong>{selectedDepartment.title}</strong><small>{selectedDepartment.capabilities.length} SYSTEMS</small></div>{selectedDepartment.capabilities.map((capability, index) => capabilityButton(capability, detailPoints[selectedDepartment.capabilities.length][index], index))}</div><aside className="atlas-inspector" aria-labelledby="atlas-selection-title"><p className="eyebrow">SYSTEM DETAIL / {selectedCapability?.id.toUpperCase().replaceAll('-', ' ')}</p><span className={'atlas-status state-' + selectedState}>{selectedState ? labels[selectedState] : ''}</span><h3 id="atlas-selection-title">{selectedCapability?.title}</h3><p className="atlas-inspector-summary">{selectedCapability?.summary}</p><p>{selectedCapability?.detail}</p>{selectedState === 'setup' && <div className="atlas-condition">Service credentials are missing. Add them on the server, then test a live request.</div>}{selectedState === 'configured' && <div className="atlas-condition">Credentials are present. Live provider access and output quality still need testing.</div>}{selectedState === 'not-trained' && <div className="atlas-condition">No FRIDAY physics weights or evaluation results exist yet.</div>}{selectedCapability?.id === 'physics-check' && selectedState === 'active' && <PhysicsCalculator/>}{selectedAction && <button type="button" className="atlas-open" onClick={() => runAction(selectedAction)}>{selectedState === 'setup' ? 'View service setup' : selectedCapability?.actionLabel} ↗</button>}{selectedCapability?.reference && <a className="atlas-reference" href={selectedCapability.reference.url} target="_blank" rel="noopener noreferrer">{selectedCapability.reference.label} ↗</a>}</aside></div></div> : <div className="atlas-overview" aria-label="FRIDAY capability sectors"><div className="atlas-overview-rings" aria-hidden="true"/><svg className="atlas-overview-lines" aria-hidden="true" viewBox="0 0 1000 650" preserveAspectRatio="none">{departments.map(d => <line key={d.id} x1="500" y1="330" x2={d.x} y2={d.y}/>)}</svg><div className="atlas-hub"><span>F</span><strong>FRIDAY</strong><small>{counts.active} ACTIVE SYSTEMS</small></div>{departments.map((department, index) => <button key={department.id} className="atlas-sector" type="button" style={{...departmentStyle(department), ...pointStyle(department.x, department.y, 1000, 650)}} onClick={() => openDepartment(department)}><span className="atlas-sector-symbol">{department.symbol}</span><span className="atlas-sector-label"><small>{String(index + 1).padStart(2, '0')} / SECTOR</small><strong>{department.title}</strong><em>{department.capabilities.length} systems</em></span></button>)}</div>}
    <p className="atlas-footnote">Status describes FRIDAY’s implementation and configuration, not third-party model performance. Referenced projects are not connected until integrated and tested.</p>
  </section>;
}
