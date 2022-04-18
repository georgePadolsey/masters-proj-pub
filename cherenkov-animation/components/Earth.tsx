import { Line, useTexture } from "@react-three/drei";
import { useFrame, useLoader, useThree } from "@react-three/fiber";
import { useCallback, useEffect, useRef, useState } from "react";
import { TextureLoader } from "three/src/loaders/TextureLoader";
import * as THREE from "three";
import CherenkovRadiation from "./CherenkovRadiation";
import IncomingRay from "./IncomingRay";
import CTA from "./CTA";

const transPosition = new THREE.Vector3().setFromSphericalCoords(
  2.5,
  (54.2029 / 180) * Math.PI, //( north/ssouth
  ((67.8402 + 90) / 180) * Math.PI - Math.PI // east/west
);

const radiationPosition = new THREE.Vector3().setFromSphericalCoords(
  2.6,
  (54.2029 / 180) * Math.PI, //( north/ssouth
  ((67.8402 + 90) / 180) * Math.PI - Math.PI // east/west
);

const ctaPosition = transPosition.clone();

const Earth = (props) => {
  // This reference gives us direct access to the THREE.Mesh object
  const earthRef = useRef();
  const cloudRef = useRef();
  // Hold state for hovered and clicked events
  const [hovered, hover] = useState(false);
  const [clicked, click] = useState(false);

  const [resetKey, setResetKey] = useState("a");

  const [rayActive, setRayActive] = useState(true);
  const [radiationActive, setRadiationActive] = useState(false);

  const onRayComplete = useCallback(() => {
    setRayActive(false);
    setRadiationActive(true);
  }, []);

  const sphereGeoTest = useRef();

  const [colorMap, bumpMap, specularMap, cloudMap, transMap] = useTexture([
    "8081_earthmap4k.jpg",
    "8081_earthbump4k.jpg",
    "8081_earthspec4k.jpg",
    "8081_earthhiresclouds4K.png",
    "trans_improved.png",
  ]);

  const camera = useThree((state) => state.camera);
  const controls = useThree((state) => state.controls);

  useEffect(() => {
    // if (clicked) {
    //
    // }
    if (clicked) {
      console.log(controls);

      camera.zoom += 0.1;
      // controls.target = new THREE.Vector3(0, 4, 0);
      // controls.minZoom += 0.1;
      // @ts-ignore
      controls.target = transPosition;

      let newOne = new THREE.Spherical().setFromVector3(transPosition).clone();
      newOne.radius = 2.51;
      newOne.phi -= 0.1;
      let newV = new THREE.Vector3().setFromSpherical(newOne);
      camera.position.set(newV.x, newV.y, newV.z);
      setRayActive(true);
      setRadiationActive(false);
      setResetKey(Math.random() + "");
      // console.log(sphereGeoTest.current.attributes.uv);

      // controls.
      // camera.zoom = 5;
    }
  }, [clicked, controls]);

  useEffect(() => {
    // camera.position.setZ(15);
  }, [resetKey]);

  useFrame((state, delta) => {
    if (state.camera.position.z >= 6.5) {
      state.camera.position.setZ(state.camera.position.z - 0.03);
    }
    if (cloudRef.current != null) {
      // @ts-ignore
      cloudRef.current.rotation.y += 0.0003;
    }
  });

  transMap.minFilter = THREE.LinearFilter;
  // Return the view, these are regular Threejs elements expressed in JSX
  return (
    <group {...props} ref={earthRef}>
      <mesh
        scale={1}
        onClick={(event) => click(!clicked)}
        onPointerOver={(event) => hover(true)}
        onPointerOut={(event) => hover(false)}
      >
        <sphereGeometry args={[2.5, 512, 64]} />
        <meshPhongMaterial
          map={colorMap}
          bumpMap={bumpMap}
          bumpScale={1}
          // displacementMap={bumpMap}
          // displacementScale={0.1}
          // @ts-ignore
          specular={"grey"}
          specularMap={specularMap}
          // roughnessMap={roughnessMap}
          // aoMap={aoMap}
        />
      </mesh>
      {/* <mesh ref={cloudRef}>
        <sphereGeometry args={[2.53, 64, 64]} />
        <meshPhongMaterial
          map={cloudMap}
          transparent={true}
          side={THREE.DoubleSide}
          opacity={0.8}
          depthWrite={false}
        />
      </mesh> */}
      {/* <mesh>
        <sphereGeometry
          ref={sphereGeoTest}
          args={[
            2.5,
            512,
            512,
            Math.PI - (112.7129 / 180) * Math.PI, //(0.1276 / 180) * Math.PI * 2 + Math.PI, // east / west
            0.01 * 1.917,
            Math.PI - ((36.0902 + 90) / 180) * Math.PI, // north/south
            0.01,
          ]}
        />
        <meshPhongMaterial map={transMap} />
      </mesh> */}
      {/* <pointLight position={[10, 10, 10]} intensity={1} /> */}

      {/* <mesh position={transPosition}>
        <sphereGeometry args={[0.01, 128, 128]} />
        <lineBasicMaterial color="red" />
      </mesh> */}
      <IncomingRay
        from={[-20, 0, 0]}
        to={radiationPosition}
        resetKey={resetKey}
        active={rayActive}
        onComplete={onRayComplete}
      />
      <CherenkovRadiation
        position={radiationPosition}
        resetKey={resetKey}
        active={radiationActive}
      />
      <CTA position={ctaPosition} active={true} />
    </group>
  );
};

export default Earth;
