import {useEffect, useState} from 'react';
import './cinematic-media.css';

export type CinematicSources = {
  hero: string;
  assembly: string;
  voice: string;
};

type Scene = keyof CinematicSources;

const scenes: {id: Scene; label: string; eyebrow: string; title: string; description: string}[] = [
  {
    id: 'hero',
    label: 'Arrival',
    eyebrow: '01 / THE COMMAND CENTER',
    title: 'A world at your command.',
    description: 'The visual identity of your private FRIDAY workspace.',
  },
  {
    id: 'assembly',
    label: 'Systems',
    eyebrow: '02 / SYSTEMS IN MOTION',
    title: 'Built around your work.',
    description: 'A cinematic view of FRIDAY’s connected systems.',
  },
  {
    id: 'voice',
    label: 'Voice concept',
    eyebrow: '03 / ASSISTANT CONCEPT',
    title: 'A presence that feels alive.',
    description: 'Visual concept preview. Voice interaction is not enabled yet.',
  },
];

export function CinematicMedia({sources, motion}: {sources: CinematicSources; motion: boolean}) {
  const [scene, setScene] = useState<Scene>('hero');
  const [reducedMotion, setReducedMotion] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(preference.matches);
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);

  const selected = scenes.find(item => item.id === scene)!;
  const showVideo = motion && !reducedMotion && !failed;

  return <section className={'cinematic-media scene-' + scene} aria-label="FRIDAY cinematic previews">
    <div className="cinematic-media-still" aria-hidden="true"/>
    {showVideo && <video
      key={scene}
      className={'cinematic-media-video' + (ready ? ' is-ready' : '')}
      autoPlay
      muted
      playsInline
      loop
      preload="metadata"
      aria-hidden="true"
      tabIndex={-1}
      onCanPlay={() => setReady(true)}
      onError={() => setFailed(true)}
    >
      <source src={sources[scene]} type="video/mp4"/>
    </video>}
    <div className="cinematic-media-shade" aria-hidden="true"/>
    <div className="cinematic-media-copy">
      <p className="cinematic-media-kicker">{selected.eyebrow}</p>
      <h2>{selected.title}</h2>
      <p>{selected.description}</p>
    </div>
    <nav className="cinematic-media-scenes" aria-label="Choose cinematic scene">
      {scenes.map((item, index) => <button
        key={item.id}
        type="button"
        aria-pressed={scene === item.id}
        onClick={() => {
          if (item.id === scene) return;
          setScene(item.id);
          setReady(false);
          setFailed(false);
        }}
      >
        <small>{String(index + 1).padStart(2, '0')}</small>
        <span>{item.label}</span>
      </button>)}
    </nav>
    <span className="cinematic-media-state">{showVideo ? 'CINEMATIC PREVIEW' : 'STILL PREVIEW'}</span>
  </section>;
}
