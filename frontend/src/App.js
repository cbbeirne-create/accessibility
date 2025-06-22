import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScanForm = ({ onScanSubmit, loading }) => {
  const [url, setUrl] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim()) {
      onScanSubmit(url.trim());
      setUrl("");
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Website Accessibility Scanner</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            Website URL to Scan
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
          {loading ? "Scanning..." : "Start Accessibility Scan"}
        </button>
      </form>
    </div>
  );
};

const ScanResult = ({ scan }) => {
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
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 break-all">{scan.url}</h3>
          <p className="text-sm text-gray-500">
            {new Date(scan.createdAt).toLocaleString()}
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

      {scan.issues && Object.keys(scan.issues).length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Issues Found</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(scan.issues, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchScans = async () => {
    try {
      const response = await axios.get(`${API}/scans`);
      setScans(response.data);
    } catch (error) {
      console.error("Error fetching scans:", error);
      setError("Failed to fetch scan results");
    }
  };

  const handleScanSubmit = async (url) => {
    setLoading(true);
    setError("");
    
    try {
      const response = await axios.post(`${API}/scans`, { url });
      console.log("Scan request created:", response.data);
      
      // Refresh the scans list
      await fetchScans();
      
      // For now, we'll simulate the scanning process
      // In a real implementation, this would be handled by a background worker
      setTimeout(async () => {
        try {
          // Simulate scan completion with mock data
          await axios.put(`${API}/scans/${response.data.id}`, {
            status: "completed",
            score: Math.floor(Math.random() * 40) + 60, // Random score between 60-100
            issues: {
              "violations": [
                {
                  "id": "color-contrast",
                  "description": "Elements must have sufficient color contrast",
                  "impact": "serious",
                  "nodes": 3
                },
                {
                  "id": "alt-text",
                  "description": "Images must have alternative text",
                  "impact": "critical",
                  "nodes": 1
                }
              ],
              "passes": 12,
              "incomplete": 2
            }
          });
          await fetchScans();
        } catch (error) {
          console.error("Error updating scan:", error);
        }
      }, 3000);
      
    } catch (error) {
      console.error("Error creating scan request:", error);
      setError("Failed to create scan request. Please check the URL and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScans();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Website Accessibility Scanner
          </h1>
          <p className="text-lg text-gray-600">
            Check your website's accessibility compliance and get detailed reports
          </p>
        </div>

        <ScanForm onScanSubmit={handleScanSubmit} loading={loading} />

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Scans</h2>
          {scans.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <p className="text-gray-500">No scans yet. Submit a URL above to get started!</p>
            </div>
          ) : (
            <div>
              {scans.map((scan) => (
                <ScanResult key={scan.id} scan={scan} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;