import React, { useState, useEffect } from 'react';
import { Play, Check, AlertCircle, Clock, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface Job {
  id: number;
  filename: string;
  status: 'PENDING' | 'PAID' | 'SLICING' | 'PRINTING' | 'DONE';
  price: number;
  customer?: string;
  material: string;
  created_at: string;
}

const Admin = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [processing, setProcessing] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/api/v1/jobs');
      setJobs(res.data);
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (id: number) => {
    setProcessing(id);
    try {
      await axios.post(`http://localhost:8000/api/v1/jobs/${id}/approve`);
      fetchJobs(); // Refresh list
    } catch (err) {
      console.error("Failed to approve job", err);
      alert("Failed to approve job");
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

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Print Queue Dashboard</h1>
            <button onClick={fetchJobs} className="p-2 bg-white border rounded shadow hover:bg-gray-50">
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
        </div>
        
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Material</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {jobs.length === 0 ? (
                  <tr>
                      <td colSpan={7} className="px-6 py-12 text-center text-gray-400">
                          No active jobs found. Upload a file to start!
                      </td>
                  </tr>
              ) : jobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{job.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{job.filename}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(job.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{job.material}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-700">${job.price}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {/* Allow approving pending jobs for demo purposes */}
                    {(job.status === 'PENDING' || job.status === 'PAID') && (
                      <button 
                        onClick={() => handleApprove(job.id)}
                        disabled={processing === job.id}
                        className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white 
                          ${processing === job.id ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
                      >
                        {processing === job.id ? (
                          <Clock className="w-4 h-4 animate-spin mr-1" />
                        ) : (
                          <Play className="w-4 h-4 mr-1" />
                        )}
                        {processing === job.id ? 'Starting...' : 'Approve & Print'}
                      </button>
                    )}
                    {job.status === 'PRINTING' && (
                      <span className="text-blue-600 flex items-center justify-end gap-1">
                        <Clock className="w-4 h-4" /> Printing...
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Admin;
