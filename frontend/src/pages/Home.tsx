import React, { useState, useEffect } from 'react';
import Viewer3D from '../components/Viewer3D';
import QuotePanel from '../components/QuotePanel';
import { UploadCloud, CheckCircle, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

// Main Home Component
function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [material, setMaterial] = useState<string>('PLA');
  const [color, setColor] = useState<string>('#ff0000');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [volume, setVolume] = useState<number | null>(null);

  // Handle File Selection (Upload)
  const handleFileSelect = async (selectedFile: File) => {
    if (selectedFile) {
      setFile(selectedFile);
      
      // Create Object URL for local preview
      const url = URL.createObjectURL(selectedFile);
      setFileUrl(url);
      
      // Upload to Backend to calculate Volume
      setLoading(true);
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const res = await axios.post('http://localhost:8000/api/v1/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        setVolume(res.data.volume_cm3);
      } catch (err) {
          console.error("Upload failed", err);
          alert("Failed to analyze file");
      } finally {
          setLoading(false);
      }
    }
  };

  // Calculate Price whenever dependencies change
  useEffect(() => {
    const fetchQuote = async () => {
        if (volume && material && quantity && file) {
            setLoading(true);
            try {
                // Call Quote Endpoint (which also saves the Job to DB as PENDING)
                const res = await axios.post('http://localhost:8000/api/v1/quote', {
                    filename: file.name,
                    material: material,
                    quantity: quantity
                });
                setPrice(res.data.total_cost);
            } catch (err) {
                console.error("Quote failed", err);
            } finally {
                setLoading(false);
            }
        }
    };

    // Debounce calls to avoid spamming while typing quantity
    const timeoutId = setTimeout(() => {
        fetchQuote();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [volume, material, quantity, file]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
      
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <UploadCloud className="w-6 h-6 text-blue-600" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">Web3DP</h1>
          </div>
          <nav className="hidden md:flex gap-8 text-sm font-medium">
            <Link to="/" className="text-gray-900 hover:text-blue-600 transition-colors">Order Now</Link>
            <Link to="#" className="text-gray-500 hover:text-gray-900 transition-colors">My Prints</Link>
            <Link to="/admin" className="text-gray-500 hover:text-gray-900 transition-colors">Admin</Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">
          
          {/* Left Column: 3D Viewer (Spans 8 cols) */}
          <div className="lg:col-span-8 space-y-6 flex flex-col">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-1 flex-grow flex flex-col min-h-[500px]">
              <div className="flex justify-between items-center px-4 py-3 border-b border-gray-50">
                <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  3D Preview
                </h2>
                {volume && (
                  <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    Vol: {volume} cm³
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
                  <h3 className="font-semibold text-sm text-gray-900">Instant Quote</h3>
                  <p className="text-xs text-gray-500 mt-1">Get accurate pricing in seconds based on volume.</p>
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
                price={price}
                loading={loading}
              />
              
              <div className="mt-6 text-center text-xs text-gray-400">
                <p>Secure payment powered by Stripe</p>
                <p className="mt-1">© 2024 Web3DP Inc.</p>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default Home;
