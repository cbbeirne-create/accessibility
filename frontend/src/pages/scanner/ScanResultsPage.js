/**
 * Scan Results Page
 * 
 * Displays detailed accessibility scan results with issue categorization.
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader friendly tabs and issue lists
 */
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { X, Download, FileText, Lock, Info } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { scansAPI } from '../../services/api';
import { 
  formatDate, 
  getScoreColorClass, 
  getImpactColorClass,
  getRemediationGuidance 
} from '../../utils/wcag';

const ScanResultsPage = () => {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("failed");
  const { user } = useAuth();

  useEffect(() => {
    const fetchScan = async () => {
      try {
        const data = await scansAPI.getById(id);
        setScan(data);
        
        // Poll if pending
        if (data.status === 'pending') {
          const interval = setInterval(async () => {
            const updated = await scansAPI.getById(id);
            setScan(updated);
            if (updated.status !== 'pending') {
              clearInterval(interval);
            }
          }, 3000);
          return () => clearInterval(interval);
        }
      } catch (err) {
        setError('Failed to load scan results');
      } finally {
        setLoading(false);
      }
    };
    fetchScan();
  }, [id]);

  const handleExportPDF = async () => {
    try {
      const blob = await scansAPI.exportPDF(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `accessibility-report-${id}.pdf`;
      a.click();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to export PDF');
    }
  };

  const handleExportJSON = async () => {
    try {
      const data = await scansAPI.exportJSON(id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `accessibility-data-${id}.json`;
      a.click();
    } catch (err) {
      alert('Failed to export JSON');
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" />
          <p className="mt-4 text-slate-300">Loading scan results...</p>
        </div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <X className="w-12 h-12 text-red-400 mx-auto mb-4" aria-hidden="true" />
          <h1 className="text-xl font-semibold text-white mb-2">Error Loading Results</h1>
          <p className="text-slate-400">{error || 'Scan not found'}</p>
        </div>
      </div>
    );
  }

  if (scan.status === 'pending') {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" />
          <h1 className="text-2xl font-semibold text-white mt-6 mb-2">Scanning in Progress</h1>
          <p className="text-slate-400 mb-4">Analyzing {scan.url}</p>
          <p className="text-slate-500 text-sm">This may take a minute...</p>
        </div>
      </div>
    );
  }

  const issues = scan.issues || { failed: [], passed: [], incomplete: [] };
  const failedCount = issues.failed?.length || 0;
  const passedCount = issues.passed?.length || 0;
  const incompleteCount = issues.incomplete?.length || 0;

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" role="main" aria-labelledby="results-heading">
        {/* Header */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 id="results-heading" className="text-2xl font-bold text-white mb-2">Scan Results</h1>
              <p className="text-slate-400 truncate max-w-xl">{scan.url}</p>
              <p className="text-slate-500 text-sm mt-1">{formatDate(scan.createdAt)}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`text-5xl font-bold ${getScoreColorClass(scan.score)}`}>
                {scan.score}
                <span className="text-lg text-slate-500">/100</span>
              </div>
            </div>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center space-x-3 mt-6 pt-6 border-t border-slate-800">
            <button
              onClick={handleExportJSON}
              className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              <Download className="w-4 h-4" aria-hidden="true" />
              <span>Export JSON</span>
            </button>
            {user?.plan === 'pro' ? (
              <button
                onClick={handleExportPDF}
                className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-4 py-2 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
              >
                <FileText className="w-4 h-4" aria-hidden="true" />
                <span>Export PDF</span>
              </button>
            ) : (
              <Link
                to="/pricing"
                className="flex items-center space-x-2 bg-slate-700 text-slate-300 px-4 py-2 rounded-lg"
              >
                <Lock className="w-4 h-4" aria-hidden="true" />
                <span>PDF (Pro)</span>
              </Link>
            )}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-red-400">{failedCount}</div>
            <div className="text-red-300 text-sm">Failed</div>
          </div>
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-emerald-400">{passedCount}</div>
            <div className="text-emerald-300 text-sm">Passed</div>
          </div>
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-amber-400">{incompleteCount}</div>
            <div className="text-amber-300 text-sm">Needs Review</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="flex border-b border-slate-800" role="tablist">
            {['failed', 'passed', 'incomplete'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                role="tab"
                aria-selected={activeTab === tab}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-inset ${
                  activeTab === tab
                    ? 'bg-slate-800 text-white border-b-2 border-emerald-400'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {tab === 'failed' && `Failed (${failedCount})`}
                {tab === 'passed' && `Passed (${passedCount})`}
                {tab === 'incomplete' && `Needs Review (${incompleteCount})`}
              </button>
            ))}
          </div>

          {/* Issues List */}
          <div className="p-6">
            {issues[activeTab]?.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                No {activeTab} tests found
              </div>
            ) : (
              <div className="space-y-4">
                {issues[activeTab]?.map((issue, idx) => (
                  <div key={idx} className="bg-slate-800/50 rounded-xl p-5">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-white font-medium">{issue.id}</h3>
                      {issue.impact && (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getImpactColorClass(issue.impact)}`}>
                          {issue.impact}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-300 text-sm mb-3">{issue.description}</p>
                    {issue.help && (
                      <p className="text-slate-400 text-sm mb-3">
                        <strong>Help:</strong> {issue.help}
                      </p>
                    )}
                    {getRemediationGuidance(issue) && (
                      <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 mt-3">
                        <div className="flex items-start space-x-2">
                          <Info className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                          <p className="text-emerald-300 text-sm">{getRemediationGuidance(issue)}</p>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ScanResultsPage;
