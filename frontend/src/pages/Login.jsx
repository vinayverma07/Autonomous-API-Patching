import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API from '../api';

export default function Login() {
  const [formData, setFormData] = useState({ username_or_email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError('');
//     setLoading(true);

//     try {
//       const res = await API.post('/api/auth/login', formData);
//       login(res.data.access_token, formData.username_or_email);
//       navigate('/');
//     } catch (err) {
//       setError(err.response?.data?.detail || 'Invalid username or password.');
//     } finally {
//       setLoading(false);
//     }
//   };

const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setLoading(true);

  try {
    const res = await API.post('/api/auth/login', formData);
    // 👇 Use res.data.username returned from backend!
    login(res.data.access_token, res.data.username); 
    navigate('/');
  } catch (err) {
    setError(err.response?.data?.detail || 'Invalid username or password.');
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center font-sans">
      <div className="bg-slate-800 border border-slate-700 p-8 rounded-xl shadow-2xl w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6 text-white">🔐 Welcome Back</h2>

        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700 text-red-300 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Username or Email</label>
            <input
              type="text"
              required
              value={formData.username_or_email}
              onChange={(e) => setFormData({ ...formData, username_or_email: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Password</label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-slate-400 mt-6">
          Don't have an account? <Link to="/register" className="text-indigo-400 hover:underline">Register here</Link>
        </p>
      </div>
    </div>
  );
}