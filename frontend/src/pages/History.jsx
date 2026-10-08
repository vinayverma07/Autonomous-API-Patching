// import { useEffect, useState } from 'react';
// import API from '../api';

// export default function History() {
//   const [history, setHistory] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [openIndex, setOpenIndex] = useState(null);

//   useEffect(() => {
//     const fetchHistory = async () => {
//       try {
//         const res = await API.get('/api/history');
//         setHistory(res.data.history || []);
//       } catch (err) {
//         console.error('Failed to fetch repair history', err);
//       } finally {
//         setLoading(false);
//       }
//     };
//     fetchHistory();
//   }, []);

//   if (loading) {
//     return <div className="p-8 text-purple-900 font-medium text-sm">Loading repair history...</div>;
//   }

//   return (
//     <div className="p-8 max-w-6xl">
//       <div className="mb-8">
//         <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-950 via-indigo-900 to-purple-900">
//            Your Repair History
//         </h2>
//         <p className="text-xs text-slate-500 mt-1 font-medium">Historical autonomous patch runs executed by your account.</p>
//       </div>

//       {history.length === 0 ? (
//         <div className="bg-white/80 backdrop-blur-xl border border-purple-100 rounded-2xl p-12 text-center text-slate-500 space-y-2 shadow-xl shadow-purple-500/5">
//           <p className="text-4xl">📂</p>
//           <p className="text-sm font-semibold text-slate-700">No repair history found.</p>
//           <p className="text-xs text-slate-400">Run a repair sequence on the dashboard to store history here.</p>
//         </div>
//       ) : (
//         <div className="space-y-4">
//           {history.map((item, idx) => {
//             const isSuccess = ['successfully_patched', 'patch_validated_successfully'].includes(item.execution_status);
//             return (
//               <div key={item._id || idx} className="bg-white/80 backdrop-blur-xl border border-purple-100 rounded-2xl p-5 shadow-xl shadow-purple-500/5 space-y-3">
//                 <div
//                   onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
//                   className="flex items-center justify-between cursor-pointer"
//                 >
//                   <div className="flex items-center space-x-3">
//                     <span className="text-xl">📄</span>
//                     <div>
//                       <h3 className="text-sm font-bold text-slate-800 font-mono">{item.target_file_path}</h3>
//                       <p className="text-xs text-slate-400 mt-0.5">
//                         Session ID: {item.session_id} • {new Date(item.timestamp).toLocaleString()}
//                       </p>
//                     </div>
//                   </div>

//                   <div className="flex items-center space-x-3">
//                     <span
//                       className={`px-3 py-1 text-xs rounded-full font-semibold ${
//                         isSuccess
//                           ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
//                           : 'bg-red-50 border border-red-200 text-red-700'
//                       }`}
//                     >
//                       {isSuccess ? '✓ Patched' : '✕ Failed'}
//                     </span>
//                     <span className="text-purple-400 text-sm font-bold">{openIndex === idx ? '▲' : '▼'}</span>
//                   </div>
//                 </div>

//                 {openIndex === idx && (
//                   <div className="pt-4 border-t border-purple-100 space-y-4">
//                     <div>
//                       <h4 className="text-xs font-bold text-purple-900 uppercase tracking-wider mb-2">Original Log Traceback</h4>
//                       <pre className="bg-slate-950 p-3.5 rounded-xl border border-purple-900/30 text-xs font-mono text-slate-200 max-h-36 overflow-y-auto">
//                         <code>{item.raw_logs}</code>
//                       </pre>
//                     </div>

//                     {item.generated_patch && (
//                       <div>
//                         <h4 className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-2">Generated Patch</h4>
//                         <pre className="bg-slate-950 p-3.5 rounded-xl border border-purple-900/30 text-xs font-mono text-emerald-300 max-h-60 overflow-y-auto">
//                           <code>{item.generated_patch}</code>
//                         </pre>
//                       </div>
//                     )}
//                   </div>
//                 )}
//               </div>
//             );
//           })}
//         </div>
//       )}
//     </div>
//   );
// }

import { useEffect, useState } from 'react';
import API from '../api';

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openIndex, setOpenIndex] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await API.get('/api/history');
        setHistory(res.data.history || []);
      } catch (err) {
        console.error('Failed to fetch repair history', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 text-purple-900 font-medium text-xs sm:text-sm flex items-center gap-2">
        <span className="animate-spin">⚙️</span>
        <span>Loading repair history...</span>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto w-full">
      <div className="mb-6 sm:mb-8">
        <h2 className="text-xl sm:text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-950 via-indigo-900 to-purple-900">
           Your Repair History
        </h2>
        <p className="text-xs text-slate-500 mt-1 font-medium">Historical autonomous patch runs executed by your account.</p>
      </div>

      {history.length === 0 ? (
        <div className="bg-white/80 backdrop-blur-xl border border-purple-100 rounded-2xl p-8 sm:p-12 text-center text-slate-500 space-y-2 shadow-xl shadow-purple-500/5">
          <p className="text-3xl sm:text-4xl">📂</p>
          <p className="text-xs sm:text-sm font-semibold text-slate-700">No repair history found.</p>
          <p className="text-[11px] sm:text-xs text-slate-400">Run a repair sequence on the dashboard to store history here.</p>
        </div>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {history.map((item, idx) => {
            const isSuccess = ['successfully_patched', 'patch_validated_successfully'].includes(item.execution_status);
            return (
              <div key={item._id || idx} className="bg-white/80 backdrop-blur-xl border border-purple-100 rounded-2xl p-4 sm:p-5 shadow-xl shadow-purple-500/5 space-y-3 w-full transition-all">
                <div
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="flex flex-col sm:flex-row sm:items-center justify-between cursor-pointer gap-3 sm:gap-4"
                >
                  <div className="flex items-start sm:items-center space-x-3 min-w-0 flex-1">
                    <span className="text-lg sm:text-xl shrink-0 mt-0.5 sm:mt-0">📄</span>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-xs sm:text-sm font-bold text-slate-800 font-mono break-all sm:break-normal">
                        {item.target_file_path}
                      </h3>
                      <p className="text-[11px] sm:text-xs text-slate-400 mt-0.5 break-all sm:break-normal leading-relaxed">
                        <span className="font-mono text-slate-500">Session ID: {item.session_id}</span>
                        <span className="hidden sm:inline"> • </span>
                        <span className="block sm:inline">{new Date(item.timestamp).toLocaleString()}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end space-x-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-purple-50">
                    <span
                      className={`px-2.5 py-1 text-[11px] sm:text-xs rounded-full font-semibold shrink-0 ${
                        isSuccess
                          ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
                          : 'bg-red-50 border border-red-200 text-red-700'
                      }`}
                    >
                      {isSuccess ? '✓ Patched' : '✕ Failed'}
                    </span>
                    <span className="text-purple-400 text-xs sm:text-sm font-bold pl-1">{openIndex === idx ? '▲' : '▼'}</span>
                  </div>
                </div>

                {openIndex === idx && (
                  <div className="pt-3 sm:pt-4 border-t border-purple-100 space-y-3 sm:space-y-4">
                    <div>
                      <h4 className="text-[11px] sm:text-xs font-bold text-purple-900 uppercase tracking-wider mb-1.5 sm:mb-2">
                        Original Log Traceback
                      </h4>
                      <div className="relative w-full overflow-hidden rounded-xl">
                        <pre className="bg-slate-950 p-3 sm:p-3.5 border border-purple-900/30 text-[11px] sm:text-xs font-mono text-slate-200 max-h-36 overflow-y-auto overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">
                          <code>{item.raw_logs}</code>
                        </pre>
                      </div>
                    </div>

                    {item.generated_patch && (
                      <div>
                        <h4 className="text-[11px] sm:text-xs font-bold text-emerald-700 uppercase tracking-wider mb-1.5 sm:mb-2">
                          Generated Patch
                        </h4>
                        <div className="relative w-full overflow-hidden rounded-xl">
                          <pre className="bg-slate-950 p-3 sm:p-3.5 border border-purple-900/30 text-[11px] sm:text-xs font-mono text-emerald-300 max-h-60 overflow-y-auto overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">
                            <code>{item.generated_patch}</code>
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}