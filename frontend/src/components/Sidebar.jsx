// import { Link, useLocation } from 'react-router-dom';
// import { useAuth } from '../context/AuthContext';

// export default function Sidebar() {
//   const { user, logout } = useAuth();
//   const location = useLocation();

//   return (
//     <aside className="w-64 bg-white/80 backdrop-blur-xl border-r border-purple-100 flex flex-col justify-between p-6 min-h-screen shrink-0 shadow-xl shadow-purple-500/5">
//       <div className="space-y-6">
//         <div className="flex items-center space-x-3">
//           <span className="text-2xl">🤖</span>
//           <h1 className="text-base font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-900 via-indigo-800 to-purple-900 tracking-tight">
//             API Patching Agent
//           </h1>
//         </div>

//         <nav className="space-y-1.5">
//           <Link
//             to="/"
//             className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
//               location.pathname === '/'
//                 ? 'bg-purple-100/80 text-purple-900 border border-purple-200/80 shadow-sm'
//                 : 'text-slate-600 hover:bg-purple-50/80 hover:text-purple-900'
//             }`}
//           >
//             <span>🚀</span>
//             <span>New Repair Job</span>
//           </Link>

//           <Link
//             to="/history"
//             className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
//               location.pathname === '/history'
//                 ? 'bg-purple-100/80 text-purple-900 border border-purple-200/80 shadow-sm'
//                 : 'text-slate-600 hover:bg-purple-50/80 hover:text-purple-900'
//             }`}
//           >
//             <span>📜</span>
//             <span>Repair History</span>
//           </Link>
//         </nav>
//       </div>

//       <div className="border-t border-purple-100 pt-4 space-y-3">
//         <div className="text-xs text-slate-500">
          
//           <strong className="text-purple-900 block text-sm font-semibold truncate mt-0.5">
//             Logged in as{' '}:{' '}{user}
//           </strong>
//         </div>
//         <button
//           onClick={logout}
//           className="w-full text-center bg-red-50 hover:bg-red-100/80 text-red-600 text-xs py-2 rounded-xl border border-red-200/80 font-semibold transition-all cursor-pointer"
//         >
//           Sign Out
//         </button>
//       </div>
//     </aside>
//   );
// }


import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Close mobile sidebar automatically when route changes
  useEffect(() => {
    setIsMobileOpen(false);
  }, [location.pathname]);

  return (
    <>
      {/* Mobile Top Header Bar with Toggle */}
      <header className="md:hidden bg-white/90 backdrop-blur-xl border-b border-purple-100 p-4 flex items-center justify-between sticky top-0 z-40 w-full shadow-sm">
        <div className="flex items-center space-x-2.5">
          <span className="text-xl">🤖</span>
          <h1 className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-900 via-indigo-800 to-purple-900 tracking-tight">
            API Patching Agent
          </h1>
        </div>
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-2 text-slate-600 hover:text-purple-900 focus:outline-none rounded-lg bg-purple-50/80 border border-purple-100"
          aria-label="Toggle Navigation Menu"
        >
          {isMobileOpen ? '✕' : '☰'}
        </button>
      </header>

      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={() => setIsMobileOpen(false)}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 md:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static top-0 left-0 z-50 h-full w-64 bg-white/90 backdrop-blur-xl border-r border-purple-100 flex flex-col justify-between p-5 sm:p-6 shrink-0 shadow-xl shadow-purple-500/5 transition-transform duration-300 ease-in-out ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🤖</span>
              <h1 className="text-base font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-900 via-indigo-800 to-purple-900 tracking-tight">
                API Patching Agent
              </h1>
            </div>
            {/* Close Button Inside Drawer on Mobile */}
            <button
              onClick={() => setIsMobileOpen(false)}
              className="md:hidden text-slate-400 hover:text-slate-700 text-sm p-1"
            >
              ✕
            </button>
          </div>

          <nav className="space-y-1.5">
            <Link
              to="/"
              className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
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
              className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
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
            <strong className="text-purple-900 block text-xs sm:text-sm font-semibold truncate mt-0.5">
              Logged in as : {user}
            </strong>
          </div>
          <button
            onClick={logout}
            className="w-full text-center bg-red-50 hover:bg-red-100/80 text-red-600 text-xs py-2.5 rounded-xl border border-red-200/80 font-semibold transition-all cursor-pointer active:scale-[0.99]"
          >
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
}