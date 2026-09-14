/**
 * New Scan Page
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Globe, Search, AlertTriangle, ArrowRight, ShieldCheck, ListChecks, Image } from 'lucide-react';
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
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 sm:py-12 px-4">
      <main id="main-content" className="container mx-auto max-w-4xl" aria-labelledby="scan-heading">
        <div className="text-center mb-8">
          <p className="text-emerald-400 text-sm font-semibold uppercase tracking-wider mb-2">Accessibility audit</p>
          <h1 id="scan-heading" className="text-3xl sm:text-4xl font-bold text-white mb-3">Scan a website</h1>
          <p className="text-slate-300 max-w-2xl mx-auto">Run automated accessibility checks, review prioritised findings and inspect the affected page elements.</p>
        </div>

        {!canScan && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-5 sm:p-6 mb-6 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" aria-hidden="true" />
            <p className="text-amber-100 font-semibold mb-2">Scan limit reached</p>
            <p className="text-amber-200/80 text-sm mb-4">You&apos;ve used all your scans for this month. Upgrade to Pro to continue scanning.</p>
            <Link to="/pricing" className="min-h-11 inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
              <span>View Pro plan</span>
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
          </div>
        )}

        <div className="grid lg:grid-cols-[minmax(0,1fr)_280px] gap-6 items-start">
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-8" aria-label="Start a scan">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div id="scan-error" className="bg-red-500/10 border border-red-500/30 text-red-200 px-4 py-3 rounded-lg text-sm" role="alert">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="scan-url" className="block text-sm font-medium text-slate-200 mb-2">Website URL <span className="text-red-400" aria-hidden="true">*</span></label>
                <div className="relative">
                  <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" aria-hidden="true" />
                  <input
                    type="url"
                    id="scan-url"
                    data-testid="scan-url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    aria-describedby={`scan-url-help${error ? ' scan-error' : ''}`}
                    aria-invalid={error ? 'true' : undefined}
                    className="w-full min-h-12 pl-12 pr-4 py-3.5 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-colors"
                    placeholder="https://example.com"
                    required
                    disabled={!canScan || loading}
                  />
                </div>
                <p id="scan-url-help" className="text-slate-400 text-sm mt-2">Use the full public URL, including https://</p>
              </div>

              <button
                type="submit"
                data-testid="scan-submit"
                disabled={loading || !canScan || !url.trim()}
                aria-busy={loading}
                className="w-full min-h-12 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-400 text-white font-semibold py-3 px-6 rounded-xl transition-colors shadow-lg shadow-emerald-950/30 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Starting scan…</span>
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2"><Search className="w-5 h-5" aria-hidden="true" /><span>Start accessibility scan</span></span>
                )}
              </button>
            </form>

            {user && (
              <div className="mt-6 pt-5 border-t border-slate-800 text-center">
                <p className="text-slate-400 text-sm">
                  {user.scans_remaining === -1 ? <span className="text-emerald-300 font-medium">Unlimited scans available</span> : <><span className="text-white font-semibold">{user.scans_remaining}</span> scans remaining this month</>}
                </p>
              </div>
            )}
          </section>

          <aside className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5" aria-labelledby="scan-includes-heading">
            <h2 id="scan-includes-heading" className="text-base font-semibold text-white mb-4">What you&apos;ll get</h2>
            <div className="space-y-4">
              <div className="flex gap-3"><ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" /><div><p className="text-sm font-medium text-slate-200">Automated checks</p><p className="text-xs text-slate-400 mt-1">Rules grouped into failed, passed and needs-review findings.</p></div></div>
              <div className="flex gap-3"><ListChecks className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" /><div><p className="text-sm font-medium text-slate-200">Actionable fixes</p><p className="text-xs text-slate-400 mt-1">Prioritised remediation guidance with affected selectors and markup.</p></div></div>
              <div className="flex gap-3"><Image className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" /><div><p className="text-sm font-medium text-slate-200">Visual evidence</p><p className="text-xs text-slate-400 mt-1">Where available, review a captured page image alongside the findings.</p></div></div>
            </div>
            <p className="text-xs text-slate-500 mt-5 pt-4 border-t border-slate-800">Automated scanning supports accessibility work but does not replace manual testing or certify WCAG conformance.</p>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default ScanPage;
