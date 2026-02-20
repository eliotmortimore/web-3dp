import React, { useState, useEffect } from 'react';
import { X, Box, Info, Settings, Clock, Layers, Weight, DollarSign, Printer, Download } from 'lucide-react';
import axios from 'axios';
import ModelViewer from './ModelViewer';

interface JobDetailsProps {
  jobId: number | null;
  onClose: () => void;
}

interface JobDetails {
  id: number;
  filename: string;
  status: string;
  slice_status: string;
  price: number;
  quantity: number;
  material: string;
  created_at: string;
  volume_cm3?: number;
  weight_g?: number;
  print_time_seconds?: number;
  sliced_file_path?: string;
  metadata?: {
    slice_info?: Record<string, string>;
    project_settings?: Record<string, string>;
  };
}

const JobDetailsModal = ({ jobId, onClose }: JobDetailsProps) => {
  const [job, setJob] = useState<JobDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'stl' | '3mf'>('stl');

  useEffect(() => {
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId]);

  const fetchJobDetails = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/jobs/${jobId}/details`);
      setJob(res.data);
      // Default to 3mf if available and sliced
      if (res.data.slice_status === 'COMPLETED') {
        setViewMode('3mf');
      }
    } catch (err) {
      console.error("Failed to fetch job details", err);
    } finally {
      setLoading(false);
    }
  };

  if (!jobId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-7xl h-[95vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-white z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Box className="w-5 h-5 text-blue-600" />
              Order #{jobId}
            </h2>
            <p className="text-sm text-gray-500 mt-1">{job?.filename || 'Loading...'}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : !job ? (
             <div className="text-center text-gray-500">Failed to load job details.</div>
          ) : (
            <div className="flex flex-col gap-6">
              
              {/* Top Section: Overview & 3D Model */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Left Column: Overview */}
                <div className="space-y-6">
                  {/* Status Card */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Info className="w-4 h-4" /> Status & Pricing
                    </h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="text-gray-600 font-medium">Order Status</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-sm font-bold">{job.status}</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="text-gray-600 font-medium">Slicing Status</span>
                        <span className={`px-2 py-1 rounded-md text-sm font-bold 
                          ${job.slice_status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                          {job.slice_status}
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border-l-4 border-green-500">
                        <span className="text-gray-900 font-bold">Total Price</span>
                        <span className="text-xl font-bold text-green-600">${job.price}</span>
                      </div>
                    </div>
                  </div>

                  {/* Physical Properties */}
                  <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Layers className="w-4 h-4" /> Physical Properties
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-gray-50 rounded-lg text-center">
                        <div className="flex justify-center text-blue-500 mb-2">
                           <Weight className="w-6 h-6" />
                        </div>
                        <div className="text-xs text-gray-500 uppercase font-semibold">Weight</div>
                        <p className="text-lg font-bold text-gray-900">{job.weight_g}g</p>
                      </div>
                      <div className="p-4 bg-gray-50 rounded-lg text-center">
                        <div className="flex justify-center text-blue-500 mb-2">
                           <Clock className="w-6 h-6" />
                        </div>
                        <div className="text-xs text-gray-500 uppercase font-semibold">Print Time</div>
                        <p className="text-lg font-bold text-gray-900">
                          {job.print_time_seconds ? `${Math.floor(job.print_time_seconds / 60)}m` : 'N/A'}
                        </p>
                      </div>
                      <div className="p-4 bg-gray-50 rounded-lg text-center">
                         <div className="flex justify-center text-blue-500 mb-2">
                           <Layers className="w-6 h-6" />
                        </div>
                        <div className="text-xs text-gray-500 uppercase font-semibold">Material</div>
                        <p className="text-lg font-bold text-gray-900">{job.material}</p>
                      </div>
                      <div className="p-4 bg-gray-50 rounded-lg text-center">
                         <div className="flex justify-center text-blue-500 mb-2">
                           <Box className="w-6 h-6" />
                        </div>
                        <div className="text-xs text-gray-500 uppercase font-semibold">Volume</div>
                        <p className="text-lg font-bold text-gray-900">{job.volume_cm3?.toFixed(2)} cm³</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column: 3D Model */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 flex flex-col h-[500px] lg:h-auto overflow-hidden">
                   <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider flex items-center gap-2">
                        <Box className="w-4 h-4" /> 3D Preview
                      </h3>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => setViewMode('stl')}
                          className={`px-3 py-1 text-xs font-medium rounded-md border transition-colors
                            ${viewMode === 'stl' ? 'bg-white border-blue-500 text-blue-600 shadow-sm' : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200'}`}
                        >
                          STL
                        </button>
                        <button 
                          onClick={() => setViewMode('3mf')}
                          disabled={!job.sliced_file_path}
                          className={`px-3 py-1 text-xs font-medium rounded-md border transition-colors
                            ${viewMode === '3mf' ? 'bg-white border-blue-500 text-blue-600 shadow-sm' : 'bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200'}
                            ${!job.sliced_file_path ? 'opacity-50 cursor-not-allowed' : ''}
                          `}
                        >
                          Sliced 3MF
                        </button>
                      </div>
                   </div>
                   <div className="flex-1 bg-gray-900 relative">
                      {viewMode === 'stl' ? (
                         <ModelViewer url={`http://localhost:8000/uploads/${job.filename}`} type="stl" />
                      ) : (
                         job.sliced_file_path && <ModelViewer url={`http://localhost:8000/uploads/${job.sliced_file_path}`} type="3mf" />
                      )}
                      
                      <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-md text-white px-3 py-1.5 rounded-full text-xs font-mono pointer-events-none border border-white/10">
                         {viewMode === 'stl' ? job.filename : job.sliced_file_path}
                      </div>
                   </div>
                </div>

              </div>

              {/* Bottom Section: Slicer Data */}
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2 border-b pb-2">
                  <Settings className="w-5 h-5 text-gray-500" /> 
                  Print Configuration
                </h3>

                 {job.metadata?.slice_info ? (
                   <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                     <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                       <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">Slicer Settings</h4>
                       <span className="text-xs text-gray-400 font-mono">Source: Metadata/slice_info.config</span>
                     </div>
                     <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-gray-100">
                       {Object.entries(job.metadata.slice_info).map(([key, value]) => (
                         <div key={key} className="bg-white p-4 hover:bg-gray-50 transition-colors">
                           <dt className="text-xs font-bold text-gray-400 uppercase mb-1 tracking-wider">{key.replace(/_/g, ' ')}</dt>
                           <dd className="text-sm font-medium text-gray-900 break-words">{value}</dd>
                         </div>
                       ))}
                     </div>
                   </div>
                 ) : (
                   <div className="p-8 text-center text-gray-500 bg-white rounded-lg border border-dashed border-gray-300">
                     No slicer metadata available. Slicing might be pending or failed.
                   </div>
                 )}
                 
                 {job.metadata?.project_settings && (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                        <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">Project Info</h4>
                        <span className="text-xs text-gray-400 font-mono">Source: Metadata/project_settings.config</span>
                      </div>
                       <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-gray-100">
                         {Object.entries(job.metadata.project_settings).map(([key, value]) => (
                           <div key={key} className="bg-white p-4 hover:bg-gray-50 transition-colors">
                             <dt className="text-xs font-bold text-gray-400 uppercase mb-1 tracking-wider">{key.replace(/_/g, ' ')}</dt>
                             <dd className="text-sm font-medium text-gray-900 break-words">{value}</dd>
                           </div>
                         ))}
                       </div>
                    </div>
                 )}
              </div>

            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-gray-100 bg-white flex justify-end gap-3 z-10">
          <button onClick={onClose} className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 shadow-sm transition-all">
            Close
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 shadow-md hover:shadow-lg transition-all flex items-center gap-2">
            <Printer className="w-4 h-4" />
            Start Print Job
          </button>
        </div>
      </div>
    </div>
  );
};

export default JobDetailsModal;
