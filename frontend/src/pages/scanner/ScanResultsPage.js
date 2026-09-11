import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Download, FileText, Info, Lock, ExternalLink, Code2, Image as ImageIcon, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scansAPI } from '../../services/api';
import { formatDate, getImpactColorClass, getRemediationGuidance, getScoreColorClass } from '../../utils/wcag';

const tabs = ['failed', 'passed', 'incomplete'];

const ScanResultsPage = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('failed');
  const [screenshotUrl, setScreenshotUrl] = useState(null);

  useEffect(() => {
    let cancelled = false;
    let timer;
    const load = async () => {
      try {
        const data = await scansAPI.getById(id);
        if (cancelled) return;
        setScan(data);
        setError('');
        if (data.status === 'pending') {
          timer = window.setTimeout(load, 2500);
        }
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.detail || 'Failed to load scan results');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; if (timer) window.clearTimeout(timer); };
  }, [id]);

  useEffect(() => {
    let objectUrl;
    if (scan?.status !== 'completed') return undefined;
    scansAPI.getScreenshot(id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setScreenshotUrl(objectUrl);
      })
      .catch(() => setScreenshotUrl(null));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [id, scan?.status]);

  const issues = scan?.issues || { failed: [], passed: [], incomplete: [] };
  const counts = useMemo(() => ({
    failed: issues.failed?.length || 0,
    passed: issues.passed?.length || 0,
    incomplete: issues.incomplete?.length || 0,
  }), [issues]);

  const selectTab = (tab) => {
    setActiveTab(tab);
    window.requestAnimationFrame(() => document.getElementById(`results-tab-${tab}`)?.focus());
  };

  const onTabKeyDown = (event, tab) => {
    const index = tabs.indexOf(tab);
    if (event.key === 'ArrowRight') { event.preventDefault(); selectTab(tabs[(index + 1) % tabs.length]); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); selectTab(tabs[(index - 1 + tabs.length) % tabs.length]); }
    if (event.key === 'Home') { event.preventDefault(); selectTab(tabs[0]); }
    if (event.key === 'End') { event.preventDefault(); selectTab(tabs[tabs.length - 1]); }
  };

  const handleExportPDF = async () => {
    const blob = await scansAPI.exportPDF(id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `auditly-report-${id}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = async () => {
    const data = await scansAPI.exportJSON(id);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `auditly-data-${id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <StatusScreen title="Loading scan results…" />;
  if (error || !scan) return <StatusScreen title="Unable to load results" detail={error || 'Scan not found'} error />;
  if (scan.status === 'pending') return <StatusScreen title="Scan in progress" detail={`Analysing ${scan.url}`} />;
  if (scan.status === 'error') return <StatusScreen title="Scan failed" detail={scan.error_message || 'The scanner could not complete this audit.'} error />;

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" aria-labelledby="results-heading">
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6" aria-labelledby="results-heading">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div className="min-w-0">
              <h1 id="results-heading" className="text-2xl font-bold text-white mb-2">Accessibility scan results</h1>
              <p className="text-slate-300 break-all">{scan.url}</p>
              <p className="text-slate-500 text-sm mt-1">{formatDate(scan.createdAt)}</p>
            </div>
            <div className="text-right">
              <p className="text-slate-400 text-xs uppercase tracking-wide">Auditly Accessibility Health Score</p>
              <div className={`text-5xl font-bold ${getScoreColorClass(scan.score)}`}>{scan.score}<span className="text-lg text-slate-500">/100</span></div>
            </div>
          </div>
          <div className="mt-5 rounded-lg border border-slate-700 bg-slate-950/60 p-3 flex gap-2 text-sm text-slate-300">
            <Info className="w-4 h-4 mt-0.5 flex-none text-sky-400" aria-hidden="true" />
            <p>This automated health score is not a WCAG compliance percentage or certification. Automated tools cannot test every WCAG requirement; items marked “Needs review” require human assessment.</p>
          </div>
          <div className="flex flex-wrap gap-3 mt-6 pt-6 border-t border-slate-800">
            <button onClick={handleExportJSON} className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
              <Download className="w-4 h-4" aria-hidden="true" /><span>Export JSON</span>
            </button>
            {user?.plan === 'pro' ? (
              <button onClick={handleExportPDF} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300">
                <FileText className="w-4 h-4" aria-hidden="true" /><span>Export PDF</span>
              </button>
            ) : (
              <Link to="/pricing" className="flex items-center gap-2 bg-slate-700 text-slate-200 px-4 py-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
                <Lock className="w-4 h-4" aria-hidden="true" /><span>PDF export — Pro</span>
              </Link>
            )}
          </div>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6" aria-label="Scan summary">
          <SummaryCard label="Failed rules" value={counts.failed} classes="text-red-300 border-red-500/20 bg-red-500/10" />
          <SummaryCard label="Passed rules" value={counts.passed} classes="text-emerald-300 border-emerald-500/20 bg-emerald-500/10" />
          <SummaryCard label="Needs review" value={counts.incomplete} classes="text-amber-300 border-amber-500/20 bg-amber-500/10" />
        </section>

        {screenshotUrl && (
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6" aria-labelledby="visual-evidence-heading">
            <h2 id="visual-evidence-heading" className="text-lg font-semibold text-white flex items-center gap-2"><ImageIcon className="w-5 h-5" aria-hidden="true" />Visual evidence</h2>
            <p className="text-sm text-slate-400 mt-1 mb-4">Failing elements are outlined where the scanner could map the rule back to a DOM selector.</p>
            <img src={screenshotUrl} alt={`Full-page screenshot of ${scan.url} captured during the accessibility scan`} className="w-full rounded-lg border border-slate-700" />
          </section>
        )}

        <section className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden" aria-label="Detailed accessibility checks">
          <div className="flex border-b border-slate-800" role="tablist" aria-label="Result categories">
            {tabs.map((tab) => (
              <button
                id={`results-tab-${tab}`}
                key={tab}
                type="button"
                onClick={() => selectTab(tab)}
                onKeyDown={(event) => onTabKeyDown(event, tab)}
                role="tab"
                aria-selected={activeTab === tab}
                aria-controls={`results-panel-${tab}`}
                tabIndex={activeTab === tab ? 0 : -1}
                className={`flex-1 px-3 sm:px-6 py-4 text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-400 ${activeTab === tab ? 'bg-slate-800 text-white border-b-2 border-emerald-400' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
              >
                {tab === 'failed' ? `Failed (${counts.failed})` : tab === 'passed' ? `Passed (${counts.passed})` : `Needs review (${counts.incomplete})`}
              </button>
            ))}
          </div>
          <div id={`results-panel-${activeTab}`} role="tabpanel" aria-labelledby={`results-tab-${activeTab}`} tabIndex={0} className="p-4 sm:p-6 focus:outline-none">
            {!issues[activeTab]?.length ? (
              <p className="text-center py-12 text-slate-400">No {activeTab === 'incomplete' ? 'manual review' : activeTab} checks found.</p>
            ) : (
              <div className="space-y-5">
                {issues[activeTab].map((issue) => <IssueCard key={issue.id} issue={issue} scan={scan} />)}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};

const SummaryCard = ({ label, value, classes }) => (
  <div className={`border rounded-xl p-4 text-center ${classes}`}>
    <div className="text-3xl font-bold">{value}</div><div className="text-sm">{label}</div>
  </div>
);

const IssueCard = ({ issue, scan }) => {
  const guidance = getRemediationGuidance(issue);
  const elements = issue.elements || [];
  const wcagTags = (issue.wcag || []).filter((tag) => /^wcag\d+/i.test(tag));
  const evidenceEntries = Object.entries(scan.evidence_screenshots || {});
  const evidence = evidenceEntries.find(([key]) => key.startsWith(`${issue.id}_`))?.[1];
  const evidenceUrl = Object.entries(scan.evidence_screenshot_urls || {}).find(([key]) => key.startsWith(`${issue.id}_`))?.[1];

  return (
    <article className="bg-slate-800/50 rounded-xl p-5 border border-slate-800" aria-labelledby={`issue-${issue.id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div>
          <h3 id={`issue-${issue.id}`} className="text-white font-semibold">{issue.help || issue.id}</h3>
          <p className="text-slate-500 text-xs mt-1 font-mono">{issue.id}</p>
        </div>
        {issue.impact && <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactColorClass(issue.impact)}`}>{issue.impact}</span>}
      </div>
      <p className="text-slate-300 text-sm">{issue.description}</p>
      <div className="flex flex-wrap gap-2 mt-3 text-xs">
        {issue.count != null && <span className="rounded bg-slate-700 px-2 py-1 text-slate-300">{issue.count} affected element{issue.count === 1 ? '' : 's'}</span>}
        {wcagTags.map((tag) => <span key={tag} className="rounded bg-sky-500/10 border border-sky-500/20 px-2 py-1 text-sky-300">{tag.toUpperCase()}</span>)}
      </div>

      {guidance && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 mt-4">
          <div className="flex items-start gap-2"><Info className="w-4 h-4 text-emerald-400 flex-none mt-0.5" aria-hidden="true" /><div><p className="text-emerald-200 text-sm font-medium">How to fix it</p><p className="text-emerald-300 text-sm mt-1">{guidance}</p></div></div>
        </div>
      )}

      {elements.length > 0 && (
        <details className="mt-4 group">
          <summary className="cursor-pointer text-sm text-slate-200 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded inline-flex items-center gap-2"><Code2 className="w-4 h-4" aria-hidden="true" />Affected DOM elements</summary>
          <div className="mt-3 space-y-3">
            {elements.slice(0, 5).map((element, index) => (
              <div key={`${issue.id}-${index}`} className="rounded-lg bg-slate-950 border border-slate-700 p-3">
                {element.target?.length > 0 && <p className="text-xs text-sky-300 font-mono break-all mb-2">Selector: {element.target.join(' → ')}</p>}
                {element.html && <pre className="text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap break-all"><code>{element.html}</code></pre>}
                {element.failureSummary && <p className="text-xs text-amber-200 mt-2 whitespace-pre-line">{element.failureSummary}</p>}
              </div>
            ))}
          </div>
        </details>
      )}

      {(evidence || evidenceUrl) && (
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-slate-200 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded inline-flex items-center gap-2"><ImageIcon className="w-4 h-4" aria-hidden="true" />Issue screenshot</summary>
          <img src={evidenceUrl || `data:image/png;base64,${evidence}`} alt={`Visual evidence for ${issue.help || issue.id}`} className="mt-3 max-w-full rounded-lg border border-slate-700" />
        </details>
      )}

      {issue.helpUrl && (
        <a href={issue.helpUrl} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-1 text-sm text-sky-300 hover:text-sky-200 underline underline-offset-2">Technical rule documentation <ExternalLink className="w-3 h-3" aria-hidden="true" /><span className="sr-only"> (opens in a new tab)</span></a>
      )}
    </article>
  );
};

const StatusScreen = ({ title, detail, error = false }) => (
  <main id="main-content" className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4" aria-live="polite">
    <div className="text-center max-w-xl">
      {error ? <X className="w-12 h-12 text-red-400 mx-auto mb-4" aria-hidden="true" /> : <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" />}
      <h1 className="text-xl font-semibold text-white mt-4">{title}</h1>
      {detail && <p className="text-slate-400 mt-2 break-words">{detail}</p>}
    </div>
  </main>
);

export default ScanResultsPage;
