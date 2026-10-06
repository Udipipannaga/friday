import {useId} from 'react';
import './friday-hologram.css';

export type FridayHologramState = 'idle' | 'listening' | 'thinking' | 'speaking';

export type FridayHologramProps = {
  state: FridayHologramState;
  /** Follows the workspace animation preference. The OS reduced-motion setting also applies. */
  motion?: boolean;
  variant?: 'stage' | 'compact';
  className?: string;
};

const descriptions: Record<FridayHologramState, string> = {
  idle: 'Standing by',
  listening: 'Listening to you',
  thinking: 'Thinking',
  speaking: 'Responding',
};

function Trace({d, opacity = 1}: {d: string; opacity?: number}) {
  return <path className="fh-trace" d={d} opacity={opacity}/>;
}

export function FridayHologram({state, motion = true, variant = 'stage', className = ''}: FridayHologramProps) {
  const id = useId().replace(/:/g, '');
  const glass = `${id}-glass`;
  const body = `${id}-body`;
  const beam = `${id}-beam`;
  const aura = `${id}-aura`;

  return <figure className={`friday-hologram friday-hologram--${variant} ${className}`} data-state={state} data-motion={motion ? 'on' : 'off'} role="img" aria-label={`FRIDAY hologram: ${descriptions[state]}`}>
    <div className="fh-atmosphere" aria-hidden="true"/>
    <svg className="fh-scene" viewBox="0 0 640 660" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={glass} x1="180" y1="30" x2="467" y2="535" gradientUnits="userSpaceOnUse">
          <stop stopColor="#c5f7ff" stopOpacity=".55"/>
          <stop offset=".35" stopColor="#39a7f3" stopOpacity=".14"/>
          <stop offset=".7" stopColor="#8aefff" stopOpacity=".38"/>
          <stop offset="1" stopColor="#2869b8" stopOpacity=".07"/>
        </linearGradient>
        <linearGradient id={body} x1="140" y1="340" x2="500" y2="560" gradientUnits="userSpaceOnUse">
          <stop stopColor="#59d6ff" stopOpacity=".18"/>
          <stop offset=".48" stopColor="#163f83" stopOpacity=".46"/>
          <stop offset="1" stopColor="#5af0ff" stopOpacity=".12"/>
        </linearGradient>
        <linearGradient id={beam} x1="320" y1="495" x2="320" y2="635" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6bdfff" stopOpacity=".27"/>
          <stop offset="1" stopColor="#389ddd" stopOpacity="0"/>
        </linearGradient>
        <radialGradient id={aura} cx="0" cy="0" r="1" gradientTransform="translate(320 328) rotate(90) scale(260 220)" gradientUnits="userSpaceOnUse">
          <stop stopColor="#2375c8" stopOpacity=".27"/>
          <stop offset="1" stopColor="#07152b" stopOpacity="0"/>
        </radialGradient>
        <filter id={`${id}-soft-glow`} x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="7"/></filter>
        <pattern id={`${id}-scan`} width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0 7.5H8" stroke="#9ceaff" strokeOpacity=".13" strokeWidth=".7"/></pattern>
      </defs>

      <ellipse cx="320" cy="312" rx="229" ry="271" fill={`url(#${aura})`}/>
      <g className="fh-field">
        <ellipse cx="320" cy="326" rx="268" ry="215" stroke="#55bbff" strokeOpacity=".16" strokeWidth="1" strokeDasharray="2 10"/>
        <ellipse cx="320" cy="326" rx="210" ry="253" stroke="#64bfff" strokeOpacity=".14" strokeWidth="1"/>
        <path d="M320 42v32M320 578v31M31 326h44M565 326h44M96 106l31 28M513 520l31 28M544 106l-31 28M127 520l-31 28" stroke="#7fcfff" strokeOpacity=".22"/>
        <circle cx="320" cy="72" r="3" fill="#83eafa"/><circle cx="110" cy="326" r="2.5" fill="#83eafa"/>
        <circle cx="530" cy="326" r="2.5" fill="#83eafa"/>
      </g>

      <path d="M229 496 159 620h322l-70-124Z" fill={`url(#${beam})`} className="fh-projector-beam"/>

      <g className="fh-avatar">
        <g className="fh-body">
          <path d="M270 331c-11 12-30 20-54 27l-62 28c-25 12-36 32-40 61l-10 75c88 25 341 25 432 0l-10-75c-4-29-15-49-40-61l-62-28c-24-7-43-15-54-27l-17 30h-66Z" fill={`url(#${body})`} stroke="#80dfff" strokeOpacity=".72" strokeWidth="1.8"/>
          <path d="M270 331c-14 17-31 22-47 31 32 26 63 41 97 55 34-14 65-29 97-55-16-9-33-14-47-31" stroke="#a3edff" strokeOpacity=".68" strokeWidth="2"/>
          <path d="M260 348 320 407l60-59m-111 12-29 54 42 101m89-155 29 54-42 101m-160-136c-20 35-26 74-26 129m296-129c20 35 26 74 26 129M320 417v99" stroke="#75c9ff" strokeOpacity=".5" strokeWidth="1"/>
          <path d="M159 387c42 10 83 31 124 55m198-55c-42 10-83 31-124 55M209 478h70m152 0h-70M232 505h39m137 0h-39" stroke="#63bcff" strokeOpacity=".3" strokeWidth="1"/>
          <path d="M153 389q60 72 119 105m215-105q-60 72-119 105" stroke="#cdf6ff" strokeOpacity=".17" strokeWidth="13"/>
          <path d="M270 331c-11 12-30 20-54 27l-62 28c-25 12-36 32-40 61l-10 75c88 25 341 25 432 0l-10-75c-4-29-15-49-40-61l-62-28c-24-7-43-15-54-27l-17 30h-66Z" fill={`url(#${id}-scan)`} opacity=".52"/>
          <path d="M282 326v29l38 47 38-47v-29" stroke="#9cecff" strokeOpacity=".8" strokeWidth="1.5"/>
          <path d="M320 410c-20 0-36 16-36 36s16 36 36 36 36-16 36-36-16-36-36-36Z" stroke="#72dfff" strokeOpacity=".36" strokeWidth="1.3"/>
          <circle className="fh-core-halo" cx="320" cy="446" r="26" stroke="currentColor" strokeWidth="5" opacity=".62" filter={`url(#${id}-soft-glow)`}/>
          <circle className="fh-core-ring" cx="320" cy="446" r="24" stroke="currentColor" strokeWidth="2" strokeDasharray="7 5"/>
          <path className="fh-core-mark" d="m320 433 11 13-11 13-11-13Z" fill="currentColor" fillOpacity=".28" stroke="currentColor" strokeWidth="1.5"/>
          <circle className="fh-core-light" cx="320" cy="446" r="4" fill="currentColor"/>
        </g>

        <g className="fh-head">
          <path d="M251 178c1-60 27-96 70-99 44 3 69 39 69 99v61c0 47-29 86-69 95-40-9-70-48-70-95Z" fill={`url(#${glass})`} stroke="#b6efff" strokeOpacity=".82" strokeWidth="2"/>
          <path d="M265 124c30-29 81-29 111 0M261 180c14-13 34-18 60-18s46 5 60 18M262 223c18 7 38 10 59 10s41-3 59-10M279 279c27 9 56 9 83 0M294 308c17 5 36 5 53 0" stroke="#8adfff" strokeOpacity=".42" strokeWidth="1.4"/>
          <path d="M321 81v251M288 91c-7 26-14 54-15 89v62c1 27 16 57 35 77M354 91c7 26 14 54 15 89v62c-1 27-16 57-35 77M253 201c25-13 48-19 68-19s43 6 68 19M255 245c22 12 44 18 66 18s44-6 66-18" stroke="#76ceff" strokeOpacity=".25" strokeWidth="1"/>
          <path d="M250 182c-14-2-16 19-10 34 3 8 7 15 14 17m135-51c14-2 16 19 10 34-3 8-7 15-14 17" stroke="#98eaff" strokeOpacity=".68" strokeWidth="1.4"/>
          <path d="M258 154h125M251 183h139M255 222h131M266 260h108M282 294h77" stroke="#ddfaff" strokeOpacity=".12" strokeWidth="5"/>
          <path d="M251 178c1-60 27-96 70-99 44 3 69 39 69 99v61c0 47-29 86-69 95-40-9-70-48-70-95Z" fill={`url(#${id}-scan)`} opacity=".48"/>
          <path d="M268 207c13-11 27-11 41 0m24 0c13-11 27-11 41 0" stroke="#b6f6ff" strokeWidth="2" strokeLinecap="round"/>
          <path d="M278 209c9 5 16 5 22 0m42 0c9 5 16 5 22 0" stroke="#63cbff" strokeOpacity=".8" strokeWidth="1.2"/>
          <circle cx="289" cy="207" r="3" fill="#c5faff"/><circle cx="353" cy="207" r="3" fill="#c5faff"/>
          <path d="M321 211v33l-9 7 9 4 9-4" stroke="#a9eaff" strokeOpacity=".65" strokeWidth="1.3"/>
          <path d="M302 277c12 5 26 5 38 0" stroke="#a5eaff" strokeWidth="1.3" strokeLinecap="round"/>
          <g className="fh-mouth-motion"><path d="M308 285h25" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/><path d="M315 290h12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></g>
          <circle cx="321" cy="80" r="3" fill="#b9f7ff"/>
          <path d="M282 93c-20 23-24 48-25 72m127 0c-1-24-5-49-25-72" stroke="#e3faff" strokeOpacity=".22" strokeWidth="6"/>
        </g>

        <g className="fh-pose fh-pose--idle">
          <Trace d="M176 382c-38 32-44 61-48 101l-7 32 70 12 25-42"/>
          <Trace d="M464 382c38 32 44 61 48 101l7 32-70 12-25-42"/>
          <Trace d="M159 420c21 15 38 39 48 64m274-64c-21 15-38 39-48 64" opacity={.52}/>
          <circle cx="142" cy="502" r="5" fill="currentColor" opacity=".75"/><circle cx="498" cy="502" r="5" fill="currentColor" opacity=".75"/>
        </g>
        <g className="fh-pose fh-pose--listening">
          <Trace d="M176 382c-38 32-44 61-48 101l-7 32 70 12 25-42"/>
          <Trace d="M464 382c30-27 34-64 20-105l-31-49-56-5"/>
          <Trace d="M449 372c13-35 8-67-9-102l-27-26" opacity={.6}/>
          <path d="M399 216c8-10 13-24 13-36m4 45c12-7 20-20 23-34m-19 44c14-3 26-13 32-27" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
          <circle className="fh-ear-signal" cx="394" cy="205" r="19" stroke="currentColor" strokeOpacity=".55"/>
        </g>
        <g className="fh-pose fh-pose--thinking">
          <Trace d="M464 382c38 32 44 61 48 101l7 32-70 12-25-42"/>
          <Trace d="M176 382c-24 25-22 54 12 70l83-38 39-117"/>
          <Trace d="M178 401c-17 27 0 38 31 45l74-45 20-86" opacity={.56}/>
          <path d="M296 309c7-12 8-25 6-39m7 38c11-11 16-25 17-38m-5 42c13-7 22-18 26-31" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
          <circle cx="302" cy="305" r="4" fill="currentColor"/>
        </g>
        <g className="fh-pose fh-pose--speaking">
          <Trace d="M176 382c-38 32-44 61-48 101l-7 32 70 12 25-42"/>
          <Trace d="M464 382c25 3 40-1 63-30l18-33"/>
          <Trace d="M441 389c42 16 76-19 99-54" opacity={.55}/>
          <g className="fh-open-hand"><path d="M543 320c-6-20-4-47-1-64m3 62 15-75m-12 76 30-65m-28 70 40-47m-47 45 53-22" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/><circle cx="547" cy="325" r="8" stroke="currentColor" strokeWidth="2"/><circle className="fh-hand-signal" cx="547" cy="325" r="29" stroke="currentColor" strokeOpacity=".5"/></g>
        </g>
      </g>

      <g className="fh-projection">
        <ellipse cx="320" cy="555" rx="191" ry="26" fill="#58cfff" opacity=".14" filter={`url(#${id}-soft-glow)`}/>
        <ellipse cx="320" cy="555" rx="207" ry="29" stroke="#70deff" strokeOpacity=".55" strokeWidth="1.2"/>
        <ellipse cx="320" cy="555" rx="165" ry="18" stroke="#70deff" strokeOpacity=".5" strokeWidth="1.1"/>
        <ellipse cx="320" cy="555" rx="113" ry="10" stroke="#70deff" strokeOpacity=".3" strokeWidth="1"/>
        <path d="M91 577c65 21 392 21 458 0M145 593c88 14 262 14 350 0" stroke="#69bfff" strokeOpacity=".17"/>
      </g>
    </svg>
    <figcaption className="fh-status"><span className="fh-status-line"/><span>F.R.I.D.A.Y.</span><strong>{descriptions[state]}</strong></figcaption>
  </figure>;
}
