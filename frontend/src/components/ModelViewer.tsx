import React, { Suspense, Component, ReactNode } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { OrbitControls, Stage } from '@react-three/drei';
import { STLLoader } from 'three-stdlib';
import { ThreeMFLoader } from 'three-stdlib';
import * as THREE from 'three';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("3D Model Viewer Error:", error);
    console.error("Component Stack:", errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

interface ModelViewerProps {
  url: string;
  type: 'stl' | '3mf';
}

const Model = ({ url, type }: ModelViewerProps) => {
  const loader = type === 'stl' ? STLLoader : ThreeMFLoader;
  
  // Create a stable loader reference based on type
  // useLoader caches based on arguments, so this is fine.
  
  // @ts-ignore - Dynamic loader type
  const geom = useLoader(loader, url);

  if (type === 'stl') {
    return (
      <mesh geometry={geom as THREE.BufferGeometry} castShadow receiveShadow>
        <meshStandardMaterial color="#6366f1" roughness={0.5} metalness={0.1} />
      </mesh>
    );
  } else {
    // 3MF loader returns a Group (Object3D)
    return <primitive object={geom} castShadow receiveShadow />;
  }
};

const ModelViewer = ({ url, type }: ModelViewerProps) => {
  return (
    <div className="w-full h-full bg-gray-900 rounded-lg overflow-hidden relative">
      <ErrorBoundary fallback={
        <div className="absolute inset-0 flex items-center justify-center text-white p-4 text-center">
          <div className="bg-red-900/50 p-4 rounded border border-red-700">
            <h3 className="font-bold mb-2">Failed to load model</h3>
            <p className="text-sm opacity-75">Check console for details or verify file exists.</p>
            <p className="text-xs mt-2 font-mono break-all">{url}</p>
          </div>
        </div>
      }>
        <Canvas shadows={{ type: THREE.PCFShadowMap }} dpr={[1, 2]} camera={{ position: [0, 0, 150], fov: 50 }}>
          <Suspense fallback={null}>
            <Stage environment="city" intensity={0.6}>
              <Model url={url} type={type} />
            </Stage>
          </Suspense>
          <OrbitControls autoRotate autoRotateSpeed={0.5} makeDefault />
        </Canvas>
      </ErrorBoundary>
      
      <div className="absolute top-4 right-4 pointer-events-none">
        <span className="bg-black/50 text-white text-xs px-2 py-1 rounded">
          {type.toUpperCase()} Viewer
        </span>
      </div>
    </div>
  );
};

export default ModelViewer;
