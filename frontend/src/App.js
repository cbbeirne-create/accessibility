import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
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

// Scan Page Component
const ScanPage = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState(""); // "success" or "error"
  const [currentScan, setCurrentScan] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setMessage("");
    setCurrentScan(null);

    try {
      const response = await axios.post(`${API}/scans`, {
        url: url.trim(),
        tool: "axe-core"
      });

      setCurrentScan(response.data);
      setMessage("Scan started successfully! Please wait while we analyze the website...");
      setMessageType("success");
      setUrl("");

      // Poll for scan completion
      pollScanStatus(response.data.id);

    } catch (error) {
      console.error("Error creating scan:", error);
      setMessage("Failed to start scan. Please check the URL and try again.");
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  };

  const pollScanStatus = async (scanId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API}/scans/${scanId}`);
        const scan = response.data;
        setCurrentScan(scan);

        if (scan.status === "completed") {
          clearInterval(pollInterval);
          setMessage("Scan completed successfully!");
          setMessageType("success");
        } else if (scan.status === "error") {
          clearInterval(pollInterval);
          setMessage(`Scan failed: ${scan.error_message || "Unknown error"}`);
          setMessageType("error");
        }
      } catch (error) {
        console.error("Error polling scan status:", error);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds
  };

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

      {currentScan && (
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-4">Scan Results</h3>
          <div className="space-y-4">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-gray-800 break-all">{currentScan.url}</h4>
                <p className="text-sm text-gray-500">
                  {new Date(currentScan.createdAt).toLocaleString()}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Tool: {currentScan.tool || "axe-core"}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(currentScan.status)}`}>
                {currentScan.status}
              </span>
            </div>

            {currentScan.status === "pending" && (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-gray-600">Scanning in progress...</span>
              </div>
            )}

            {currentScan.score !== null && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Accessibility Score</span>
                  <span className={`text-2xl font-bold ${getScoreColor(currentScan.score)}`}>
                    {currentScan.score}/100
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      currentScan.score >= 80 ? 'bg-green-500' : 
                      currentScan.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${currentScan.score}%` }}
                  ></div>
                </div>
              </div>
            )}

            {currentScan.issues && (
              <div className="mt-6">
                <h5 className="text-lg font-medium text-gray-800 mb-3">Detailed Results</h5>
                
                {currentScan.issues.violations && currentScan.issues.violations.length > 0 && (
                  <div className="mb-4">
                    <h6 className="text-md font-medium text-red-700 mb-2">
                      Violations ({currentScan.issues.violations.length})
                    </h6>
                    <div className="space-y-2">
                      {currentScan.issues.violations.slice(0, 5).map((violation, index) => (
                        <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h6 className="font-medium text-red-800">{violation.id}</h6>
                              <p className="text-sm text-red-600 mt-1">{violation.description}</p>
                              <div className="flex items-center space-x-4 mt-2 text-xs text-red-500">
                                <span>Impact: {violation.impact}</span>
                                <span>Nodes: {violation.nodes ? violation.nodes.length : 0}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                      {currentScan.issues.violations.length > 5 && (
                        <p className="text-sm text-gray-500">
                          ... and {currentScan.issues.violations.length - 5} more violations
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {currentScan.issues.passes ? currentScan.issues.passes.length : 0}
                    </div>
                    <div className="text-sm text-green-700">Passed Tests</div>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {currentScan.issues.violations ? currentScan.issues.violations.length : 0}
                    </div>
                    <div className="text-sm text-red-700">Violations</div>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {currentScan.issues.incomplete ? currentScan.issues.incomplete.length : 0}
                    </div>
                    <div className="text-sm text-yellow-700">Incomplete</div>
                  </div>
                </div>
              </div>
            )}

            {currentScan.error_message && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h6 className="font-medium text-red-800 mb-2">Error Details</h6>
                <p className="text-sm text-red-600">{currentScan.error_message}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Dashboard Component (existing home page)
const Dashboard = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
              <div key={scan.id} className="bg-white rounded-lg shadow-md p-6">
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
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(scan.status)}`}>
                    {scan.status}
                  </span>
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
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;