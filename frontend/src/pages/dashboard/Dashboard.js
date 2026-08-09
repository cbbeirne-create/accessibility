/**
 * Dashboard Page
 * 
 * Main landing page for authenticated users showing overview and quick actions.
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader friendly scan list
 */
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, BarChart3, Zap, ChevronRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scansAPI } from '../../services/api';
import { formatDate, getScoreColorClass } from '../../utils/wcag';

const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" role="main" aria-labelledby="dashboard-heading">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 id="dashboard-heading" className="text-3xl font-bold text-white mb-2">
            Welcome back, {user?.full_name || user?.email?.split('@')[0]}
          </h1>
          <p className="text-slate-400">
            {user?.scans_remaining === -1 
              ? 'You have unlimited scans with your Pro plan' 
              : `You have ${user?.scans_remaining} scans remaining this month`}
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link
            to="/scan"
            className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 rounded-2xl p-6 hover:border-emerald-500/50 transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-500/30 transition-all">
              <Search className="w-6 h-6 text-emerald-400" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">New Scan</h2>
            <p className="text-slate-400 text-sm">Start a new accessibility scan</p>
          </Link>

          <Link
            to="/my-scans"
            className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-slate-700 transition-all">
              <BarChart3 className="w-6 h-6 text-slate-400" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">My Scans</h2>
            <p className="text-slate-400 text-sm">View all your scan history</p>
          </Link>

          {user?.plan === 'free' && (
            <Link
              to="/pricing"
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-emerald-500/30 transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
                <Zap className="w-6 h-6 text-amber-400" aria-hidden="true" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Upgrade to Pro</h2>
              <p className="text-slate-400 text-sm">Get unlimited scans and PDF exports</p>
            </Link>
          )}
        </div>

        {/* Recent Scans */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white">Recent Scans</h2>
            {scans.length > 0 && (
              <Link to="/my-scans" className="text-emerald-400 hover:text-emerald-300 text-sm font-medium">
                View All →
              </Link>
            )}
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400" aria-hidden="true" />
            </div>
          ) : scans.length === 0 ? (
            <div className="text-center py-8">
              <Search className="w-10 h-10 text-slate-600 mx-auto mb-3" aria-hidden="true" />
              <p className="text-slate-400">No scans yet. Start your first scan!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {scans.map((scan) => (
                <Link
                  key={scan.id}
                  to={`/scan-results/${scan.id}`}
                  className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl hover:bg-slate-800 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{scan.url}</p>
                    <p className="text-slate-400 text-sm">{formatDate(scan.createdAt)}</p>
                  </div>
                  <div className="flex items-center space-x-4 ml-4">
                    <span className={`text-2xl font-bold ${getScoreColorClass(scan.score || 0)}`}>
                      {scan.score ?? '-'}
                    </span>
                    <ChevronRight className="w-5 h-5 text-slate-400" aria-hidden="true" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
