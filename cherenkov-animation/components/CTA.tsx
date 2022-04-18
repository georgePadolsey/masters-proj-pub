import { Line, useHelper } from "@react-three/drei";
import { useEffect, useRef } from "react";
import { CameraHelper, PerspectiveCamera } from "three";
import * as THREE from "three";

const CTA = ({ position, active }) => {
  const horizCamera = useRef<PerspectiveCamera>();
  const vertCamera = useRef<PerspectiveCamera>();
  let dronePositionS = new THREE.Spherical().setFromVector3(position);
  dronePositionS.phi += 1;
  dronePositionS.theta -= 0;
  dronePositionS.radius = 0.1;
  let dronePosition = new THREE.Vector3().setFromSpherical(dronePositionS);

  //   const horizontalView = useRef();
  useHelper(horizCamera, CameraHelper, 1, "hotpink");
  useHelper(vertCamera, CameraHelper, 1, "hotpink");

  useEffect(() => {
    const horizontalView = new THREE.Spherical().setFromVector3(position);
    horizontalView.phi += 0.8;
    horizontalView.theta -= 0.1;
    horizontalView.radius = 5000;

    const verticalView = new THREE.Spherical().setFromVector3(position);
    verticalView.radius += 0.2;

    if (horizCamera.current != null) {
      horizCamera.current.lookAt(
        new THREE.Vector3().setFromSpherical(horizontalView)
      );
    }

    if (vertCamera.current != null) {
      vertCamera.current.lookAt(
        new THREE.Vector3().setFromSpherical(verticalView)
      );
    }
  }, []);

  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[0.01, 64, 64]} />
        <meshStandardMaterial color="red" />
      </mesh>

      <mesh position={dronePosition}>
        <boxGeometry args={[0.01, 0.01, 0.01]} />
        <meshStandardMaterial color="orange" />
      </mesh>
      <perspectiveCamera
        args={[75, 1, 0.01, 0.1]}
        position={[0, 0, 0]}
        ref={horizCamera}
      />
      <Line
        color="hotpink"
        points={[[0, 0, 0], dronePosition.toArray()]}
        lineWidth={2}
      />

      {/* <perspectiveCamera
        args={[75, 1, 0.1, 0.5]}
        position={[0, 0, 0]}
        ref={vertCamera}
      /> */}
    </group>
  );
};
export default CTA;
