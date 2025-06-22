import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = () => {
  return (
    <nav className="bg-blue-600 text-white p-4 mb-8">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">Accessibility Scanner</h1>
        <div className="space-x-4">
          <Link to="/" className="hover:text-blue-200 transition-colors">
            Dashboard
          </Link>
          <Link to="/scan" className="hover:text-blue-200 transition-colors">
            New Scan
          </Link>
        </div>
      </div>
    </nav>
  );
};

// Scan Results Page Component
const ScanResultsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchScanDetails();
    
    // If scan is pending, poll for updates
    const interval = setInterval(() => {
      if (scan && scan.status === "pending") {
        fetchScanDetails();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [id, scan?.status]);

  const fetchScanDetails = async () => {
    try {
      const response = await axios.get(`${API}/scans/${id}`);
      setScan(response.data);
      setError("");
    } catch (error) {
      console.error("Error fetching scan details:", error);
      setError("Failed to load scan details. The scan may not exist.");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackgroundColor = (score) => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'serious':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'minor':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatWcagReference = (tags) => {
    const wcagTags = tags.filter(tag => tag.startsWith('wcag'));
    return wcagTags.length > 0 ? wcagTags.join(', ').toUpperCase() : 'N/A';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Loading scan details...</p>
        </div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-red-800 mb-4">Scan Not Found</h2>
          <p className="text-red-600 mb-6">{error || "The requested scan could not be found."}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 max-w-6xl">
      {/* Header Section */}
      <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Accessibility Scan Results</h1>
            <h2 className="text-xl text-gray-600 break-all mb-4">{scan.url}</h2>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Scanned: {new Date(scan.createdAt).toLocaleString()}</span>
              <span>Tool: {scan.tool || "axe-core"}</span>
            </div>
          </div>
          <button
            onClick={() => navigate('/')}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>

      {/* Status-based Content */}
      {scan.status === 'pending' && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Scanning in progress...</h2>
          <p className="text-gray-600">Please wait while we analyze the website for accessibility issues.</p>
        </div>
      )}

      {scan.status === 'error' && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <div className="text-red-500 text-6xl mb-6">⚠️</div>
          <h2 className="text-2xl font-bold text-red-800 mb-4">Scan failed. Please try again later.</h2>
          <p className="text-gray-600 mb-6">
            {scan.error_message || "An unexpected error occurred during the accessibility scan."}
          </p>
          <button
            onClick={() => navigate('/scan')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Start New Scan
          </button>
        </div>
      )}

      {scan.status === 'completed' && (
        <div className="space-y-8">
          {/* Score Section */}
          <div className={`rounded-lg border-2 p-8 text-center ${getScoreBackgroundColor(scan.score)}`}>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Accessibility Score</h2>
            <div className={`text-6xl font-bold mb-4 ${getScoreColor(scan.score)}`}>
              {scan.score}/100
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
              <div
                className={`h-4 rounded-full ${
                  scan.score >= 80 ? 'bg-green-500' : 
                  scan.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${scan.score}%` }}
              ></div>
            </div>
            <p className="text-gray-700">
              {scan.score >= 80 ? 'Excellent accessibility!' : 
               scan.score >= 60 ? 'Good accessibility with room for improvement.' : 
               'Poor accessibility - immediate attention needed.'}
            </p>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-red-600 mb-2">
                {scan.issues?.violations ? scan.issues.violations.length : 0}
              </div>
              <div className="text-red-700 font-medium">Violations</div>
              <div className="text-sm text-red-600 mt-1">Issues that need fixing</div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {scan.issues?.passes ? scan.issues.passes.length : 0}
              </div>
              <div className="text-green-700 font-medium">Passed Tests</div>
              <div className="text-sm text-green-600 mt-1">Accessibility checks passed</div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {scan.issues?.incomplete ? scan.issues.incomplete.length : 0}
              </div>
              <div className="text-yellow-700 font-medium">Incomplete</div>
              <div className="text-sm text-yellow-600 mt-1">Manual review needed</div>
            </div>
          </div>

          {/* Violations Table */}
          {scan.issues?.violations && scan.issues.violations.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="bg-red-50 border-b border-red-200 px-8 py-4">
                <h3 className="text-xl font-bold text-red-800">Accessibility Violations</h3>
                <p className="text-red-600 text-sm mt-1">Issues that need immediate attention</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Issue Summary
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Impact
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        WCAG Reference
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Affected Elements
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {scan.issues.violations.map((violation, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="max-w-xs">
                            <div className="font-semibold text-gray-900 mb-1">{violation.id}</div>
                            <div className="text-sm text-gray-600">{violation.description}</div>
                            {violation.help && (
                              <div className="text-sm text-blue-600 mt-1">{violation.help}</div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getImpactColor(violation.impact)}`}>
                            {violation.impact || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {formatWcagReference(violation.tags || [])}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900">
                            {violation.nodes ? violation.nodes.length : 0} element(s)
                          </div>
                          {violation.nodes && violation.nodes.length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                                View elements
                              </summary>
                              <div className="mt-2 max-h-32 overflow-y-auto">
                                {violation.nodes.slice(0, 3).map((node, nodeIndex) => (
                                  <div key={nodeIndex} className="text-xs text-gray-500 mb-1 font-mono">
                                    {node.target ? node.target.join(', ') : 'N/A'}
                                  </div>
                                ))}
                                {violation.nodes.length > 3 && (
                                  <div className="text-xs text-gray-400">
                                    ... and {violation.nodes.length - 3} more
                                  </div>
                                )}
                              </div>
                            </details>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* No Violations Message */}
          {scan.issues?.violations && scan.issues.violations.length === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
              <div className="text-green-500 text-4xl mb-4">✅</div>
              <h3 className="text-xl font-bold text-green-800 mb-2">No Accessibility Violations Found!</h3>
              <p className="text-green-600">This website meets all tested accessibility standards.</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => navigate('/scan')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Run Another Scan
            </button>
            <button
              onClick={() => window.print()}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Print Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Scan Page Component
const ScanPage = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState(""); // "success" or "error"
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setMessage("");

    try {
      const response = await axios.post(`${API}/scans`, {
        url: url.trim(),
        tool: "axe-core"
      });

      setMessage("Scan started successfully! Redirecting to results page...");
      setMessageType("success");
      setUrl("");

      // Redirect to results page after a brief delay
      setTimeout(() => {
        navigate(`/scan-results/${response.data.id}`);
      }, 1500);

    } catch (error) {
      console.error("Error creating scan:", error);
      setMessage("Failed to start scan. Please check the URL and try again.");
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 max-w-4xl">
      <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-6">Run Accessibility Scan</h2>
        <p className="text-gray-600 mb-6">
          Enter a website URL below to analyze its accessibility compliance using axe-core.
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
              Website URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              required
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {loading ? "Starting Scan..." : "Run Accessibility Scan"}
          </button>
        </form>

        {message && (
          <div className={`mt-4 p-4 rounded-lg ${
            messageType === "success" 
              ? "bg-green-100 text-green-700 border border-green-200" 
              : "bg-red-100 text-red-700 border border-red-200"
          }`}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

// Dashboard Component (existing home page)
const Dashboard = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const fetchScans = async () => {
    try {
      const response = await axios.get(`${API}/scans`);
      setScans(response.data);
    } catch (error) {
      console.error("Error fetching scans:", error);
      setError("Failed to fetch scan results");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
    
    // Auto-refresh every 5 seconds for pending scans
    const interval = setInterval(fetchScans, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading scans...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Accessibility Scanner Dashboard
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          Monitor your website accessibility scans and compliance reports
        </p>
        <Link
          to="/scan"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          Run New Scan
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Scans</h2>
        {scans.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-500">No scans yet. Run your first accessibility scan!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {scans.map((scan) => (
              <div key={scan.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-800 break-all">{scan.url}</h3>
                    <p className="text-sm text-gray-500">
                      {new Date(scan.createdAt).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">
                      Tool: {scan.tool || "axe-core"}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(scan.status)}`}>
                      {scan.status}
                    </span>
                    <button
                      onClick={() => navigate(`/scan-results/${scan.id}`)}
                      className="bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium py-2 px-4 rounded-lg transition-colors text-sm"
                    >
                      View Details
                    </button>
                  </div>
                </div>
                
                {scan.score !== null && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Accessibility Score</span>
                      <span className={`text-2xl font-bold ${getScoreColor(scan.score)}`}>
                        {scan.score}/100
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          scan.score >= 80 ? 'bg-green-500' : 
                          scan.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${scan.score}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {scan.issues && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-green-600">
                        {scan.issues.passes ? scan.issues.passes.length : 0}
                      </div>
                      <div className="text-xs text-green-700">Passed</div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-red-600">
                        {scan.issues.violations ? scan.issues.violations.length : 0}
                      </div>
                      <div className="text-xs text-red-700">Violations</div>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-yellow-600">
                        {scan.issues.incomplete ? scan.issues.incomplete.length : 0}
                      </div>
                      <div className="text-xs text-yellow-700">Incomplete</div>
                    </div>
                  </div>
                )}

                {scan.error_message && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-600">{scan.error_message}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan" element={<ScanPage />} />
          <Route path="/scan-results/:id" element={<ScanResultsPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;