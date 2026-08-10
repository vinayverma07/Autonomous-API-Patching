import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <aside className="w-64 bg-white/80 backdrop-blur-xl border-r border-purple-100 flex flex-col justify-between p-6 min-h-screen shrink-0 shadow-xl shadow-purple-500/5">
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">🤖</span>
          <h1 className="text-base font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-900 via-indigo-800 to-purple-900 tracking-tight">
            API Patching Agent
          </h1>
        </div>

        <nav className="space-y-1.5">
          <Link
            to="/"
            className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              location.pathname === '/'
                ? 'bg-purple-100/80 text-purple-900 border border-purple-200/80 shadow-sm'
                : 'text-slate-600 hover:bg-purple-50/80 hover:text-purple-900'
            }`}
          >
            <span>🚀</span>
            <span>New Repair Job</span>
          </Link>

          <Link
            to="/history"
            className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              location.pathname === '/history'
                ? 'bg-purple-100/80 text-purple-900 border border-purple-200/80 shadow-sm'
                : 'text-slate-600 hover:bg-purple-50/80 hover:text-purple-900'
            }`}
          >
            <span>📜</span>
            <span>Repair History</span>
          </Link>
        </nav>
      </div>

      <div className="border-t border-purple-100 pt-4 space-y-3">
        <div className="text-xs text-slate-500">
          
          <strong className="text-purple-900 block text-sm font-semibold truncate mt-0.5">
            Logged in as{' '}:{' '}{user}
          </strong>
        </div>
        <button
          onClick={logout}
          className="w-full text-center bg-red-50 hover:bg-red-100/80 text-red-600 text-xs py-2 rounded-xl border border-red-200/80 font-semibold transition-all cursor-pointer"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}