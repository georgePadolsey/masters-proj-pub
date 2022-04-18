import React, { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import Earth from "../components/Earth";
import { OrbitControls, PerspectiveCamera, Stars } from "@react-three/drei";
import * as THREE from "three";
const IndexPage = () => {
  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        position: "fixed",
        top: 0,
        left: 0,
      }}
    >
      <Canvas resize={{ debounce: 100 }}>
        <Suspense fallback={null}>
          <ambientLight intensity={0.15} />
          <pointLight position={[10, 10, -10]} intensity={0.4} />
          <Earth position={[0, 0, 0]} />
          <mesh>
            <sphereBufferGeometry args={[100, 32, 32]} />
            <meshBasicMaterial color="black" side={THREE.DoubleSide} />
          </mesh>
          <OrbitControls
            addEventListener={undefined}
            hasEventListener={undefined}
            removeEventListener={undefined}
            dispatchEvent={undefined}
            makeDefault
          />
          <PerspectiveCamera
            fov={60}
            makeDefault
            position={[0, 0, 15]}
            near={0.01}
            far={1000}
          />
        </Suspense>
      </Canvas>
    </div>
  );
};

export default IndexPage;
