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
    return <div className="p-8 text-slate-400 text-sm">Loading repair history...</div>;
  }

  return (
    <div className="p-8 max-w-6xl">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">📜 Your Repair History</h2>
        <p className="text-xs text-slate-400 mt-1">Historical autonomous patch runs executed by your account.</p>
      </div>

      {history.length === 0 ? (
        <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-12 text-center text-slate-400 space-y-2">
          <p className="text-4xl">📂</p>
          <p className="text-sm font-medium">No repair history found.</p>
          <p className="text-xs text-slate-500">Run a repair sequence on the dashboard to store history here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((item, idx) => {
            const isSuccess = ['successfully_patched', 'patch_validated_successfully'].includes(item.execution_status);
            return (
              <div key={item._id || idx} className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-5 shadow-lg space-y-3">
                <div
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">📄</span>
                    <div>
                      <h3 className="text-sm font-semibold text-white font-mono">{item.target_file_path}</h3>
                      <p className="text-xs text-slate-400">
                        Session ID: {item.session_id} • {new Date(item.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span
                      className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                        isSuccess
                          ? 'bg-emerald-950 border border-emerald-500/40 text-emerald-400'
                          : 'bg-red-950 border border-red-500/40 text-red-400'
                      }`}
                    >
                      {isSuccess ? '✓ Patched' : '✕ Failed'}
                    </span>
                    <span className="text-slate-400 text-sm">{openIndex === idx ? '▲' : '▼'}</span>
                  </div>
                </div>

                {openIndex === idx && (
                  <div className="pt-4 border-t border-slate-700/50 space-y-4">
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Original Log Traceback</h4>
                      <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-36 overflow-y-auto">
                        <code>{item.raw_logs}</code>
                      </pre>
                    </div>

                    {item.generated_patch && (
                      <div>
                        <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Generated Patch</h4>
                        <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono text-emerald-300 max-h-60 overflow-y-auto">
                          <code>{item.generated_patch}</code>
                        </pre>
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