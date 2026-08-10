import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between p-6 min-h-screen shrink-0">
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🤖</span>
          <h1 className="text-base font-bold text-white tracking-tight">API Patching Agent</h1>
        </div>

        <nav className="space-y-1">
          <Link
            to="/"
            className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              location.pathname === '/'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:bg-slate-900 hover:text-white'
            }`}
          >
            <span>🚀</span>
            <span>New Repair Job</span>
          </Link>

          <Link
            to="/history"
            className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              location.pathname === '/history'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:bg-slate-900 hover:text-white'
            }`}
          >
            <span>📜</span>
            <span>Repair History</span>
          </Link>
        </nav>
      </div>

      <div className="border-t border-slate-800 pt-4 space-y-3">
        <div className="text-xs text-slate-400">
          Logged in as: <strong className="text-indigo-300 block text-sm font-semibold truncate">{user}</strong>
        </div>
        <button
          onClick={logout}
          className="w-full text-center bg-red-950/40 hover:bg-red-900/60 text-red-300 text-xs py-2 rounded-lg border border-red-800/50 transition-colors cursor-pointer"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}