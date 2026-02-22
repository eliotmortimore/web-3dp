import React, { useState, useEffect } from 'react';
import { Upload, DollarSign, Box, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';

interface QuotePanelProps {
  onFileSelect: (file: File) => void;
  onMaterialChange: (material: string, color: string) => void;
  onQuantityChange: (qty: number) => void;
  onPriceUpdate?: (price: number) => void;
  price: number | null;
  loading: boolean;
  jobId: number | null;
}

const MATERIALS = [
  { id: 'PLA', name: 'PLA Basic', pricePerG: 0.05, colors: [
    { name: 'Red', hex: '#ff0000' },
    { name: 'Blue', hex: '#0000ff' },
    { name: 'White', hex: '#ffffff' },
    { name: 'Black', hex: '#000000' },
  ]},
  { id: 'PETG', name: 'PETG Strong', pricePerG: 0.06, colors: [
    { name: 'Transparent', hex: '#cccccc' },
    { name: 'Black', hex: '#000000' },
  ]},
];

const QuotePanel: React.FC<QuotePanelProps> = ({
  onFileSelect,
  onMaterialChange,
  onQuantityChange,
  onPriceUpdate,
  price,
  loading,
  jobId
}) => {
  const { session } = useAuth();
  const [selectedMat, setSelectedMat] = useState(MATERIALS[0]);
  const [selectedColor, setSelectedColor] = useState(MATERIALS[0].colors[0]);
  const [qty, setQty] = useState(1);
  const [showSuccess, setShowSuccess] = useState(false);
  const [updating, setUpdating] = useState(false);

  // Debounced update for quantity/material changes
  useEffect(() => {
    if (!jobId) return;

    const timer = setTimeout(() => {
        updateJobDetails();
    }, 500);

    return () => clearTimeout(timer);
  }, [qty, selectedMat.id, selectedColor.name]);

  const updateJobDetails = async () => {
      if (!jobId) return;
      try {
          const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
          const res = await api.patch(`/api/v1/jobs/${jobId}`, {
              quantity: qty,
              material: selectedMat.id,
              color: selectedColor.name
          }, { headers });
          if (res.data.price !== undefined && onPriceUpdate) {
              onPriceUpdate(res.data.price);
          }
      } catch (err) {
          console.error("Failed to update job", err);
      }
  };

  const handleMatChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const mat = MATERIALS.find(m => m.id === e.target.value) || MATERIALS[0];
    setSelectedMat(mat);
    setSelectedColor(mat.colors[0]);
    onMaterialChange(mat.id, mat.colors[0].hex);
  };

  const handleColorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const color = selectedMat.colors.find(c => c.name === e.target.value) || selectedMat.colors[0];
    setSelectedColor(color);
    onMaterialChange(selectedMat.id, color.hex);
  };

  const handleQtyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value) || 1;
    setQty(val);
    onQuantityChange(val);
  };

  const handleAddToOrder = async () => {
    if (!jobId) return;
    
    setUpdating(true);
    try {
        const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
        await api.patch(`/api/v1/jobs/${jobId}`, {
            status: "PAID", // Simulating payment for now
            quantity: qty,
            material: selectedMat.id,
            color: selectedColor.name
        }, { headers });

        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 2000);
        alert("Order confirmed! (Simulated)");
    } catch (err) {
        console.error("Failed to add to order", err);
        alert("Failed to place order.");
    } finally {
        setUpdating(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Get Instant Quote</h2>
      
      {/* File Upload */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Upload STL</label>
        <div className="flex items-center justify-center w-full">
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <Upload className="w-8 h-8 mb-3 text-gray-400" />
              <p className="mb-2 text-sm text-gray-500"><span className="font-semibold">Click to upload</span> or drag and drop</p>
              <p className="text-xs text-gray-500">STL files only</p>
            </div>
            <input 
              type="file" 
              className="hidden" 
              accept=".stl" 
              onChange={(e) => e.target.files && onFileSelect(e.target.files[0])} 
            />
          </label>
        </div>
      </div>

      {/* Material Selection */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Material</label>
          <select 
            value={selectedMat.id} 
            onChange={handleMatChange}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            {MATERIALS.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
          <select 
            value={selectedColor.name} 
            onChange={handleColorChange}
            className="w-full p-2 border border-gray-300 rounded-md"
          >
            {selectedMat.colors.map(c => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Quantity */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Box className="h-5 w-5 text-gray-400" />
          </div>
          <input 
            type="number" 
            min="1" 
            value={qty} 
            onChange={handleQtyChange}
            className="pl-10 w-full p-2 border border-gray-300 rounded-md" 
          />
        </div>
      </div>

      {/* Price Display */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6 flex justify-between items-center">
        <span className="text-gray-600 font-medium">Estimated Cost:</span>
        <div className="text-3xl font-bold text-green-600 flex items-center">
          {loading ? (
            <span className="text-sm text-gray-400">Calculating...</span>
          ) : price ? (
            <><DollarSign className="w-6 h-6" />{price.toFixed(2)}</>
          ) : (
            <span className="text-gray-300">--</span>
          )}
        </div>
      </div>

      <button 
        onClick={handleAddToOrder}
        disabled={!price || showSuccess || updating || !jobId}
        className={`w-full py-3 px-4 rounded-md text-white font-bold transition-all duration-200 flex items-center justify-center gap-2
          ${price && !showSuccess && !updating ? 'bg-blue-600 hover:bg-blue-700 shadow-lg transform hover:-translate-y-0.5' : 'bg-gray-300 cursor-not-allowed'}
          ${showSuccess ? 'bg-green-500 hover:bg-green-600' : ''}`}
      >
        {showSuccess ? (
          <>
            <Check className="w-5 h-5" />
            Added to Order!
          </>
        ) : updating ? (
            "Updating..."
        ) : (
          "Add to Order"
        )}
      </button>
    </div>
  );
};

export default QuotePanel;
