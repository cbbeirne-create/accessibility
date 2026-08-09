/**
 * New Scan Page
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader announcements
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Globe, Search, AlertTriangle, ArrowRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scansAPI } from '../../services/api';

const ScanPage = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const scan = await scansAPI.create(url);
      navigate(`/scan-results/${scan.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const canScan = user?.scans_remaining === -1 || user?.scans_remaining > 0;

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-12 px-4">
      <main id="main-content" className="container mx-auto max-w-2xl" role="main" aria-labelledby="scan-heading">
        <div className="text-center mb-8">
          <h1 id="scan-heading" className="text-3xl font-bold text-white mb-4">Start New Scan</h1>
          <p className="text-slate-300">Enter a URL to analyze for accessibility issues</p>
        </div>

        {!canScan && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-6 mb-8 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" aria-hidden="true" />
            <p className="text-amber-200 font-medium mb-2">Scan Limit Reached</p>
            <p className="text-amber-300/80 text-sm mb-4">
              You&apos;ve used all your free scans this month. Upgrade to Pro for unlimited scans.
            </p>
            <Link
              to="/pricing"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-2 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-600 transition-all"
            >
              <span>Upgrade to Pro</span>
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
          </div>
        )}

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6" aria-labelledby="scan-heading">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="scan-url" className="block text-sm font-medium text-slate-200 mb-2">
                Website URL <span className="text-red-400" aria-hidden="true">*</span>
              </label>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" aria-hidden="true" />
                <input
                  type="url"
                  id="scan-url"
                  data-testid="scan-url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="https://example.com"
                  required
                  disabled={!canScan}
                />
              </div>
              <p className="text-slate-400 text-sm mt-2">
                Enter the full URL including https://
              </p>
            </div>

            <button
              type="submit"
              data-testid="scan-submit"
              disabled={loading || !canScan || !url.trim()}
              aria-busy={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Starting Scan...</span>
                </span>
              ) : (
                <span className="flex items-center justify-center space-x-2">
                  <Search className="w-5 h-5" aria-hidden="true" />
                  <span>Start Accessibility Scan</span>
                </span>
              )}
            </button>
          </form>

          {user && (
            <div className="mt-6 pt-6 border-t border-slate-800 text-center">
              <p className="text-slate-400 text-sm">
                {user.scans_remaining === -1 ? (
                  <span className="text-emerald-400">Unlimited scans available</span>
                ) : (
                  <>
                    <span className="text-white font-medium">{user.scans_remaining}</span> scans remaining this month
                  </>
                )}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ScanPage;
