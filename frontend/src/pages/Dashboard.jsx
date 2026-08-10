import { useState, useEffect } from 'react';
import API from '../api';

export default function Dashboard() {
  const [formData, setFormData] = useState({
    target_file_path: 'sample_api.py',
    raw_logs: '',
    original_code: '',
  });
  const [sessionId, setSessionId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setJobStatus(null);
    try {
      const res = await API.post('/api/repair', formData);
      setSessionId(res.data.session_id);
      setJobStatus({ status: 'queued' });
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to initialize repair job.');
    } finally {
      setLoading(false);
    }
  };

  // Poll backend for repair status when sessionId changes
  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(async () => {
      try {
        const res = await API.get(`/api/status/${sessionId}`);
        setJobStatus(res.data);
        if (
          ['successfully_patched', 'patch_validated_successfully', 'failed_to_patch', 'execution_error'].includes(
            res.data.status
          )
        ) {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [sessionId]);

  return (
    <div className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Diagnostics Input Form */}
      <section className="bg-white/80 backdrop-blur-xl border border-purple-100 rounded-2xl p-6 shadow-xl shadow-purple-500/5 h-fit">
        <h2 className="text-lg font-bold text-purple-950 mb-4">📥 Inbound Failure Diagnostics</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Target Broken File Path</label>
            <input
              type="text"
              required
              value={formData.target_file_path}
              onChange={(e) => setFormData({ ...formData, target_file_path: e.target.value })}
              className="w-full bg-white/90 border border-purple-200/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-500/20 transition-all font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Raw API Exception Logs / Traceback Dump</label>
            <textarea
              rows="5"
              required
              placeholder="Paste exception traceback here..."
              value={formData.raw_logs}
              onChange={(e) => setFormData({ ...formData, raw_logs: e.target.value })}
              className="w-full bg-white/90 border border-purple-200/80 rounded-xl px-3.5 py-2.5 text-sm font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-500/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Original Broken Codebase Content</label>
            <textarea
              rows="8"
              required
              placeholder="Paste original broken code here..."
              value={formData.original_code}
              onChange={(e) => setFormData({ ...formData, original_code: e.target.value })}
              className="w-full bg-white/90 border border-purple-200/80 rounded-xl px-3.5 py-2.5 text-sm font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-purple-600 focus:ring-2 focus:ring-purple-500/20 transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium py-2.5 rounded-xl shadow-lg shadow-purple-600/25 transition-all duration-200 cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Submitting Job...' : '🚀 Execute Autonomous Repair Loop'}
          </button>
        </form>
      </section>

      {/* Execution Status & Output Panel */}
      <section className="bg-white/80 backdrop-blur-xl border border-purple-100 rounded-2xl p-6 shadow-xl shadow-purple-500/5 flex flex-col h-fit min-h-[400px]">
        <h2 className="text-lg font-bold text-purple-950 mb-4">🧠 Agentic Lifecycle Orchestration</h2>

        {!jobStatus ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 text-sm min-h-[300px]">
            <div className="text-center space-y-2">
              <p className="text-4xl">⚙️</p>
              <p className="text-slate-500 font-medium">System Idle. Submit a repair request to initialize the pipeline.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-purple-50/80 border border-purple-200/80 rounded-xl text-purple-900 text-sm flex items-center justify-between font-medium">
              <span>
                Current Execution Status: <strong className="text-purple-950 uppercase">{jobStatus.status}</strong>
              </span>
              {['queued', 'in_progress'].includes(jobStatus.status) && <span className="animate-spin">⚙️</span>}
            </div>

            {['successfully_patched', 'patch_validated_successfully'].includes(jobStatus.status) && (
              <div className="space-y-3">
                <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm font-semibold">
                  🎉 Code Repair Successful! Patch Applied & Validated.
                </div>
                <pre className="bg-slate-950 p-4 rounded-xl border border-purple-900/30 text-xs font-mono text-emerald-300 overflow-x-auto shadow-inner">
                  <code>{jobStatus.generated_patch}</code>
                </pre>
              </div>
            )}

            {['failed_to_patch', 'execution_error'].includes(jobStatus.status) && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm space-y-2">
                <p className="font-semibold">❌ Repair Process Failed</p>
                <p className="text-xs font-mono text-slate-600">{jobStatus.error || 'Agentic workflow could not generate a passing patch.'}</p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}