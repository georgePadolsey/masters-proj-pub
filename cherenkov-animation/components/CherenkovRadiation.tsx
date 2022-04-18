import { Line, QuadraticBezierLine } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import {
  createRef,
  RefObject,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import seedrandom from "seedrandom";
import * as THREE from "three";
import { Line2 } from "three-stdlib";

const avgPrimaryShower = 30;
const avgSecondaryShower = 30;

const maxLengthPrimary = 0.3;
const maxLengthSecondary = 0.1;

// @from https://stackoverflow.com/questions/25582882/javascript-math-random-normal-distribution-gaussian-bell-curve
function randn_bm(rng) {
  let u = 0,
    v = 0;
  while (u === 0) u = rng(); //Converting [0,1) to (0,1)
  while (v === 0) v = rng();
  let num = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  num = num / 10.0 + 0.5; // Translate to 0 -> 1
  if (num > 1 || num < 0) return randn_bm(rng); // resample between 0 and 1
  return num;
}

const RAY_DURATION_TIME = 1_000;
const SECONDARY_START_TIME = 1_000;

const OPACITY_FADE = 800;

const CherenkovRadiation = ({ resetKey, active, ...props }) => {
  const lines = useMemo(() => {
    var rng = seedrandom("jaffa");

    const primaryShowerNums = randn_bm(rng) * avgPrimaryShower;
    const secondaryShowerNums = randn_bm(rng) * avgSecondaryShower;

    let lines = [];
    for (let i = 0; i < primaryShowerNums; i++) {
      let newLine = [
        [0, 0, 0],
        [
          maxLengthPrimary * randn_bm(rng),
          maxLengthPrimary * (randn_bm(rng) - 0.5),
          0,
        ],
        1,
      ];
      lines.push(newLine);
      for (let j = 0; j < secondaryShowerNums; j++) {
        lines.push([
          newLine[1],
          [
            maxLengthSecondary * randn_bm(rng) + newLine[1][0],
            maxLengthSecondary * (randn_bm(rng) - 0.5) + newLine[1][1],
            newLine[1][2],
          ],
          2,
        ]);
      }
    }
    return lines;
  }, []);

  const lineLength = lines.length;
  const elRefs = useRef<RefObject<Line2>[]>([]);
  const flashLightRef = useRef<THREE.PointLight>();
  const followLightRef = useRef<THREE.PointLight>();
  const startTime = useRef<number>();

  useEffect(() => {
    // add or remove refs

    elRefs.current = Array(lineLength)
      .fill(undefined)
      .map((_, i) => elRefs?.current[i] ?? createRef<Line2>());
  }, [lineLength]);

  useEffect(() => {
    if (!active) {
      return;
    }
    startTime.current = +new Date();
    if (flashLightRef.current != null) {
      flashLightRef.current.intensity = 10;
    }
  }, [resetKey, active]);

  useFrame((state, dt) => {
    if (
      startTime.current == null ||
      flashLightRef.current == null ||
      followLightRef.current == null ||
      elRefs.current == null
    ) {
      return;
    }

    flashLightRef.current.intensity = Math.max(
      0,
      flashLightRef.current.intensity * 0.9
    );

    // console.log(flashLightRef.current);
    // flashLightRef.current.intensity -= 0.1;

    let i = 0;

    for (const ref of elRefs.current) {
      if (ref.current == null) {
        i++;
        continue;
      }
      let isPrimary = lines[i][2] === 1;
      let diff = +new Date() - startTime.current;

      if (!isPrimary) {
        if (diff <= SECONDARY_START_TIME) {
          i++;
          continue;
        } else {
          diff -= SECONDARY_START_TIME;
        }
      }

      ref.current.material.opacity = Math.max(
        0,
        Math.min(1, 1 - (diff - OPACITY_FADE) / OPACITY_FADE)
      );

      // ref.current.material

      let percentComplete = Math.min(1, diff / RAY_DURATION_TIME);

      // console.log(percentComplete);

      let s = lines[i][1].slice();

      s[0] =
        (lines[i][1][0] - lines[i][0][0]) * percentComplete + lines[i][0][0];

      // console.log(ref.current);

      // ref.current.distStart = new THREE.Vector3(0, 0, 1);
      // ref.current.distEnd = new THREE.Vector3(0, 0, 1);
      // ref.current.geometry.vertices = [lines[i][0], s];
      // ref.current.geometry.attributes.position.needsUpdate = true;
      ref.current.geometry.setPositions([...lines[i][0], ...s]);
      // console.log();
      // ref.current.geometry.vertices = [[s[0], s[1], s[2]];
      // ref.current.geometry.verticesNeedUpdate = true;
      if (i === 0) {
        followLightRef.current.position.set(s[0], s[1], s[2]);
      }
      i++;
    }
  });

  const allLines = useMemo(() => {
    return lines.map(([start, end, stage], i) => {
      elRefs.current[i] = createRef<Line2>();
      return (
        active && (
          <Line
            key={i}
            ref={elRefs.current[i]}
            points={[start, end]}
            color="purple" // Default
            lineWidth={1} // In pixels (default)
            opacity={active ? 1 : 0}
            transparent={true}
            dashed={false} // Default
            //   vertexColors={[[0, 0, 0], ...]} // Optional array of RGB values for each point
            //   {...lineProps}                  // All THREE.Line2 props are valid
            //   {...materialProps}              // All THREE.LineMaterial props are valid
          />
        )
      );
    });
  }, [lines, elRefs, active]);

  return (
    <group {...props}>
      {allLines}
      <pointLight
        position={[0, 0, 0]}
        intensity={active ? 10 : 0}
        color="purple"
        ref={flashLightRef}
      />
      <pointLight
        position={[10, 10, 10]}
        intensity={active ? 0.6 : 0}
        color="purple"
        ref={followLightRef}
      />
    </group>
  );
};

export default CherenkovRadiation;
