/**
 * Scheduled Scans Page
 * 
 * Manage automated recurring accessibility scans.
 * Pro users get unlimited, Free users get 1.
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Clock, Plus, Globe, Calendar, Trash2, 
  Play, Pause, AlertTriangle, Zap, ChevronRight,
  RefreshCw, ExternalLink
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scheduledScansAPI } from '../../services/api';
import { formatDate, getScoreColorClass } from '../../utils/wcag';

const ScheduledScansPage = () => {
  const { user } = useAuth();
  const [scheduledScans, setScheduledScans] = useState([]);
  const [limitsInfo, setLimitsInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newInterval, setNewInterval] = useState(7);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [scans, limits] = await Promise.all([
        scheduledScansAPI.getAll(),
        scheduledScansAPI.getLimits()
      ]);
      setScheduledScans(scans);
      setLimitsInfo(limits);
    } catch (err) {
      console.error('Failed to fetch scheduled scans:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setError('');

    try {
      const newScan = await scheduledScansAPI.create(newUrl, newInterval);
      setScheduledScans([newScan, ...scheduledScans]);
      setShowCreateModal(false);
      setNewUrl('');
      setNewInterval(7);
      // Refresh limits
      const limits = await scheduledScansAPI.getLimits();
      setLimitsInfo(limits);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create scheduled scan');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleToggle = async (scheduledId) => {
    try {
      const updated = await scheduledScansAPI.toggle(scheduledId);
      setScheduledScans(scheduledScans.map(s => 
        s.id === scheduledId ? updated : s
      ));
    } catch (err) {
      alert('Failed to toggle scheduled scan');
    }
  };

  const handleDelete = async (scheduledId) => {
    if (!window.confirm('Are you sure you want to delete this scheduled scan?')) return;
    
    try {
      await scheduledScansAPI.delete(scheduledId);
      setScheduledScans(scheduledScans.filter(s => s.id !== scheduledId));
      // Refresh limits
      const limits = await scheduledScansAPI.getLimits();
      setLimitsInfo(limits);
    } catch (err) {
      alert('Failed to delete scheduled scan');
    }
  };

  const formatNextRun = (nextRun) => {
    const date = new Date(nextRun);
    const now = new Date();
    const diffMs = date - now;
    const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays <= 0) return 'Running soon...';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays <= 7) return `In ${diffDays} days`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getIntervalText = (days) => {
    if (days === 1) return 'Daily';
    if (days === 7) return 'Weekly';
    if (days === 14) return 'Bi-weekly';
    if (days === 30) return 'Monthly';
    return `Every ${days} days`;
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400" aria-hidden="true" />
      </div>
    );
  }

  const isPro = user?.plan === 'pro';
  const canCreate = limitsInfo?.can_create || false;

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-4xl" role="main" aria-labelledby="scheduled-heading">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-start gap-4 mb-8">
          <div>
            <h1 id="scheduled-heading" className="text-3xl font-bold text-white mb-2">Scheduled Scans</h1>
            <p className="text-slate-400">Automate your accessibility monitoring</p>
          </div>
          
          {canCreate ? (
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-5 py-2.5 rounded-xl font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              <Plus className="w-5 h-5" aria-hidden="true" />
              <span>New Scheduled Scan</span>
            </button>
          ) : !isPro ? (
            <Link
              to="/pricing"
              className="flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-5 py-2.5 rounded-xl font-medium transition-all"
            >
              <Zap className="w-5 h-5" aria-hidden="true" />
              <span>Upgrade for More</span>
            </Link>
          ) : null}
        </div>

        {/* Limits Info */}
        {limitsInfo && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Clock className="w-5 h-5 text-slate-400" aria-hidden="true" />
                <span className="text-slate-300">
                  {limitsInfo.limit === -1 ? (
                    <span className="text-emerald-400">Unlimited scheduled scans (Pro)</span>
                  ) : (
                    <>
                      <span className="text-white font-medium">{limitsInfo.used}</span>
                      <span className="text-slate-400"> / {limitsInfo.limit} scheduled scan{limitsInfo.limit !== 1 ? 's' : ''} used</span>
                    </>
                  )}
                </span>
              </div>
              {!isPro && (
                <Link to="/pricing" className="text-emerald-400 hover:text-emerald-300 text-sm font-medium">
                  Upgrade for unlimited →
                </Link>
              )}
            </div>
          </div>
        )}

        {/* Pro Only Notice for Free Users */}
        {!isPro && scheduledScans.length === 0 && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-8 mb-6 text-center">
            <Zap className="w-12 h-12 text-amber-400 mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-xl font-semibold text-white mb-2">Premium Feature</h2>
            <p className="text-amber-200/80 mb-4 max-w-md mx-auto">
              Scheduled scans automatically monitor your websites for accessibility issues.
              Free users can try 1 scheduled scan. Upgrade to Pro for unlimited.
            </p>
            <Link
              to="/pricing"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-3 rounded-xl font-medium hover:from-emerald-600 hover:to-teal-600 transition-all"
            >
              <Zap className="w-5 h-5" aria-hidden="true" />
              <span>Upgrade to Pro</span>
            </Link>
          </div>
        )}

        {/* Scheduled Scans List */}
        {scheduledScans.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Clock className="w-12 h-12 text-slate-600 mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-xl font-semibold text-white mb-2">No scheduled scans yet</h2>
            <p className="text-slate-400 mb-6">Set up automatic recurring scans for your websites.</p>
            {canCreate && (
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-3 rounded-xl font-medium hover:from-emerald-600 hover:to-teal-600 transition-all"
              >
                <Plus className="w-5 h-5" aria-hidden="true" />
                <span>Create First Scheduled Scan</span>
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {scheduledScans.map((scan) => (
              <div
                key={scan.id}
                className={`bg-slate-900 border rounded-xl p-6 transition-all ${
                  scan.enabled ? 'border-slate-800' : 'border-slate-800/50 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <Globe className="w-5 h-5 text-slate-400 flex-shrink-0" aria-hidden="true" />
                      <span className="text-white font-medium truncate">{scan.url}</span>
                      {!scan.enabled && (
                        <span className="px-2 py-0.5 bg-slate-700 text-slate-400 text-xs rounded-full">
                          Paused
                        </span>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400 mt-3">
                      <span className="flex items-center space-x-1">
                        <RefreshCw className="w-4 h-4" aria-hidden="true" />
                        <span>{getIntervalText(scan.interval_days)}</span>
                      </span>
                      
                      {scan.enabled && (
                        <span className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" aria-hidden="true" />
                          <span>Next: {formatNextRun(scan.next_run)}</span>
                        </span>
                      )}
                      
                      {scan.last_run && (
                        <span className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" aria-hidden="true" />
                          <span>Last: {formatDate(scan.last_run)}</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    {scan.last_score !== null && scan.last_score !== undefined && (
                      <div className={`text-2xl font-bold ${getScoreColorClass(scan.last_score)}`}>
                        {scan.last_score}
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-1">
                      {scan.last_scan_id && (
                        <Link
                          to={`/scan-results/${scan.last_scan_id}`}
                          className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                          aria-label="View last scan results"
                        >
                          <ExternalLink className="w-5 h-5" aria-hidden="true" />
                        </Link>
                      )}
                      
                      <button
                        onClick={() => handleToggle(scan.id)}
                        className={`p-2 transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
                          scan.enabled ? 'text-emerald-400 hover:text-emerald-300' : 'text-slate-500 hover:text-slate-400'
                        }`}
                        aria-label={scan.enabled ? 'Pause scheduled scan' : 'Resume scheduled scan'}
                      >
                        {scan.enabled ? (
                          <Pause className="w-5 h-5" aria-hidden="true" />
                        ) : (
                          <Play className="w-5 h-5" aria-hidden="true" />
                        )}
                      </button>
                      
                      <button
                        onClick={() => handleDelete(scan.id)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                        aria-label="Delete scheduled scan"
                      >
                        <Trash2 className="w-5 h-5" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" role="dialog" aria-modal="true" aria-labelledby="create-modal-title">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md">
            <h2 id="create-modal-title" className="text-xl font-bold text-white mb-4">Create Scheduled Scan</h2>
            
            <form onSubmit={handleCreate} className="space-y-5">
              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="scheduled-url" className="block text-sm font-medium text-slate-200 mb-2">
                  Website URL <span className="text-red-400" aria-hidden="true">*</span>
                </label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" aria-hidden="true" />
                  <input
                    type="url"
                    id="scheduled-url"
                    value={newUrl}
                    onChange={(e) => setNewUrl(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                    placeholder="https://example.com"
                    required
                  />
                </div>
              </div>

              <div>
                <label htmlFor="scheduled-interval" className="block text-sm font-medium text-slate-200 mb-2">
                  Scan Interval
                </label>
                <select
                  id="scheduled-interval"
                  value={newInterval}
                  onChange={(e) => setNewInterval(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                >
                  <option value={1}>Daily</option>
                  <option value={7}>Weekly</option>
                  <option value={14}>Bi-weekly (Every 2 weeks)</option>
                  <option value={30}>Monthly</option>
                  <option value={90}>Quarterly (Every 3 months)</option>
                </select>
                <p className="text-slate-500 text-sm mt-2">
                  First scan will run in {newInterval} day{newInterval !== 1 ? 's' : ''}
                </p>
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setShowCreateModal(false); setError(''); }}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-medium py-3 px-4 rounded-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading || !newUrl.trim()}
                  className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-medium py-3 px-4 rounded-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                >
                  {createLoading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduledScansPage;
