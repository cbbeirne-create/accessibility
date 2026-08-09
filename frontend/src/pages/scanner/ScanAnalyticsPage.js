/**
 * Scan Analytics Page
 * 
 * Displays scan statistics, trends, and comparison features.
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader friendly charts and stats
 */
import React, { useState, useEffect } from 'react';
import { Globe, BarChart3, ArrowRight, Check } from 'lucide-react';
import { scansAPI } from '../../services/api';
import { formatDate, getScoreColorClass, getScoreBgClass } from '../../utils/wcag';

const ScanAnalyticsPage = () => {
  const [stats, setStats] = useState(null);
  const [scannedUrls, setScannedUrls] = useState([]);
  const [selectedUrl, setSelectedUrl] = useState(null);
  const [urlHistory, setUrlHistory] = useState(null);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedScans, setSelectedScans] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, urlsData] = await Promise.all([
          scansAPI.getStats(),
          scansAPI.getScannedUrls()
        ]);
        setStats(statsData);
        setScannedUrls(urlsData.urls || []);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleUrlSelect = async (url) => {
    setSelectedUrl(url);
    setHistoryLoading(true);
    setComparison(null);
    setSelectedScans([]);
    setCompareMode(false);
    try {
      const history = await scansAPI.getHistoryByUrl(url);
      setUrlHistory(history);
    } catch (err) {
      console.error('Failed to load URL history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleScanSelect = (scanId) => {
    if (!compareMode) return;
    
    if (selectedScans.includes(scanId)) {
      setSelectedScans(selectedScans.filter(id => id !== scanId));
    } else if (selectedScans.length < 2) {
      setSelectedScans([...selectedScans, scanId]);
    }
  };

  const handleCompare = async () => {
    if (selectedScans.length !== 2) return;
    setCompareLoading(true);
    try {
      const result = await scansAPI.compare(selectedScans[0], selectedScans[1]);
      setComparison(result);
    } catch (err) {
      console.error('Failed to compare scans:', err);
      alert('Failed to compare scans. Please try again.');
    } finally {
      setCompareLoading(false);
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
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" role="main" aria-labelledby="analytics-heading">
        {/* Header */}
        <div className="mb-8">
          <h1 id="analytics-heading" className="text-3xl font-bold text-white mb-2">Scan Analytics</h1>
          <p className="text-slate-400">Track your accessibility progress over time</p>
        </div>

        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="text-3xl font-bold text-white mb-1">{stats.total_scans}</div>
              <div className="text-slate-400 text-sm">Total Scans</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className={`text-3xl font-bold ${getScoreColorClass(stats.average_score)}`}>
                {stats.average_score}
              </div>
              <div className="text-slate-400 text-sm">Average Score</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="text-3xl font-bold text-emerald-400">{stats.best_score}</div>
              <div className="text-slate-400 text-sm">Best Score</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <div className="text-3xl font-bold text-white">{stats.unique_urls}</div>
              <div className="text-slate-400 text-sm">Unique URLs</div>
            </div>
          </div>
        )}

        {/* Trend Indicator */}
        {stats?.recent_trend && (
          <div className={`mb-8 p-4 rounded-xl border ${
            stats.recent_trend.direction === 'up' 
              ? 'bg-emerald-500/10 border-emerald-500/20' 
              : stats.recent_trend.direction === 'down'
              ? 'bg-red-500/10 border-red-500/20'
              : 'bg-slate-800 border-slate-700'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                stats.recent_trend.direction === 'up' 
                  ? 'bg-emerald-500/20' 
                  : stats.recent_trend.direction === 'down'
                  ? 'bg-red-500/20'
                  : 'bg-slate-700'
              }`}>
                {stats.recent_trend.direction === 'up' ? (
                  <ArrowRight className="w-5 h-5 text-emerald-400 rotate-[-45deg]" aria-hidden="true" />
                ) : stats.recent_trend.direction === 'down' ? (
                  <ArrowRight className="w-5 h-5 text-red-400 rotate-[45deg]" aria-hidden="true" />
                ) : (
                  <ArrowRight className="w-5 h-5 text-slate-400" aria-hidden="true" />
                )}
              </div>
              <div>
                <div className={`font-medium ${
                  stats.recent_trend.direction === 'up' 
                    ? 'text-emerald-300' 
                    : stats.recent_trend.direction === 'down'
                    ? 'text-red-300'
                    : 'text-slate-300'
                }`}>
                  {stats.recent_trend.direction === 'up' 
                    ? 'Improving!' 
                    : stats.recent_trend.direction === 'down'
                    ? 'Declining'
                    : 'Stable'}
                </div>
                <div className="text-sm text-slate-400">
                  Recent average: {stats.recent_trend.recent_average} | Previous: {stats.recent_trend.older_average}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Score History Chart */}
        {stats?.score_history && stats.score_history.length > 1 && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">Score History</h2>
            <div className="flex items-end space-x-2 h-40">
              {stats.score_history.map((item, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center">
                  <div 
                    className={`w-full rounded-t transition-all ${getScoreBgClass(item.score)}`}
                    style={{ height: `${item.score}%` }}
                    title={`${item.score} - ${formatDate(item.date)}`}
                  >
                    <div className={`text-xs font-medium text-center pt-1 ${getScoreColorClass(item.score)}`}>
                      {item.score}
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1 truncate w-full text-center">
                    {new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* URL List with History */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* URL List */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Scanned URLs</h2>
            {scannedUrls.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Globe className="w-10 h-10 mx-auto mb-3 opacity-50" aria-hidden="true" />
                <p>No scans yet. Start scanning to see your history!</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {scannedUrls.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleUrlSelect(item.url)}
                    className={`w-full text-left p-3 rounded-lg transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
                      selectedUrl === item.url 
                        ? 'bg-emerald-500/20 border border-emerald-500/30' 
                        : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                    }`}
                  >
                    <div className="text-white text-sm font-medium truncate">{item.url}</div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-slate-400 text-xs">{item.scan_count} scan{item.scan_count !== 1 ? 's' : ''}</span>
                      <span className={`text-sm font-medium ${getScoreColorClass(item.latest_score)}`}>
                        {item.latest_score}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* URL History / Comparison */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            {historyLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400" aria-hidden="true" />
              </div>
            ) : urlHistory ? (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">Scan History</h2>
                  {urlHistory.scans.length >= 2 && (
                    <button
                      onClick={() => {
                        setCompareMode(!compareMode);
                        setSelectedScans([]);
                        setComparison(null);
                      }}
                      className={`text-sm px-3 py-1.5 rounded-lg transition-all ${
                        compareMode 
                          ? 'bg-emerald-500 text-white' 
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      {compareMode ? 'Cancel Compare' : 'Compare Scans'}
                    </button>
                  )}
                </div>

                {/* Trend Summary */}
                {urlHistory.trend && (
                  <div className={`mb-4 p-3 rounded-lg ${
                    urlHistory.trend.direction === 'up' 
                      ? 'bg-emerald-500/10' 
                      : urlHistory.trend.direction === 'down'
                      ? 'bg-red-500/10'
                      : 'bg-slate-800'
                  }`}>
                    <div className="flex items-center justify-between text-sm">
                      <span className={`font-medium ${
                        urlHistory.trend.direction === 'up' 
                          ? 'text-emerald-300' 
                          : urlHistory.trend.direction === 'down'
                          ? 'text-red-300'
                          : 'text-slate-300'
                      }`}>
                        {urlHistory.trend.direction === 'up' ? '↗' : urlHistory.trend.direction === 'down' ? '↘' : '→'} 
                        {' '}{urlHistory.trend.change > 0 ? '+' : ''}{urlHistory.trend.change} points
                      </span>
                      <span className="text-slate-400">
                        Avg: {urlHistory.trend.average_score} | Best: {urlHistory.trend.best_score}
                      </span>
                    </div>
                  </div>
                )}

                {/* Compare Mode Instructions */}
                {compareMode && (
                  <div className="mb-4 p-3 bg-amber-500/10 rounded-lg text-sm text-amber-200">
                    Select 2 scans to compare. Selected: {selectedScans.length}/2
                    {selectedScans.length === 2 && (
                      <button
                        onClick={handleCompare}
                        disabled={compareLoading}
                        className="ml-3 bg-emerald-500 text-white px-3 py-1 rounded text-xs font-medium hover:bg-emerald-600"
                      >
                        {compareLoading ? 'Comparing...' : 'Compare Now'}
                      </button>
                    )}
                  </div>
                )}

                {/* Scan List */}
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {urlHistory.scans.map((scan, idx) => (
                    <div
                      key={scan.id}
                      onClick={() => handleScanSelect(scan.id)}
                      className={`p-3 rounded-lg border transition-all ${
                        compareMode ? 'cursor-pointer' : ''
                      } ${
                        selectedScans.includes(scan.id)
                          ? 'bg-emerald-500/20 border-emerald-500/30'
                          : 'bg-slate-800/50 border-transparent hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {compareMode && (
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                              selectedScans.includes(scan.id)
                                ? 'bg-emerald-500 border-emerald-500'
                                : 'border-slate-600'
                            }`}>
                              {selectedScans.includes(scan.id) && (
                                <Check className="w-3 h-3 text-white" aria-hidden="true" />
                              )}
                            </div>
                          )}
                          <div>
                            <div className="text-white text-sm">
                              {formatDate(scan.createdAt)}
                            </div>
                            {scan.issues_summary && (
                              <div className="text-xs text-slate-400">
                                {scan.issues_summary.failed} failed | {scan.issues_summary.passed} passed
                              </div>
                            )}
                          </div>
                        </div>
                        <div className={`text-lg font-bold ${getScoreColorClass(scan.score)}`}>
                          {scan.score}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Comparison Results */}
                {comparison && (
                  <div className="mt-6 pt-6 border-t border-slate-700">
                    <h3 className="text-white font-semibold mb-4">Comparison Results</h3>
                    
                    {/* Score Change */}
                    <div className={`p-4 rounded-lg mb-4 ${
                      comparison.comparison.improved 
                        ? 'bg-emerald-500/10' 
                        : comparison.comparison.score_change < 0
                        ? 'bg-red-500/10'
                        : 'bg-slate-800'
                    }`}>
                      <div className="text-center">
                        <div className={`text-3xl font-bold ${
                          comparison.comparison.improved 
                            ? 'text-emerald-400' 
                            : comparison.comparison.score_change < 0
                            ? 'text-red-400'
                            : 'text-slate-400'
                        }`}>
                          {comparison.comparison.score_change > 0 ? '+' : ''}{comparison.comparison.score_change}
                        </div>
                        <div className="text-sm text-slate-400">
                          {comparison.comparison.older_scan.score} → {comparison.comparison.newer_scan.score}
                        </div>
                      </div>
                    </div>

                    {/* Issue Summary */}
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div className="bg-emerald-500/10 rounded-lg p-3">
                        <div className="text-xl font-bold text-emerald-400">{comparison.summary.issues_fixed}</div>
                        <div className="text-xs text-emerald-300">Fixed</div>
                      </div>
                      <div className="bg-red-500/10 rounded-lg p-3">
                        <div className="text-xl font-bold text-red-400">{comparison.summary.new_issues}</div>
                        <div className="text-xs text-red-300">New Issues</div>
                      </div>
                      <div className="bg-slate-700 rounded-lg p-3">
                        <div className="text-xl font-bold text-slate-300">{comparison.summary.unchanged_issues}</div>
                        <div className="text-xs text-slate-400">Unchanged</div>
                      </div>
                    </div>

                    {/* Fixed Issues List */}
                    {comparison.issues.fixed.count > 0 && (
                      <div className="mt-4">
                        <h4 className="text-emerald-400 text-sm font-medium mb-2">
                          Fixed Issues ({comparison.issues.fixed.count})
                        </h4>
                        <div className="space-y-1 max-h-32 overflow-y-auto">
                          {comparison.issues.fixed.items.slice(0, 5).map((issue, idx) => (
                            <div key={idx} className="text-xs text-slate-300 bg-slate-800/50 px-2 py-1 rounded">
                              {issue.id}: {issue.description?.slice(0, 60)}...
                            </div>
                          ))}
                          {comparison.issues.fixed.count > 5 && (
                            <div className="text-xs text-slate-500">
                              +{comparison.issues.fixed.count - 5} more
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* New Issues List */}
                    {comparison.issues.new.count > 0 && (
                      <div className="mt-4">
                        <h4 className="text-red-400 text-sm font-medium mb-2">
                          New Issues ({comparison.issues.new.count})
                        </h4>
                        <div className="space-y-1 max-h-32 overflow-y-auto">
                          {comparison.issues.new.items.slice(0, 5).map((issue, idx) => (
                            <div key={idx} className="text-xs text-slate-300 bg-slate-800/50 px-2 py-1 rounded">
                              {issue.id}: {issue.description?.slice(0, 60)}...
                            </div>
                          ))}
                          {comparison.issues.new.count > 5 && (
                            <div className="text-xs text-slate-500">
                              +{comparison.issues.new.count - 5} more
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-64 text-slate-400">
                <div className="text-center">
                  <BarChart3 className="w-10 h-10 mx-auto mb-3 opacity-50" aria-hidden="true" />
                  <p>Select a URL to view its scan history</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ScanAnalyticsPage;
