import React, { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';

export default function TrainerDashboard(){
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [jobs, setJobs] = useState<any[]>([]);
  const navigate = useNavigate();

  const isTrainer = localStorage.getItem('is_trainer') === '1';

  const fetchJobs = async () => {
    if (!isTrainer) return;
    try {
      const res = await fetch('/api/ml_pipeline/jobs');
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
      }
    } catch (e) {
      console.error('Failed to fetch jobs');
    }
  };

  useEffect(() => {
    if (!isTrainer) return;
    fetchJobs();
    const interval = setInterval(fetchJobs, 2000);
    return () => clearInterval(interval);
  }, [isTrainer]);

  if (!isTrainer) {
    return <Navigate to="/" replace />;
  }

  const upload = async () => {
    if (!file) return setMessage('Select a file');
    const form = new FormData();
    form.append('dataset_file', file);
    setMessage('Uploading...');
    try{
      const res = await fetch('/api/ml_pipeline/fine-tune', { method: 'POST', body: form, credentials: 'include' });
      if(!res.ok) throw new Error('upload failed');
      const data = await res.json();
      setMessage('Job enqueued: ' + (data.job_id || ''));
      fetchJobs();
    }catch(e){
      setMessage('Failed to enqueue');
    }
  };

  const buttonStyle = {
    borderTop: '2px solid white',
    borderLeft: '2px solid white',
    borderRight: '2px solid #404040',
    borderBottom: '2px solid #404040'
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.borderTop = '2px solid #404040';
    e.currentTarget.style.borderLeft = '2px solid #404040';
    e.currentTarget.style.borderRight = '2px solid white';
    e.currentTarget.style.borderBottom = '2px solid white';
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.borderTop = '2px solid white';
    e.currentTarget.style.borderLeft = '2px solid white';
    e.currentTarget.style.borderRight = '2px solid #404040';
    e.currentTarget.style.borderBottom = '2px solid #404040';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-teal-700 font-sans p-4">
      <div 
        className="w-full max-w-3xl bg-[#c0c0c0] shadow-xl"
        style={{
          borderTop: '2px solid white',
          borderLeft: '2px solid white',
          borderRight: '2px solid #404040',
          borderBottom: '2px solid #404040'
        }}
      >
        {/* Classic Window Title Bar */}
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold text-sm">
          <span>Trainer Console</span>
          <div className="flex space-x-1">
            <button 
              onClick={() => {
                localStorage.removeItem('is_trainer');
                navigate('/');
              }} 
              className="px-2 h-4 bg-[#c0c0c0] border border-white border-r-gray-800 border-b-gray-800 flex items-center justify-center text-black font-bold focus:outline-none text-xs"
            >
              Logout
            </button>
            <button onClick={() => navigate('/')} className="w-4 h-4 bg-[#c0c0c0] border border-white border-r-gray-800 border-b-gray-800 flex items-center justify-center text-black font-bold focus:outline-none">
              <span>X</span>
            </button>
          </div>
        </div>

        {/* Window Content */}
        <div className="p-4 text-black text-sm space-y-6">
          
          {/* Upload Section */}
          <div 
            className="p-3"
            style={{
              borderTop: '2px solid #404040',
              borderLeft: '2px solid #404040',
              borderRight: '2px solid white',
              borderBottom: '2px solid white'
            }}
          >
            <h2 className="font-bold mb-3">Upload Dataset</h2>
            <p className="mb-2 text-gray-700">Upload dataset (JSON array of {"{text, label}"})</p>
            <div className="flex items-center space-x-4">
              <input 
                type="file" 
                aria-label="dataset-file" 
                accept="application/json" 
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 px-1 py-1"
              />
              <button 
                onClick={upload}
                className="px-4 py-1 bg-[#c0c0c0] text-black focus:outline-none"
                style={buttonStyle}
                onMouseDown={handleMouseDown} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
              >
                Upload & Train
              </button>
            </div>
            {message && <div className="mt-3 font-bold text-blue-800">{message}</div>}
          </div>

          {/* Jobs List Section */}
          <div 
            className="p-3"
            style={{
              borderTop: '2px solid #404040',
              borderLeft: '2px solid #404040',
              borderRight: '2px solid white',
              borderBottom: '2px solid white'
            }}
          >
            <h2 className="font-bold mb-3">Training Jobs & Metrics</h2>
            <div className="bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 h-64 overflow-y-auto p-1">
              {jobs.length === 0 ? (
                <div className="text-gray-500 p-2">No training jobs found.</div>
              ) : (
                <div className="space-y-4">
                  {jobs.map(job => (
                    <div key={job.job_id} className="p-2 border border-gray-400 bg-gray-50">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold">Job: {job.job_id.substring(0,8)}...</span>
                        <span className={`font-bold ${job.status === 'completed' ? 'text-green-700' : job.status === 'failed' ? 'text-red-700' : 'text-blue-700'}`}>
                          {job.status.toUpperCase()}
                        </span>
                      </div>
                      
                      {/* Progress Bar */}
                      <div className="w-full bg-gray-300 h-4 border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 relative">
                        <div 
                          className="h-full bg-blue-800"
                          style={{ width: `${job.progress}%` }}
                        ></div>
                        <div className="absolute inset-0 flex justify-center items-center text-[10px] font-bold text-white mix-blend-difference">
                          {job.progress}%
                        </div>
                      </div>

                      {/* Metrics Display */}
                      {job.result && job.status === 'completed' && (
                        <div className="mt-2 text-xs bg-black text-green-400 p-2 font-mono">
                          <div><span className="text-white">Validation Loss:</span> {job.result.metrics?.eval_loss || job.result.metrics?.loss || 'N/A'}</div>
                          <div><span className="text-white">Model Saved:</span> {job.result.model_path || 'N/A'}</div>
                        </div>
                      )}
                      
                      {job.result && job.status === 'failed' && (
                        <div className="mt-2 text-xs text-red-600 font-bold">
                          Error: {job.result.error || 'Unknown error occurred'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
