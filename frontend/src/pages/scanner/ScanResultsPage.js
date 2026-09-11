import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Download, ExternalLink, FileText, Info, Lock, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scansAPI } from '../../services/api';
import {
  formatDate,
  getScoreColorClass,
  getImpactColorClass,
  getRemediationGuidance,
} from '../../utils/wcag';

const TABS = ['failed', 'passed', 'incomplete'];

const ScanResultsPage = () => {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('failed');
  const [screenshotUrl, setScreenshotUrl] = useState(null);
  const tabRefs = useRef([]);
  const { user } = useAuth();

  useEffect(() => {
    let cancelled = false;
    let interval;

    const load = async () => {
      try {
        const data = await scansAPI.getById(id);
        if (cancelled) return;
        setScan(data);
        if (data.status === 'pending') {
          interval = window.setInterval(async () => {
            try {
              const updated = await scansAPI.getById(id);
              if (cancelled) return;
              setScan(updated);
              if (updated.status !== 'pending') window.clearInterval(interval);
            } catch {
              window.clearInterval(interval);
            }
          }, 3000);
        }
      } catch {
        if (!cancelled) setError('Failed to load scan results');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
      if (interval) window.clearInterval(interval);
    };
  }, [id]);

  useEffect(() => {
    let objectUrl;
    if (scan?.status !== 'completed') return undefined;

    scansAPI.getScreenshot(id)
      .then((blob) => {
        objectUrl = window.URL.createObjectURL(blob);
        setScreenshotUrl(objectUrl);
      })
      .catch(() => setScreenshotUrl(null));

    return () => {
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [id, scan?.status]);

  const issues = useMemo(() => scan?.issues || { failed: [], passed: [], incomplete: [] }, [scan]);

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleExportPDF = async () => {
    try {
      downloadBlob(await scansAPI.exportPDF(id), `accessibility-report-${id}.pdf`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to export PDF');
    }
  };

  const handleExportJSON = async () => {
    try {
      const data = await scansAPI.exportJSON(id);
      downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }), `accessibility-data-${id}.json`);
    } catch {
      setError('Failed to export JSON');
    }
  };

  const selectTab = (index) => {
    const normalized = (index + TABS.length) % TABS.length;
    setActiveTab(TABS[normalized]);
    tabRefs.current[normalized]?.focus();
  };

  const onTabKeyDown = (event, index) => {
    if (event.key === 'ArrowRight') { event.preventDefault(); selectTab(index + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); selectTab(index - 1); }
    if (event.key === 'Home') { event.preventDefault(); selectTab(0); }
    if (event.key === 'End') { event.preventDefault(); selectTab(TABS.length - 1); }
  };

  if (loading) {
    return <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center" role="status" aria-live="polite"><p className="text-slate-300">Loading scan results…</p></div>;
  }

  if (error && !scan) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="text-center"><X className="w-12 h-12 text-red-400 mx-auto mb-4" aria-hidden="true" /><h1 className="text-xl font-semibold text-white">Error Loading Results</h1><p className="text-slate-400">{error}</p></div>
      </div>
    );
  }

  if (scan?.status === 'pending') {
    return <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center" role="status" aria-live="polite"><div className="text-center"><h1 className="text-2xl font-semibold text-white">Scanning in progress</h1><p className="text-slate-400 mt-2">Analyzing {scan.url}</p></div></div>;
  }

  if (!scan) return null;

  const failedCount = issues.failed?.length || 0;
  const passedCount = issues.passed?.length || 0;
  const incompleteCount = issues.incomplete?.length || 0;
  const metadata = scan.scan_metadata || {};

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" aria-labelledby="results-heading">
        {error && <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-200" role="alert">{error}</div>}

        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6" aria-labelledby="results-heading">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 id="results-heading" className="text-2xl font-bold text-white">Scan Results</h1>
              <p className="text-slate-300 break-all mt-2">{scan.url}</p>
              <p className="text-slate-500 text-sm mt-1">{formatDate(scan.createdAt)}</p>
            </div>
            <div className="text-right">
              <div className={`text-5xl font-bold ${getScoreColorClass(scan.score)}`}>{scan.score}<span className="text-lg text-slate-500">/100</span></div>
              <p className="text-xs text-slate-400 mt-2">{metadata.score_name || 'Auditly Accessibility Health Score'}</p>
            </div>
          </div>
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-sky-500/20 bg-sky-500/10 p-3 text-sm text-sky-100">
            <Info className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
            <p>{metadata.score_disclaimer || 'This automated score is a prioritisation aid, not a WCAG conformance certification. Manual testing is still required.'}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3 mt-6 pt-6 border-t border-slate-800">
            <button onClick={handleExportJSON} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"><Download className="w-4 h-4" aria-hidden="true" />Export JSON</button>
            {user?.plan === 'pro' ? (
              <button onClick={handleExportPDF} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"><FileText className="w-4 h-4" aria-hidden="true" />Export PDF</button>
            ) : (
              <Link to="/pricing" className="flex items-center gap-2 bg-slate-700 text-slate-200 px-4 py-2 rounded-lg"><Lock className="w-4 h-4" aria-hidden="true" />PDF (Pro)</Link>
            )}
          </div>
        </section>

        {screenshotUrl && (
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6" aria-labelledby="visual-evidence-heading">
            <h2 id="visual-evidence-heading" className="text-xl font-semibold text-white mb-3">Visual evidence</h2>
            <p className="text-sm text-slate-400 mb-4">Highlighted areas show a sample of elements associated with automated violations.</p>
            <a href={screenshotUrl} target="_blank" rel="noreferrer" className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded-lg">
              <img src={screenshotUrl} alt={`Full-page evidence captured during the accessibility scan of ${scan.url}`} className="w-full max-h-[520px] object-contain bg-white rounded-lg" />
            </a>
          </section>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6" aria-label="Scan summary">
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-red-400">{failedCount}</div><div className="text-red-300 text-sm">Failed rules</div></div>
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-emerald-400">{passedCount}</div><div className="text-emerald-300 text-sm">Passed rules</div></div>
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-amber-400">{incompleteCount}</div><div className="text-amber-300 text-sm">Needs review</div></div>
        </div>

        <section className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden" aria-labelledby="issues-heading">
          <h2 id="issues-heading" className="sr-only">Accessibility findings</h2>
          <div className="flex border-b border-slate-800" role="tablist" aria-label="Finding categories">
            {TABS.map((tab, index) => {
              const selected = activeTab === tab;
              const count = tab === 'failed' ? failedCount : tab === 'passed' ? passedCount : incompleteCount;
              const label = tab === 'incomplete' ? 'Needs Review' : `${tab.charAt(0).toUpperCase()}${tab.slice(1)}`;
              return (
                <button
                  key={tab}
                  ref={(node) => { tabRefs.current[index] = node; }}
                  id={`tab-${tab}`}
                  aria-controls={`panel-${tab}`}
                  role="tab"
                  aria-selected={selected}
                  tabIndex={selected ? 0 : -1}
                  onClick={() => setActiveTab(tab)}
                  onKeyDown={(event) => onTabKeyDown(event, index)}
                  className={`flex-1 px-4 py-4 text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-400 ${selected ? 'bg-slate-800 text-white border-b-2 border-emerald-400' : 'text-slate-400 hover:text-white'}`}
                >{label} ({count})</button>
              );
            })}
          </div>

          <div id={`panel-${activeTab}`} role="tabpanel" aria-labelledby={`tab-${activeTab}`} tabIndex={0} className="p-6 focus:outline-none">
            {!issues[activeTab]?.length ? <p className="text-center py-12 text-slate-400">No {activeTab} tests found.</p> : (
              <div className="space-y-5">
                {issues[activeTab].map((issue, idx) => {
                  const guidance = getRemediationGuidance(issue);
                  const wcagTags = (issue.wcag || []).filter((tag) => tag.startsWith('wcag'));
                  return (
                    <article key={`${issue.id}-${idx}`} className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
                      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                        <div><h3 className="text-white font-semibold">{issue.help || issue.id}</h3><p className="text-xs text-slate-500 mt-1">Rule: {issue.id}{issue.count ? ` · ${issue.count} affected element${issue.count === 1 ? '' : 's'}` : ''}</p></div>
                        {issue.impact && <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactColorClass(issue.impact)}`}>{issue.impact}</span>}
                      </div>
                      <p className="text-slate-300 text-sm mb-3">{issue.description}</p>

                      {wcagTags.length > 0 && <div className="flex flex-wrap gap-2 mb-3" aria-label="WCAG references">{wcagTags.map((tag) => <span key={tag} className="text-xs rounded bg-slate-700 px-2 py-1 text-slate-200">{tag}</span>)}</div>}

                      {guidance && <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 my-3"><p className="text-emerald-200 text-sm"><strong>Recommended fix:</strong> {guidance}</p></div>}

                      {issue.elements?.length > 0 && (
                        <details className="mt-4">
                          <summary className="cursor-pointer text-sm font-medium text-sky-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">Affected elements ({issue.elements.length})</summary>
                          <div className="space-y-3 mt-3">
                            {issue.elements.slice(0, 10).map((element, elementIndex) => (
                              <div key={elementIndex} className="rounded-lg bg-slate-950 p-3 border border-slate-800">
                                {element.target?.length > 0 && <p className="text-xs text-slate-400 mb-2"><strong>Selector:</strong> <code className="text-sky-300 break-all">{element.target.join(' → ')}</code></p>}
                                {element.html && <pre className="text-xs text-slate-200 whitespace-pre-wrap break-all overflow-x-auto"><code>{element.html}</code></pre>}
                                {element.failureSummary && <p className="text-sm text-amber-100 mt-3 whitespace-pre-line">{element.failureSummary}</p>}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}

                      {issue.helpUrl && <a href={issue.helpUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 mt-4 text-sm text-sky-300 underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">Rule documentation <ExternalLink className="w-3 h-3" aria-hidden="true" /></a>}
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};

export default ScanResultsPage;
