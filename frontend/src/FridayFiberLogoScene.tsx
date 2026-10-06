import {useRef} from 'react';
import {Canvas, useFrame} from '@react-three/fiber';
import type {Group, Mesh} from 'three';

type SceneProps = {motion: boolean; detailed: boolean};

function Reactor({motion, detailed}: SceneProps) {
  const outer = useRef<Group>(null);
  const crystal = useRef<Mesh>(null);
  const crown = useRef<Group>(null);

  useFrame(({clock}, delta) => {
    if (!motion) return;
    const step = Math.min(delta, 0.05);
    if (outer.current) {
      outer.current.rotation.y += step * 0.27;
      outer.current.rotation.z += step * 0.08;
    }
    if (crystal.current) {
      crystal.current.rotation.y += step * 0.24;
      crystal.current.position.y = Math.sin(clock.elapsedTime * 1.1) * 0.035;
    }
    if (crown.current) crown.current.rotation.z -= step * 0.12;
  });

  return <>
    <ambientLight intensity={1.15}/>
    <pointLight color="#6fdcff" position={[1.5, 1.8, 3]} intensity={24}/>
    <pointLight color="#e8a951" position={[-1.6, -1.2, 2]} intensity={14}/>

    <mesh position={[0, 0, -0.2]} rotation={[Math.PI / 2, 0, 0]}>
      <cylinderGeometry args={[0.64, 0.75, 0.12, 32]}/>
      <meshStandardMaterial color="#102230" metalness={0.72} roughness={0.22} emissive="#0b5f7b" emissiveIntensity={0.45}/>
    </mesh>
    <mesh position={[0, 0, -0.12]}>
      <torusGeometry args={[0.68, 0.045, 10, 48]}/>
      <meshStandardMaterial color="#a7f3ff" metalness={0.44} roughness={0.18} emissive="#54d4ff" emissiveIntensity={0.78}/>
    </mesh>

    <group ref={outer} rotation={[0.36, -0.2, -0.3]}>
      <mesh>
        <torusGeometry args={[1.0, 0.055, 12, 64]}/>
        <meshStandardMaterial color="#83dafa" metalness={0.72} roughness={0.22} emissive="#238cc4" emissiveIntensity={0.5}/>
      </mesh>
      <mesh rotation={[1.15, 0.46, 0.14]}>
        <torusGeometry args={[0.89, 0.037, 10, 64]}/>
        <meshStandardMaterial color="#dceef0" metalness={0.82} roughness={0.2} emissive="#30729d" emissiveIntensity={0.27}/>
      </mesh>
      <mesh rotation={[0.1, 0.06, -0.32]}>
        <torusGeometry args={[1.08, 0.052, 10, 48, Math.PI * 0.69]}/>
        <meshStandardMaterial color="#ffc987" metalness={0.65} roughness={0.19} emissive="#ca6d27" emissiveIntensity={0.72}/>
      </mesh>
    </group>

    {detailed && <group ref={crown}>
      {Array.from({length: 8}, (_, index) => <group key={index} rotation={[0, 0, index * Math.PI / 4]}>
        <mesh position={[0, 0.77, 0.1]}>
          <boxGeometry args={[0.047, 0.16, 0.045]}/>
          <meshStandardMaterial color={index % 2 ? '#8dd8ea' : '#f3b778'} metalness={0.5} roughness={0.2} emissive={index % 2 ? '#4ac6f1' : '#d1893d'} emissiveIntensity={0.55}/>
        </mesh>
      </group>)}
    </group>}

    <mesh ref={crystal} rotation={[0.3, 0.45, 0.2]}>
      <octahedronGeometry args={[0.43, 0]}/>
      <meshStandardMaterial color="#a5eaff" metalness={0.46} roughness={0.14} emissive="#2489c8" emissiveIntensity={0.8}/>
    </mesh>
    <mesh position={[0, 0, 0.13]}>
      <octahedronGeometry args={[0.47, 0]}/>
      <meshBasicMaterial color="#d7faff" wireframe transparent opacity={0.36}/>
    </mesh>
  </>;
}

export default function FridayFiberLogoScene({motion, detailed}: SceneProps) {
  return <Canvas
    className="friday-fiber-canvas"
    camera={{position: [0, 0, 4.2], fov: 34, near: 0.1, far: 20}}
    dpr={[1, 1.5]}
    frameloop={motion ? 'always' : 'demand'}
    gl={{alpha: true, antialias: true, powerPreference: 'low-power'}}
    fallback={<span className="friday-fiber-logo-fallback" aria-hidden="true"><span/></span>}
  ><Reactor motion={motion} detailed={detailed}/></Canvas>;
}
