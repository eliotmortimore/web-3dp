import React, { Suspense, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, Center } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { useLoader } from '@react-three/fiber';
import * as THREE from 'three';

interface ViewerProps {
  fileUrl: string | null;
  color: string;
}

const Model = ({ url, color }: { url: string; color: string }) => {
  const geometry = useLoader(STLLoader, url);
  
  // Center geometry to ensure it rotates around the middle
  useMemo(() => {
    if (geometry) {
      geometry.center();
      geometry.computeVertexNormals();
    }
  }, [geometry]);

  return (
    <mesh geometry={geometry} castShadow receiveShadow rotation={[-Math.PI / 2, 0, 0]}>
      <meshStandardMaterial color={color} roughness={0.5} metalness={0.1} />
    </mesh>
  );
};

const Viewer3D: React.FC<ViewerProps> = ({ fileUrl, color }) => {
  if (!fileUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
        <p>No model loaded</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] bg-gray-900 rounded-lg overflow-hidden shadow-xl">
      <Canvas shadows camera={{ position: [0, 0, 100], fov: 50 }}>
        <Suspense fallback={null}>
          <Stage environment="city" intensity={0.6}>
            <Center>
              <Model url={fileUrl} color={color} />
            </Center>
          </Stage>
        </Suspense>
        <OrbitControls autoRotate autoRotateSpeed={4} makeDefault />
      </Canvas>
    </div>
  );
};

export default Viewer3D;
