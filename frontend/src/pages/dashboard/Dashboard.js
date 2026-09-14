/**
 * Dashboard Page
 */
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, BarChart3, Zap, ChevronRight, Clock3 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scansAPI } from '../../services/api';
import { formatDate, getScoreColorClass } from '../../utils/wcag';

const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchScans = async () => {
      try {
        const data = await scansAPI.getAll();
        setScans(data.slice(0, 5));
      } catch (err) {
        console.error('Failed to fetch scans:', err);
        setError('We could not load your recent scans. You can still start a new scan.');
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  const scansRemaining = user?.scans_remaining;
  const hasUnlimitedScans = scansRemaining === -1;

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-6 sm:py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" aria-labelledby="dashboard-heading">
        <header className="mb-8 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <p className="text-emerald-400 text-sm font-semibold mb-2">Overview</p>
            <h1 id="dashboard-heading" className="text-3xl font-bold text-white mb-2">Welcome back, {user?.full_name || user?.email?.split('@')[0]}</h1>
            <p className="text-slate-400">
              {hasUnlimitedScans ? 'Your Pro plan includes unlimited scans.' : `You have ${scansRemaining ?? 0} scans remaining this month.`}
            </p>
          </div>
          <Link to="/scan" className="min-h-11 inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
            <Search className="w-4 h-4" aria-hidden="true" />
            New scan
          </Link>
        </header>

        <section aria-labelledby="quick-actions-heading" className="mb-8">
          <h2 id="quick-actions-heading" className="sr-only">Quick actions</h2>
          <div className={`grid gap-4 ${user?.plan === 'free' ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
            <Link to="/my-scans" className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-colors group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 bg-slate-800 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-slate-700 transition-colors"><BarChart3 className="w-5 h-5 text-slate-300" aria-hidden="true" /></div>
                <div><h3 className="text-lg font-semibold text-white">Scan history</h3><p className="text-slate-400 text-sm mt-1">Review previous scans and findings.</p></div>
              </div>
            </Link>

            <Link to="/scheduled-scans" className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-colors group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 bg-slate-800 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-slate-700 transition-colors"><Clock3 className="w-5 h-5 text-slate-300" aria-hidden="true" /></div>
                <div><h3 className="text-lg font-semibold text-white">Scheduled scans</h3><p className="text-slate-400 text-sm mt-1">Monitor sites on a recurring schedule.</p></div>
              </div>
            </Link>

            {user?.plan === 'free' && (
              <Link to="/pricing" className="bg-emerald-500/10 border border-emerald-500/25 rounded-2xl p-5 hover:border-emerald-500/50 transition-colors group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
                <div className="flex items-start gap-4">
                  <div className="w-11 h-11 bg-emerald-500/15 rounded-xl flex items-center justify-center shrink-0"><Zap className="w-5 h-5 text-amber-300" aria-hidden="true" /></div>
                  <div><h3 className="text-lg font-semibold text-white">Upgrade to Pro</h3><p className="text-slate-300 text-sm mt-1">Unlock unlimited scans and PDF reports.</p></div>
                </div>
              </Link>
            )}
          </div>
        </section>

        <section className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden" aria-labelledby="recent-scans-heading">
          <div className="flex justify-between items-center gap-4 p-5 sm:p-6 border-b border-slate-800">
            <div>
              <h2 id="recent-scans-heading" className="text-xl font-semibold text-white">Recent scans</h2>
              <p className="text-sm text-slate-400 mt-1">Your five most recent accessibility checks.</p>
            </div>
            {scans.length > 0 && <Link to="/my-scans" className="min-h-11 inline-flex items-center text-emerald-300 hover:text-emerald-200 text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">View all</Link>}
          </div>

          {error && <div className="m-5 sm:m-6 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100" role="alert">{error}</div>}

          {loading ? (
            <div className="flex items-center justify-center gap-3 py-12" role="status" aria-live="polite">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-400" aria-hidden="true" />
              <span className="text-sm text-slate-400">Loading recent scans…</span>
            </div>
          ) : scans.length === 0 ? (
            <div className="text-center py-12 px-5">
              <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center mx-auto mb-4"><Search className="w-6 h-6 text-slate-400" aria-hidden="true" /></div>
              <h3 className="text-white font-semibold">No scans yet</h3>
              <p className="text-slate-400 text-sm mt-2 mb-5">Start with any public webpage and Auditly will organise the automated findings for you.</p>
              <Link to="/scan" className="min-h-11 inline-flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-lg text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">Start your first scan</Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {scans.map((scan) => (
                <Link key={scan.id} to={`/scan-results/${scan.id}`} className="flex items-center justify-between gap-4 p-4 sm:p-5 hover:bg-slate-800/60 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-400">
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{scan.url}</p>
                    <p className="text-slate-400 text-sm mt-1">{formatDate(scan.createdAt)}</p>
                  </div>
                  <div className="flex items-center gap-3 sm:gap-4 ml-2">
                    <div className="text-right"><span className={`text-2xl font-bold ${getScoreColorClass(scan.score || 0)}`}>{scan.score ?? '—'}</span><span className="block text-[11px] text-slate-500">Score</span></div>
                    <ChevronRight className="w-5 h-5 text-slate-400" aria-hidden="true" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
