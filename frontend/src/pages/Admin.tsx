import React, { useState, useEffect, useRef } from 'react';
import { Play, Check, AlertCircle, Clock, RefreshCw, LayoutDashboard, List, Package, Truck, Settings, ChevronDown, Printer, Ban, PauseCircle } from 'lucide-react';
import axios from 'axios';
import JobDetailsModal from '../components/JobDetailsModal';

interface Job {
  id: number;
  filename: string;
  status: 'PENDING' | 'PAID' | 'SLICING' | 'PRINTING' | 'DONE';
  price: number;
  quantity: number;
  customer?: string;
  material: string;
  created_at: string;
}

import { useAuth } from '../context/AuthContext';

const Admin = () => {
  const { session, loading: authLoading } = useAuth();
  console.log("Admin Render - Session:", session, "Loading:", authLoading);

  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeTab, setActiveTab] = useState('jobs');
  const [processing, setProcessing] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [dropdownOpen, setDropdownOpen] = useState<number | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      if (!session?.access_token) return;
      const res = await axios.get('http://localhost:8000/api/v1/jobs', {
          headers: { Authorization: `Bearer ${session.access_token}` }
      });
      setJobs(res.data);
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (session) {
        fetchJobs();
        const interval = setInterval(fetchJobs, 5000); 
        return () => clearInterval(interval);
    }
  }, [session]);

  // ... (rest of useEffects)

  const handleAction = async (id: number, action: 'print' | 'reject' | 'pause') => {
    setProcessing(id);
    setDropdownOpen(null); // Close dropdown
    
    try {
      if (!session?.access_token) return;
      const headers = { Authorization: `Bearer ${session.access_token}` };
      
      if (action === 'print') {
        await axios.post(`http://localhost:8000/api/v1/jobs/${id}/approve`, {}, { headers });
      } else {
        // Placeholder for other actions
        console.log(`Action ${action} triggered for job ${id}`);
        // await axios.post(`http://localhost:8000/api/v1/jobs/${id}/${action}`, {}, { headers });
      }
      fetchJobs(); 
    } catch (err) {
      alert(`Failed to ${action} job`);
    } finally {
      setProcessing(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PAID': return 'bg-green-100 text-green-800';
      case 'PRINTING': return 'bg-blue-100 text-blue-800';
      case 'SLICING': return 'bg-yellow-100 text-yellow-800';
      case 'DONE': return 'bg-gray-100 text-gray-800';
      case 'PENDING': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-50 text-gray-500';
    }
  };

  const renderContent = () => {
    switch(activeTab) {
      case 'dashboard':
        return (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Active Jobs</h3>
              <p className="text-3xl font-bold mt-2">{jobs.filter(j => j.status !== 'DONE').length}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Revenue (Today)</h3>
              <p className="text-3xl font-bold mt-2 text-green-600">$124.50</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm font-medium">Printers Online</h3>
              <p className="text-3xl font-bold mt-2 text-blue-600">2 / 3</p>
            </div>
          </div>
        );
      case 'jobs':
        return (
          <div className="bg-white rounded-lg shadow overflow-hidden min-h-[500px]">
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
              <h2 className="font-semibold text-gray-700">All Jobs</h2>
              <button onClick={fetchJobs} className="p-2 hover:bg-gray-100 rounded-full">
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr 
                    key={job.id} 
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={(e) => {
                      // Prevent modal opening when clicking action buttons
                      if ((e.target as HTMLElement).closest('button')) return;
                      setSelectedJobId(job.id);
                    }}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{job.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">{job.filename}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(job.created_at).toLocaleDateString()} <span className="text-xs text-gray-400">{new Date(job.created_at).toLocaleTimeString()}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs">{job.material}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold">{job.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">${job.price}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium relative">
                      {(job.status === 'PENDING' || job.status === 'PAID') && (
                        <div className="relative inline-block text-left">
                          <div className="flex items-center">
                            <button
                              onClick={() => setDropdownOpen(dropdownOpen === job.id ? null : job.id)}
                              disabled={processing === job.id}
                              className={`inline-flex items-center justify-between px-3 py-1.5 w-40 border border-transparent text-xs font-medium rounded-md shadow-sm text-white 
                                ${processing === job.id ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
                            >
                              <span className="flex items-center">
                                {processing === job.id ? <Clock className="w-4 h-4 animate-spin mr-2" /> : <Printer className="w-4 h-4 mr-2" />}
                                Send to Printer
                              </span>
                              <ChevronDown className="w-3 h-3 ml-1" />
                            </button>
                          </div>

                          {/* Dropdown Menu */}
                          {dropdownOpen === job.id && (
                            <div 
                              ref={dropdownRef}
                              className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50 focus:outline-none"
                            >
                              <div className="py-1">
                                <button
                                  onClick={() => handleAction(job.id, 'print')}
                                  className="group flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                                >
                                  <Printer className="mr-3 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
                                  Send to Printer
                                </button>
                                <button
                                  onClick={() => handleAction(job.id, 'pause')}
                                  className="group flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                                >
                                  <PauseCircle className="mr-3 h-4 w-4 text-gray-400 group-hover:text-gray-500" />
                                  Pause
                                </button>
                                <button
                                  onClick={() => handleAction(job.id, 'reject')}
                                  className="group flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 hover:text-red-900"
                                >
                                  <Ban className="mr-3 h-4 w-4 text-red-500 group-hover:text-red-600" />
                                  Reject
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      case 'filament':
        return <div className="p-12 text-center text-gray-400">Filament Management Coming Soon</div>;
      case 'shipping':
        return <div className="p-12 text-center text-gray-400">Shipping Integration Coming Soon</div>;
      case 'settings':
        return <div className="p-12 text-center text-gray-400">System Settings Coming Soon</div>;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg fixed h-full z-10">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-bold text-gray-900">Web3DP Admin</h1>
        </div>
        <nav className="mt-6 px-4 space-y-2">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
            { id: 'jobs', label: 'Jobs', icon: List },
            { id: 'filament', label: 'Filament', icon: Package },
            { id: 'shipping', label: 'Shipping', icon: Truck },
            { id: 'settings', label: 'Settings', icon: Settings },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors
                ${activeTab === item.id ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 ml-64 p-8">
        {renderContent()}
      </div>

      {/* Details Modal */}
      {selectedJobId && (
        <JobDetailsModal 
          jobId={selectedJobId} 
          onClose={() => setSelectedJobId(null)} 
        />
      )}
    </div>
  );
};

export default Admin;
