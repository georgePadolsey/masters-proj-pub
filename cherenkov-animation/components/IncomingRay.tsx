import { Line } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { Line2 } from "three-stdlib";

const spinAxis = new THREE.Vector3(1, 0, 0);

const spinRadius = 0.01;
let spinAngle = 0;
const spinSize = 0.2;
const points = 50;
const maxLoops = 3;

const spinSpeed = 0.01;

const IncomingRay = ({ from, to, active, resetKey, onComplete }) => {
  const spinRef = useRef<Line2>();
  const mainGroup = useRef<THREE.Group>();
  const startTime = useRef<number>();

  const hasCompleted = useRef<boolean>(false);

  const fromVec = useRef<THREE.Vector3>();
  const toVec = useRef<THREE.Vector3>();
  const curVec = useRef<THREE.Vector3>();

  useEffect(() => {
    if (active) {
      startTime.current = +new Date();
      hasCompleted.current = false;
    }

    fromVec.current = new THREE.Vector3(...from);
    toVec.current = new THREE.Vector3(...to);
    curVec.current = new THREE.Vector3();
  }, [active, resetKey]);

  useFrame(() => {
    if (
      startTime.current == null ||
      spinRef.current == null ||
      fromVec.current == null ||
      toVec.current == null ||
      curVec.current == null
    ) {
      return;
    }

    spinRef.current.rotation.x += 0.5;

    //   mainGroup.current.set

    const diff = +new Date() - startTime.current;
    const percent = Math.min(1, diff / 5_000);

    // @ts-ignore
    spinRef.current.opacity = 1 - (percent - 0.5) * 2;

    if (!hasCompleted.current && percent >= 1) {
      hasCompleted.current = true;
      onComplete();
    }

    mainGroup.current.position.x = THREE.MathUtils.lerp(
      fromVec.current.x,
      toVec.current.x,
      percent
    );

    mainGroup.current.position.y = THREE.MathUtils.lerp(
      fromVec.current.y,
      toVec.current.y,
      percent
    );

    mainGroup.current.position.z = THREE.MathUtils.lerp(
      fromVec.current.z,
      toVec.current.z,
      percent
    );
  });

  const spinPoints = useMemo(() => {
    const spinPosition = new THREE.Vector3(0, 0, 0);
    const spinPoints = [];

    for (let i = 0; i < points; i++) {
      spinPoints.push(
        new THREE.Vector3(
          //   0,
          -(i / points) * spinSize,
          spinRadius * Math.cos(spinAngle),
          spinRadius * Math.sin(spinAngle)
        ).add(spinPosition)
      );
      spinAngle += (Math.PI * 2 * maxLoops) / points;
    }
    return spinPoints;
  }, [from]);

  return (
    <group position={from} ref={mainGroup}>
      {active && (
        <Line
          points={spinPoints}
          color="yellow"
          lineWidth={1}
          ref={spinRef}
          transparent={true}
          opacity={1}
          userData={{ test: "incoming" }}
        />
      )}
    </group>
  );
};

export default IncomingRay;
