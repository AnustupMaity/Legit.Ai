import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Trainer {
  id: string;
  username: string;
  password?: string;
  status: 'Active' | 'Stalled';
}

export default function AdminDashboard() {
  const [trainers, setTrainers] = useState<Trainer[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editUsername, setEditUsername] = useState('');
  const [editPassword, setEditPassword] = useState('');

  const navigate = useNavigate();

  const fetchTrainers = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch('/backend/trainers', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTrainers(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (localStorage.getItem('is_admin') !== '1') {
      navigate('/');
      return;
    }
    fetchTrainers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername || !newPassword) return;
    
    const token = localStorage.getItem('access_token');
    try {
      await fetch('/backend/trainers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ username: newUsername, password: newPassword })
      });
      setNewUsername('');
      setNewPassword('');
      fetchTrainers();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemove = async (id: string) => {
    const token = localStorage.getItem('access_token');
    try {
      await fetch(`/backend/trainers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchTrainers();
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleStall = async (t: Trainer) => {
    const token = localStorage.getItem('access_token');
    const newStatus = t.status === 'Active' ? false : true;
    try {
      await fetch(`/backend/trainers/${t.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ active: newStatus })
      });
      fetchTrainers();
    } catch (e) {
      console.error(e);
    }
  };

  const startEdit = (t: Trainer) => {
    setEditingId(t.id);
    setEditUsername(t.username);
    setEditPassword(''); // Password is not returned by API
  };

  const saveEdit = async () => {
    if (!editingId) return;
    const token = localStorage.getItem('access_token');
    const body: any = {};
    if (editUsername) body.username = editUsername;
    if (editPassword) body.password = editPassword;
    
    try {
      await fetch(`/backend/trainers/${editingId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(body)
      });
      setEditingId(null);
      fetchTrainers();
    } catch (e) {
      console.error(e);
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
        className="w-full max-w-2xl bg-[#c0c0c0] shadow-xl"
        style={{
          borderTop: '2px solid white',
          borderLeft: '2px solid white',
          borderRight: '2px solid #404040',
          borderBottom: '2px solid #404040'
        }}
      >
        {/* Classic Window Title Bar */}
        <div className="bg-[#000080] text-white px-2 py-1 flex justify-between items-center font-bold text-sm">
          <span className="truncate pr-2">Admin Console</span>
          <div className="flex space-x-1 shrink-0">
            <button 
              onClick={() => {
                localStorage.removeItem('is_admin');
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
          
          {/* Create Trainer Section */}
          <div 
            className="p-3"
            style={{
              borderTop: '2px solid #404040',
              borderLeft: '2px solid #404040',
              borderRight: '2px solid white',
              borderBottom: '2px solid white'
            }}
          >
            <h2 className="font-bold mb-3">Create New Trainer</h2>
            <form onSubmit={handleCreate} className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-end gap-4">
              <div className="flex flex-col w-full sm:w-auto sm:flex-1">
                <label className="mb-1">User ID / Username:</label>
                <input 
                  value={newUsername}
                  onChange={e => setNewUsername(e.target.value)}
                  className="bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 px-2 py-1 w-full"
                  required
                />
              </div>
              <div className="flex flex-col w-full sm:w-auto sm:flex-1">
                <label className="mb-1">Password:</label>
                <input 
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className="bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 px-2 py-1 w-full"
                  required
                />
              </div>
              <button 
                type="submit"
                className="px-4 py-1 bg-[#c0c0c0] text-black focus:outline-none w-full sm:w-auto mt-2 sm:mt-0"
                style={buttonStyle}
                onMouseDown={handleMouseDown}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                Create Trainer
              </button>
            </form>
          </div>

          {/* Trainers List Section */}
          <div 
            className="p-3"
            style={{
              borderTop: '2px solid #404040',
              borderLeft: '2px solid #404040',
              borderRight: '2px solid white',
              borderBottom: '2px solid white'
            }}
          >
            <h2 className="font-bold mb-3">Trainer Management</h2>
            <div className="bg-white border-t-gray-500 border-l-gray-500 border-b-white border-r-white border-2 h-48 overflow-auto p-1">
              {trainers.length === 0 ? (
                <div className="text-gray-500 p-2">No trainers found.</div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead className="bg-[#c0c0c0]">
                    <tr>
                      <th className="border border-gray-400 px-2 py-1 font-normal" style={buttonStyle}>Username</th>
                      <th className="border border-gray-400 px-2 py-1 font-normal" style={buttonStyle}>Password</th>
                      <th className="border border-gray-400 px-2 py-1 font-normal" style={buttonStyle}>Status</th>
                      <th className="border border-gray-400 px-2 py-1 font-normal" style={buttonStyle}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trainers.map((t, idx) => {
                      const isEditing = editingId === t.id;
                      return (
                        <tr key={t.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-100'}>
                          <td className="px-2 py-1">
                            {isEditing ? (
                              <input 
                                value={editUsername} 
                                onChange={e => setEditUsername(e.target.value)} 
                                className="border border-gray-500 px-1 w-full"
                              />
                            ) : (
                              t.username
                            )}
                          </td>
                          <td className="px-2 py-1">
                            {isEditing ? (
                              <input 
                                type="text"
                                value={editPassword} 
                                onChange={e => setEditPassword(e.target.value)} 
                                className="border border-gray-500 px-1 w-full"
                              />
                            ) : (
                              t.password ? '••••••••' : 'N/A'
                            )}
                          </td>
                          <td className="px-2 py-1">
                            <span className={t.status === 'Active' ? 'text-green-700' : 'text-red-700'}>
                              {t.status}
                            </span>
                          </td>
                          <td className="px-2 py-1 space-x-1 whitespace-nowrap">
                            {isEditing ? (
                              <>
                                <button 
                                  onClick={saveEdit}
                                  className="px-2 py-0.5 bg-[#c0c0c0] text-black text-xs focus:outline-none"
                                  style={buttonStyle}
                                  onMouseDown={handleMouseDown} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
                                >
                                  Save
                                </button>
                                <button 
                                  onClick={() => setEditingId(null)}
                                  className="px-2 py-0.5 bg-[#c0c0c0] text-black text-xs focus:outline-none"
                                  style={buttonStyle}
                                  onMouseDown={handleMouseDown} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
                                >
                                  Cancel
                                </button>
                              </>
                            ) : (
                              <>
                                <button 
                                  onClick={() => startEdit(t)}
                                  className="px-2 py-0.5 bg-[#c0c0c0] text-black text-xs focus:outline-none"
                                  style={buttonStyle}
                                  onMouseDown={handleMouseDown} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
                                >
                                  Edit
                                </button>
                                <button 
                                  onClick={() => handleToggleStall(t)}
                                  className="px-2 py-0.5 bg-[#c0c0c0] text-black text-xs focus:outline-none"
                                  style={buttonStyle}
                                  onMouseDown={handleMouseDown} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
                                >
                                  {t.status === 'Active' ? 'Stall' : 'Unstall'}
                                </button>
                                <button 
                                  onClick={() => handleRemove(t.id)}
                                  className="px-2 py-0.5 bg-[#c0c0c0] text-black text-xs focus:outline-none"
                                  style={buttonStyle}
                                  onMouseDown={handleMouseDown} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
                                >
                                  Remove
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
