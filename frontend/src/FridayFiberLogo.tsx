import {Component, Suspense, lazy, useEffect, useState, type ReactNode} from 'react';
import './friday-fiber-logo.css';

const FridayFiberLogoScene = lazy(() => import('./FridayFiberLogoScene'));

export type FridayFiberLogoProps = {
  /** Pixel diameter. The scene uses less detail for compact marks. */
  size?: number;
  /** Follows FRIDAY's motion preference, and still respects reduced-motion OS settings. */
  motion?: boolean;
  className?: string;
  /** Set false only when the logo appears without the FRIDAY wordmark nearby. */
  decorative?: boolean;
};

class LogoErrorBoundary extends Component<{children: ReactNode}, {failed: boolean}> {
  state = {failed: false};

  static getDerivedStateFromError() {
    return {failed: true};
  }

  render() {
    return this.state.failed ? <LogoFallback/> : this.props.children;
  }
}

function LogoFallback() {
  return <span className="friday-fiber-logo-fallback" aria-hidden="true"><span/></span>;
}

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true);

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    if (!media) return;
    const update = () => setReduced(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  return reduced;
}

/** A self-contained three-dimensional reactor mark; its CSS fallback needs no GPU. */
export function FridayFiberLogo({size = 36, motion = true, className = '', decorative = true}: FridayFiberLogoProps) {
  const reducedMotion = useReducedMotion();
  const canUseWebGL = typeof window !== 'undefined' && 'WebGL2RenderingContext' in window;
  const diameter = Math.max(24, Math.min(size, 240));

  return <span
    className={'friday-fiber-logo ' + className}
    style={{width: diameter, height: diameter}}
    role={decorative ? undefined : 'img'}
    aria-hidden={decorative || undefined}
    aria-label={decorative ? undefined : 'FRIDAY three-dimensional reactor emblem'}
  >
    {canUseWebGL
      ? <LogoErrorBoundary><Suspense fallback={<LogoFallback/>}><FridayFiberLogoScene motion={motion && !reducedMotion} detailed={diameter >= 72}/></Suspense></LogoErrorBoundary>
      : <LogoFallback/>}
  </span>;
}
