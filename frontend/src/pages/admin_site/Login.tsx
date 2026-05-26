import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ADMIN_CREDS = { username: 'admin', password: 'adminpass' };
const TRAINER_CREDS = { username: 'trainer', password: 'trainerpass' };

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('admin');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    try {
      const res = await fetch('/backend/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Login failed');
      }
      
      const data = await res.json();
      const roles = data.roles || [];
      
      localStorage.setItem('access_token', data.access_token);
      
      if (roles.includes('admin') && role === 'admin') {
        localStorage.setItem('is_admin', '1');
        navigate('/admin-site/dashboard');
      } else if (roles.includes('trainer') && role === 'trainer') {
        if (data.user.status === 'Stalled') {
          setError('Account is currently stalled by admin');
          return;
        }
        localStorage.setItem('is_trainer', '1');
        navigate('/trainer-site/dashboard');
      } else {
        setError('Unauthorized role for this portal');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-teal-700 font-sans p-4">
      <div 
        className="w-full max-w-sm bg-[#c0c0c0] shadow-xl"
        style={{
          borderTop: '2px solid white',
          borderLeft: '2px solid white',
          borderRight: '2px solid #404040',
          borderBottom: '2px solid #404040'
        }}
      >
        {/* Classic Window Title Bar */}
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold text-sm">
          <span className="truncate pr-2">Admin/Trainer Login</span>
          <div className="flex space-x-1 shrink-0">
            <div className="w-4 h-4 bg-[#c0c0c0] border border-white border-r-gray-800 border-b-gray-800 flex items-center justify-center text-black font-bold cursor-default">
              <span className="mb-1">_</span>
            </div>
            <div className="w-4 h-4 bg-[#c0c0c0] border border-white border-r-gray-800 border-b-gray-800 flex items-center justify-center text-black font-bold cursor-default">
              <span>X</span>
            </div>
          </div>
        </div>

        {/* Window Content */}
        <div className="p-4 text-black text-sm">
          <form onSubmit={submit} className="space-y-4">
            
            <div className="flex items-center">
              <label className="w-24 shrink-0">Role:</label>
              <select 
                aria-label="role" 
                value={role} 
                onChange={(e) => setRole(e.target.value)} 
                className="flex-1 min-w-0 bg-white border border-gray-500 shadow-inner px-1 py-1"
              >
                <option value="admin">Admin</option>
                <option value="trainer">Trainer</option>
              </select>
            </div>

            <div className="flex items-center">
              <label className="w-24 shrink-0">Username:</label>
              <input 
                aria-label="username" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                className="flex-1 min-w-0 bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 px-1 py-1" 
              />
            </div>

            <div className="flex items-center">
              <label className="w-24 shrink-0">Password:</label>
              <input 
                aria-label="password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                className="flex-1 min-w-0 bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 px-1 py-1" 
              />
            </div>

            {error && <div className="text-red-700 font-bold text-center mt-2">{error}</div>}

            <div className="flex justify-end pt-2">
              <button 
                type="submit"
                className="w-full sm:w-auto px-6 py-1 bg-[#c0c0c0] text-black focus:outline-none focus:ring-1 focus:ring-black"
                style={{
                  borderTop: '2px solid white',
                  borderLeft: '2px solid white',
                  borderRight: '2px solid #404040',
                  borderBottom: '2px solid #404040'
                }}
                onMouseDown={(e) => {
                  e.currentTarget.style.borderTop = '2px solid #404040';
                  e.currentTarget.style.borderLeft = '2px solid #404040';
                  e.currentTarget.style.borderRight = '2px solid white';
                  e.currentTarget.style.borderBottom = '2px solid white';
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.borderTop = '2px solid white';
                  e.currentTarget.style.borderLeft = '2px solid white';
                  e.currentTarget.style.borderRight = '2px solid #404040';
                  e.currentTarget.style.borderBottom = '2px solid #404040';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderTop = '2px solid white';
                  e.currentTarget.style.borderLeft = '2px solid white';
                  e.currentTarget.style.borderRight = '2px solid #404040';
                  e.currentTarget.style.borderBottom = '2px solid #404040';
                }}
              >
                OK
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
