/**
 * My Scans Page
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader friendly scan list
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Calendar, ExternalLink, Trash2 } from 'lucide-react';
import { scansAPI } from '../../services/api';
import { formatDate, getScoreColorClass } from '../../utils/wcag';

const MyScansPage = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const data = await scansAPI.getAll();
        setScans(data);
      } catch (err) {
        setError('Failed to load scans');
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, []);

  const handleDelete = async (scanId) => {
    if (!window.confirm('Are you sure you want to delete this scan?')) return;
    try {
      await scansAPI.delete(scanId);
      setScans(scans.filter(s => s.id !== scanId));
    } catch (err) {
      alert('Failed to delete scan');
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400" aria-hidden="true" />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-12 px-4">
      <main id="main-content" className="container mx-auto max-w-4xl" role="main" aria-labelledby="my-scans-heading">
        <div className="flex justify-between items-center mb-8">
          <h1 id="my-scans-heading" className="text-3xl font-bold text-white">My Scans</h1>
          <Link
            to="/scan"
            className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-6 py-2 rounded-lg font-medium transition-all"
          >
            New Scan
          </Link>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg mb-6" role="alert">
            {error}
          </div>
        )}

        {scans.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-xl font-semibold text-white mb-2">No scans yet</h2>
            <p className="text-slate-400 mb-6">Start your first accessibility scan to see results here.</p>
            <Link
              to="/scan"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-3 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-600 transition-all"
            >
              <Search className="w-5 h-5" aria-hidden="true" />
              <span>Start New Scan</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {scans.map((scan) => (
              <div
                key={scan.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/scan-results/${scan.id}`}
                      className="text-white font-medium hover:text-emerald-400 transition-colors truncate block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded"
                    >
                      {scan.url}
                    </Link>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" aria-hidden="true" />
                        <span>{formatDate(scan.createdAt)}</span>
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        scan.status === 'completed' 
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : scan.status === 'pending'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-red-500/20 text-red-300'
                      }`}>
                        {scan.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 ml-4">
                    {scan.score !== null && scan.score !== undefined && (
                      <div className={`text-2xl font-bold ${getScoreColorClass(scan.score)}`}>
                        {scan.score}
                      </div>
                    )}
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/scan-results/${scan.id}`}
                        className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                        aria-label={`View scan results for ${scan.url}`}
                      >
                        <ExternalLink className="w-5 h-5" aria-hidden="true" />
                      </Link>
                      <button
                        onClick={() => handleDelete(scan.id)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                        aria-label={`Delete scan for ${scan.url}`}
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
    </div>
  );
};

export default MyScansPage;
