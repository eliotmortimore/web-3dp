import React, { useState, useEffect, useRef } from 'react';
import Viewer3D from '../components/Viewer3D';
import QuotePanel from '../components/QuotePanel';
import { UploadCloud, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';

// Main Home Component
function Home() {
  const { session } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [material, setMaterial] = useState<string>('PLA');
  const [color, setColor] = useState<string>('#ff0000');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [volume, setVolume] = useState<number | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const pollInterval = useRef<number | null>(null);

  // Handle File Selection (Upload & Start Analysis)
  const handleFileSelect = async (selectedFile: File) => {
    if (selectedFile) {
      setFile(selectedFile);
      
      // Create Object URL for local preview
      const url = URL.createObjectURL(selectedFile);
      setFileUrl(url);
      
      // Upload to Backend to start background slicing
      setAnalyzing(true);
      setStatusMessage("Uploading & Starting Analysis...");
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('material', material);
      formData.append('quantity', quantity.toString());

      try {
        const headers: Record<string, string> = {};
        
        if (session?.access_token) {
            headers['Authorization'] = `Bearer ${session.access_token}`;
        }

        const res = await api.post('/api/v1/upload', formData, {
            headers
        });
        
        setJobId(res.data.job_id);
        
        if (res.data.status === "ESTIMATED" || res.data.price) {
             setVolume(res.data.volume_cm3);
             setPrice(res.data.price);
             setAnalyzing(false);
             setStatusMessage("");
        } else {
             setStatusMessage("Processing...");
             // Fallback to polling if needed (though current flow is sync)
             startPolling(res.data.job_id);
        }
        
      } catch (err: any) {
          console.error("Upload failed", err);
          const msg = err.response?.data?.detail || "Failed to upload file";
          alert(msg);
          setAnalyzing(false);
          setStatusMessage("");
      }
    }
  };

  const startPolling = (id: number) => {
      if (pollInterval.current) clearInterval(pollInterval.current);
      
      pollInterval.current = window.setInterval(async () => {
          try {
              const res = await api.get(`/api/v1/jobs/${id}/status`);
              const job = res.data;
              
              if (job.status === "COMPLETED") {
                  setVolume(job.volume_cm3);
                  setPrice(job.price);
                  setAnalyzing(false);
                  setStatusMessage("");
                  stopPolling();
              } else if (job.status === "FAILED") {
                  setAnalyzing(false);
                  setStatusMessage("Analysis Failed. Please try another file.");
                  stopPolling();
              }
          } catch (err) {
              console.error("Polling error", err);
          }
      }, 1000);
  };

  const stopPolling = () => {
      if (pollInterval.current) {
          clearInterval(pollInterval.current);
          pollInterval.current = null;
      }
  };

  useEffect(() => {
      return () => stopPolling();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
      
      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">
          
          {/* Left Column: 3D Viewer (Spans 8 cols) */}
          <div className="lg:col-span-8 space-y-6 flex flex-col">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-1 flex-grow flex flex-col min-h-[500px]">
              <div className="flex justify-between items-center px-4 py-3 border-b border-gray-50">
                <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${analyzing ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`}></span>
                  3D Preview
                </h2>
                {analyzing ? (
                    <span className="text-xs font-mono text-blue-600 flex items-center gap-2">
                        <Loader2 className="w-3 h-3 animate-spin" /> {statusMessage}
                    </span>
                ) : volume && (
                  <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    Vol: {volume.toFixed(2)} cm³
                  </span>
                )}
              </div>
              
              <div className="flex-grow relative rounded-lg overflow-hidden bg-gray-900">
                <Viewer3D fileUrl={fileUrl} color={color} />
                
                {/* Overlay Controls */}
                <div className="absolute bottom-4 left-4 right-4 flex justify-between text-xs text-white/50 pointer-events-none">
                  <span>Drag to rotate</span>
                  <span>Scroll to zoom</span>
                </div>
              </div>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm flex items-start gap-3">
                <div className="p-2 bg-green-50 rounded-lg shrink-0">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-gray-900">Precise Quote</h3>
                  <p className="text-xs text-gray-500 mt-1">Pricing based on actual slicer simulation.</p>
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm flex items-start gap-3">
                <div className="p-2 bg-yellow-50 rounded-lg shrink-0">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-gray-900">Printability Check</h3>
                  <p className="text-xs text-gray-500 mt-1">Automated analysis for wall thickness & overhangs.</p>
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-gray-100 shadow-sm flex items-start gap-3">
                <div className="p-2 bg-blue-50 rounded-lg shrink-0">
                  <UploadCloud className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-gray-900">Direct to Print</h3>
                  <p className="text-xs text-gray-500 mt-1">Seamless integration with Bambu Lab printers.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Quote Panel (Spans 4 cols) */}
          <div className="lg:col-span-4">
            <div className="sticky top-24">
              <QuotePanel
                onFileSelect={handleFileSelect}
                onMaterialChange={(m, c) => { setMaterial(m); setColor(c); }}
                onQuantityChange={setQuantity}
                onPriceUpdate={setPrice}
                price={price}
                loading={analyzing}
                jobId={jobId}
              />
              
              <div className="mt-6 text-center text-xs text-gray-400">
                <p>Secure payment powered by Stripe</p>
                <p className="mt-1">© 2026 Web3DP Inc.</p>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default Home;
