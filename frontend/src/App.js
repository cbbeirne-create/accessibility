import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// WCAG Remediation Guidance Dictionary
const WCAG_REMEDIATION = {
  // 1.1 Text Alternatives
  "1.1.1": "Add descriptive alt text to all meaningful images using the `alt` attribute. For decorative images, use an empty alt attribute (`alt=\"\"`).",
  "wcag111": "Add descriptive alt text to all meaningful images using the `alt` attribute. For decorative images, use an empty alt attribute (`alt=\"\"`).",
  
  // 1.3 Adaptable
  "1.3.1": "Use proper HTML semantic elements (headings, lists, tables) and ARIA roles to convey content structure and relationships.",
  "wcag131": "Use proper HTML semantic elements (headings, lists, tables) and ARIA roles to convey content structure and relationships.",
  
  // 1.4 Distinguishable
  "1.4.1": "Ensure information is not conveyed by color alone. Use text, icons, or patterns in addition to color.",
  "1.4.3": "Increase color contrast ratio to at least 4.5:1 for normal text and 3:1 for large text against the background.",
  "1.4.6": "Increase color contrast ratio to at least 7:1 for normal text and 4.5:1 for large text (enhanced contrast).",
  "wcag141": "Ensure information is not conveyed by color alone. Use text, icons, or patterns in addition to color.",
  "wcag143": "Increase color contrast ratio to at least 4.5:1 for normal text and 3:1 for large text against the background.",
  
  // 2.1 Keyboard Accessible
  "2.1.1": "Ensure all interactive elements are keyboard accessible using Tab, Enter, Space, and arrow keys.",
  "2.1.2": "Ensure users can exit any keyboard trap using standard navigation methods.",
  "wcag211": "Ensure all interactive elements are keyboard accessible using Tab, Enter, Space, and arrow keys.",
  "wcag212": "Ensure users can exit any keyboard trap using standard navigation methods.",
  
  // 2.4 Navigable
  "2.4.1": "Provide a 'Skip to main content' link and other skip navigation options for keyboard users.",
  "2.4.2": "Add a descriptive and unique `<title>` element to each page that describes the page topic or purpose.",
  "2.4.3": "Ensure the tab order follows a logical sequence that preserves meaning and operability.",
  "2.4.4": "Write clear, descriptive link text that makes sense out of context. Avoid generic text like 'click here' or 'read more'.",
  "2.4.6": "Use clear, descriptive headings and labels that describe the topic or purpose of content sections.",
  "2.4.7": "Ensure keyboard focus indicators are clearly visible with sufficient contrast and size.",
  "wcag241": "Provide a 'Skip to main content' link and other skip navigation options for keyboard users.",
  "wcag242": "Add a descriptive and unique `<title>` element to each page that describes the page topic or purpose.",
  "wcag243": "Ensure the tab order follows a logical sequence that preserves meaning and operability.",
  "wcag244": "Write clear, descriptive link text that makes sense out of context. Avoid generic text like 'click here' or 'read more'.",
  "wcag246": "Use clear, descriptive headings and labels that describe the topic or purpose of content sections.",
  "wcag247": "Ensure keyboard focus indicators are clearly visible with sufficient contrast and size.",
  
  // 3.1 Readable
  "3.1.1": "Add a `lang` attribute to the `<html>` element to specify the page language (e.g., `<html lang=\"en\">`).",
  "3.1.2": "Use the `lang` attribute on elements where the language changes from the page default.",
  "wcag311": "Add a `lang` attribute to the `<html>` element to specify the page language (e.g., `<html lang=\"en\">`).",
  "wcag312": "Use the `lang` attribute on elements where the language changes from the page default.",
  
  // 3.2 Predictable
  "3.2.1": "Ensure receiving focus does not trigger unexpected context changes like form submission or page navigation.",
  "3.2.2": "Ensure changing form controls does not automatically trigger unexpected context changes.",
  "wcag321": "Ensure receiving focus does not trigger unexpected context changes like form submission or page navigation.",
  "wcag322": "Ensure changing form controls does not automatically trigger unexpected context changes.",
  
  // 4.1 Compatible
  "4.1.1": "Fix HTML validation errors, especially duplicate IDs, improper nesting, and missing required attributes.",
  "4.1.2": "Ensure all UI components have accessible names and roles, and programmatically convey their state.",
  "4.1.3": "Ensure status messages are programmatically determinable through ARIA live regions or role attributes.",
  "wcag411": "Fix HTML validation errors, especially duplicate IDs, improper nesting, and missing required attributes.",
  "wcag412": "Ensure all UI components have accessible names and roles, and programmatically convey their state.",
  "wcag413": "Ensure status messages are programmatically determinable through ARIA live regions or role attributes.",
  
  // Common axe-core rule IDs
  "html-has-lang": "Add a `lang` attribute to the `<html>` element to specify the page language (e.g., `<html lang=\"en\">`).",
  "color-contrast": "Increase the color contrast ratio between text and background to meet WCAG standards (4.5:1 for normal text).",
  "image-alt": "Add descriptive alt text to images using the `alt` attribute. Use empty alt (`alt=\"\"`) for decorative images.",
  "link-name": "Ensure all links have accessible names through link text, aria-label, or aria-labelledby attributes.",
  "button-name": "Ensure all buttons have accessible names through button text, aria-label, or aria-labelledby attributes.",
  "form-field-multiple-labels": "Ensure form fields have exactly one properly associated label using the `for` attribute or implicit labeling.",
  "heading-order": "Use heading elements (h1-h6) in hierarchical order without skipping levels (h1 → h2 → h3).",
  "landmark-one-main": "Include exactly one `main` landmark on each page to identify the primary content area.",
  "page-has-heading-one": "Include exactly one h1 element on each page to provide a main heading for the content.",
  "region": "Ensure all content is contained within landmark regions (main, nav, aside, etc.) for screen reader navigation.",
  "skip-link": "Provide a 'Skip to main content' link as the first focusable element on the page.",
  "focus-order-semantics": "Ensure the focus order follows the logical reading order and maintains semantic meaning.",
  "aria-allowed-attr": "Remove ARIA attributes that are not allowed for the element's role, or change the element's role.",
  "aria-required-attr": "Add the required ARIA attributes for the element's role (e.g., aria-expanded for buttons).",
  "duplicate-id": "Ensure all ID attributes are unique within the page. Duplicate IDs can break form labels and ARIA references."
};

// User Management Utility
const UserManager = {
  getUserId: () => {
    let userId = localStorage.getItem('accessibility_scanner_user_id');
    if (!userId) {
      userId = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('accessibility_scanner_user_id', userId);
    }
    return userId;
  },
  
  clearUser: () => {
    localStorage.removeItem('accessibility_scanner_user_id');
  }
};

// Helper function to get remediation guidance for WCAG codes
const getRemediationGuidance = (issue) => {
  if (!issue.wcag || !Array.isArray(issue.wcag)) {
    return null;
  }
  
  // Try to find remediation guidance by checking various WCAG references
  for (const wcagRef of issue.wcag) {
    const guidance = WCAG_REMEDIATION[wcagRef];
    if (guidance) {
      return guidance;
    }
  }
  
  // Also check the issue ID itself (for axe-core rules)
  if (issue.id && WCAG_REMEDIATION[issue.id]) {
    return WCAG_REMEDIATION[issue.id];
  }
  
  return null;
};

// Navigation Component
const Navigation = () => {
  const userId = UserManager.getUserId();
  
  return (
    <nav className="bg-blue-600 text-white p-4 mb-8">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">Accessibility Scanner</h1>
        <div className="flex items-center space-x-4">
          <Link to="/" className="hover:text-blue-200 transition-colors">
            Dashboard
          </Link>
          <Link to="/scan" className="hover:text-blue-200 transition-colors">
            New Scan
          </Link>
          <Link to="/my-scans" className="hover:text-blue-200 transition-colors">
            My Scans
          </Link>
          <div className="text-sm text-blue-200">
            User: {userId.substring(0, 8)}...
          </div>
        </div>
      </div>
    </nav>
  );
};

// My Scans Page Component
const MyScansPage = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const userId = UserManager.getUserId();

  useEffect(() => {
    fetchUserScans();
    
    // Auto-refresh every 10 seconds for pending scans
    const interval = setInterval(fetchUserScans, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchUserScans = async () => {
    try {
      const response = await axios.get(`${API}/users/${userId}/scans`);
      setScans(response.data);
      setError("");
    } catch (error) {
      setError("Failed to fetch your scans");
    } finally {
      setLoading(false);
    }
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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Loading your scans...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">My Accessibility Scans</h1>
            <p className="text-gray-600">Track and manage your website accessibility scan history</p>
          </div>
          <Link
            to="/scan"
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            New Scan
          </Link>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {scans.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-gray-400 text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">No scans yet</h2>
            <p className="text-gray-600 mb-6">Start your first accessibility scan to see results here.</p>
            <Link
              to="/scan"
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Run Your First Scan
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800">
                Scan History ({scans.length} {scans.length === 1 ? 'scan' : 'scans'})
              </h2>
            </div>
            
            {/* Desktop Table View */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Website URL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date & Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tool
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {scans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="max-w-xs">
                          <div className="text-sm font-medium text-gray-900 truncate">{scan.url}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{formatDate(scan.createdAt)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          {scan.tool || "axe-core"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(scan.status)}`}>
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {scan.score !== null ? (
                          <span className={`text-lg font-bold ${getScoreColor(scan.score)}`}>
                            {scan.score}/100
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => navigate(`/scan-results/${scan.id}`)}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium py-2 px-4 rounded-lg transition-colors text-sm"
                        >
                          View Results
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="md:hidden">
              {scans.map((scan) => (
                <div key={scan.id} className="border-b border-gray-200 p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">{scan.url}</h3>
                      <p className="text-xs text-gray-500 mt-1">{formatDate(scan.createdAt)}</p>
                    </div>
                    <span className={`ml-2 inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(scan.status)}`}>
                      {scan.status}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {scan.tool || "axe-core"}
                      </span>
                      {scan.score !== null && (
                        <span className={`text-lg font-bold ${getScoreColor(scan.score)}`}>
                          {scan.score}/100
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => navigate(`/scan-results/${scan.id}`)}
                      className="bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium py-2 px-4 rounded-lg transition-colors text-sm"
                    >
                      View Results
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
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
                {scan.issues?.failed ? scan.issues.failed.length : 0}
              </div>
              <div className="text-red-700 font-medium">Failed Tests</div>
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

          {/* Failed Issues Table */}
          {scan.issues?.failed && scan.issues.failed.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="bg-red-50 border-b border-red-200 px-8 py-4">
                <h3 className="text-xl font-bold text-red-800">❌ Accessibility Issues</h3>
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
                    {scan.issues.failed.map((issue, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="max-w-xs">
                            <div className="font-semibold text-gray-900 mb-1">{issue.id}</div>
                            <div className="text-sm text-gray-600 mb-2">{issue.description}</div>
                            {issue.help && (
                              <div className="text-sm text-blue-600 mb-2">{issue.help}</div>
                            )}
                            {/* Remediation Guidance */}
                            {(() => {
                              const guidance = getRemediationGuidance(issue);
                              return guidance ? (
                                <div className="mt-3">
                                  <div className="text-xs font-medium text-gray-700 mb-1">💡 How to fix it</div>
                                  <div className="bg-gray-100 p-2 rounded text-sm text-gray-700">
                                    {guidance}
                                  </div>
                                </div>
                              ) : null;
                            })()}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getImpactColor(issue.impact)}`}>
                            {issue.impact || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {formatWcagReference(issue.wcag || [])}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900">
                            {issue.count || 0} element(s)
                          </div>
                          {issue.elements && issue.elements.length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                                View elements
                              </summary>
                              <div className="mt-2 max-h-32 overflow-y-auto">
                                {issue.elements.slice(0, 3).map((element, elemIndex) => (
                                  <div key={elemIndex} className="text-xs text-gray-500 mb-1 font-mono">
                                    {element.target ? element.target.join(', ') : 'N/A'}
                                  </div>
                                ))}
                                {issue.elements.length > 3 && (
                                  <div className="text-xs text-gray-400">
                                    ... and {issue.elements.length - 3} more
                                  </div>
                                )}
                              </div>
                            </details>
                          )}
                          {issue.selectors && issue.selectors.length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                                View selectors
                              </summary>
                              <div className="mt-2 max-h-32 overflow-y-auto">
                                {issue.selectors.slice(0, 3).map((selector, selIndex) => (
                                  <div key={selIndex} className="text-xs text-gray-500 mb-1 font-mono">
                                    {Array.isArray(selector) ? selector.join(', ') : selector}
                                  </div>
                                ))}
                                {issue.selectors.length > 3 && (
                                  <div className="text-xs text-gray-400">
                                    ... and {issue.selectors.length - 3} more
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

          {/* Passed Tests Collapsible Section */}
          {scan.issues?.passed && scan.issues.passed.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <details className="group">
                <summary className="cursor-pointer bg-green-50 border-b border-green-200 px-8 py-4 hover:bg-green-100 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-green-800">✅ Passed Tests ({scan.issues.passed.length})</h3>
                      <p className="text-green-600 text-sm mt-1">Tests that passed accessibility requirements</p>
                    </div>
                    <div className="transform group-open:rotate-180 transition-transform duration-200">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </summary>
                <div className="px-8 py-6 bg-green-25">
                  <div className="grid gap-4">
                    {scan.issues.passed.map((test, index) => (
                      <div key={index} className="border border-green-200 rounded-lg p-4 bg-green-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-green-800 mb-2">{test.id}</h4>
                            <p className="text-sm text-green-700 mb-2">{test.description}</p>
                            {test.help && (
                              <p className="text-xs text-green-600 mb-2">{test.help}</p>
                            )}
                            <div className="flex items-center space-x-4 text-xs text-green-600">
                              {test.wcag && test.wcag.length > 0 && (
                                <span className="bg-green-100 px-2 py-1 rounded">
                                  WCAG: {formatWcagReference(test.wcag)}
                                </span>
                              )}
                              {test.count && (
                                <span className="bg-green-100 px-2 py-1 rounded">
                                  Elements: {test.count}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            </div>
          )}

          {/* Incomplete Tests Collapsible Section */}
          {scan.issues?.incomplete && scan.issues.incomplete.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <details className="group">
                <summary className="cursor-pointer bg-yellow-50 border-b border-yellow-200 px-8 py-4 hover:bg-yellow-100 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-yellow-800">⚠️ Incomplete Tests ({scan.issues.incomplete.length})</h3>
                      <p className="text-yellow-600 text-sm mt-1">Manual review needed - requires human verification</p>
                    </div>
                    <div className="transform group-open:rotate-180 transition-transform duration-200">
                      <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </summary>
                <div className="px-8 py-6 bg-yellow-25">
                  <div className="grid gap-4">
                    {scan.issues.incomplete.map((test, index) => (
                      <div key={index} className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-yellow-800 mb-2">{test.id}</h4>
                            <p className="text-sm text-yellow-700 mb-2">{test.description}</p>
                            {test.help && (
                              <p className="text-xs text-yellow-600 mb-2">{test.help}</p>
                            )}
                            <div className="bg-yellow-100 border border-yellow-300 rounded p-2 mb-3">
                              <p className="text-xs text-yellow-800 font-medium">
                                📝 Manual Review Required
                              </p>
                              <p className="text-xs text-yellow-700 mt-1">
                                {test.reason || "Requires human verification - automated testing cannot determine if this passes or fails"}
                              </p>
                            </div>
                            <div className="flex items-center space-x-4 text-xs text-yellow-600">
                              {test.wcag && test.wcag.length > 0 && (
                                <span className="bg-yellow-100 px-2 py-1 rounded">
                                  WCAG: {formatWcagReference(test.wcag)}
                                </span>
                              )}
                              {test.count && (
                                <span className="bg-yellow-100 px-2 py-1 rounded">
                                  Elements: {test.count}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            </div>
          )}

          {/* No Failed Issues Message */}
          {scan.issues?.failed && scan.issues.failed.length === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
              <div className="text-green-500 text-4xl mb-4">✅</div>
              <h3 className="text-xl font-bold text-green-800 mb-2">No Accessibility Issues Found!</h3>
              <p className="text-green-600">This website meets all tested accessibility standards.</p>
            </div>
          )}

          {/* Visual Evidence Section */}
          {scan.full_page_screenshot && (
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-4">📸 Visual Evidence</h3>
              <p className="text-gray-600 mb-4">
                Full page screenshot with accessibility issues highlighted in red.
              </p>
              <div className="bg-gray-50 rounded-lg p-4">
                <img
                  src={`data:image/png;base64,${scan.full_page_screenshot}`}
                  alt="Full page screenshot with accessibility issues highlighted"
                  className="max-w-full h-auto rounded border shadow-sm"
                  style={{ maxHeight: '600px', objectFit: 'contain' }}
                />
                <div className="mt-4 text-center">
                  <button
                    onClick={() => window.open(`${API}/scans/${scan.id}/screenshot`, '_blank')}
                    className="bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium py-2 px-4 rounded-lg transition-colors text-sm"
                  >
                    View Full Size
                  </button>
                </div>
              </div>
            </div>
          )}
          <div className="flex justify-center space-x-4 flex-wrap gap-y-2">
            <button
              onClick={() => navigate('/scan')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Run Another Scan
            </button>
            
            {/* Download Report Buttons */}
            {scan.status === 'completed' && (
              <>
                <button
                  onClick={() => window.open(`${API}/scans/${scan.id}/export/pdf`, '_blank')}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
                >
                  <span>📄</span>
                  <span>Download PDF Report</span>
                </button>
                
                <button
                  onClick={() => window.open(`${API}/scans/${scan.id}/export/json`, '_blank')}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
                >
                  <span>📊</span>
                  <span>Download JSON Data</span>
                </button>
                
                {scan.full_page_screenshot && (
                  <button
                    onClick={() => window.open(`${API}/scans/${scan.id}/screenshot`, '_blank')}
                    className="bg-orange-600 hover:bg-orange-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
                  >
                    <span>📸</span>
                    <span>View Screenshot</span>
                  </button>
                )}
              </>
            )}
            
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
  const [tool, setTool] = useState("axe-core");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState(""); // "success" or "error"
  const [apiStatus, setApiStatus] = useState({});
  const navigate = useNavigate();
  const userId = UserManager.getUserId();

  useEffect(() => {
    // Fetch external API status on component mount
    fetchApiStatus();
  }, []);

  const fetchApiStatus = async () => {
    try {
      const response = await axios.get(`${API}/external-apis/status`);
      setApiStatus(response.data);
    } catch (error) {
      console.error("Error fetching API status:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setMessage("");

    try {
      const response = await axios.post(`${API}/scans`, {
        url: url.trim(),
        tool: tool,
        user_id: userId
      });

      setMessage("Scan started successfully! Redirecting to results page...");
      setMessageType("success");
      setUrl("");

      // Redirect to results page after a brief delay
      setTimeout(() => {
        navigate(`/scan-results/${response.data.id}`);
      }, 1500);

    } catch (error) {
      setMessage("Failed to start scan. Please check the URL and try again.");
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  };

  const getToolDescription = (toolName) => {
    switch (toolName) {
      case "axe-core":
        return "Free, comprehensive accessibility testing using headless browser automation";
      case "wave":
        return "WebAIM's WAVE API for detailed accessibility evaluation";
      case "equalweb":
        return "EqualWeb's professional accessibility compliance scanning";
      case "accessibe":
        return "AccessiBe's accessibility analysis and compliance checking";
      default:
        return "";
    }
  };

  const getToolStatus = (toolName) => {
    if (toolName === "axe-core") return { available: true, status: "ready" };
    return {
      available: apiStatus[toolName]?.configured || false,
      status: apiStatus[toolName]?.status || "unknown"
    };
  };

  return (
    <div className="container mx-auto px-4 max-w-4xl">
      <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-6">Run Accessibility Scan</h2>
        <p className="text-gray-600 mb-6">
          Enter a website URL and select your preferred accessibility scanning tool.
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-6">
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

          <div>
            <label htmlFor="tool" className="block text-sm font-medium text-gray-700 mb-3">
              Scanning Tool
            </label>
            <div className="space-y-3">
              {["axe-core", "wave", "equalweb", "accessibe"].map((toolOption) => {
                const toolStatus = getToolStatus(toolOption);
                const isDisabled = !toolStatus.available && toolOption !== "axe-core";
                
                return (
                  <div key={toolOption} className="flex items-start space-x-3">
                    <input
                      type="radio"
                      id={toolOption}
                      name="tool"
                      value={toolOption}
                      checked={tool === toolOption}
                      onChange={(e) => setTool(e.target.value)}
                      disabled={loading || isDisabled}
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <label htmlFor={toolOption} className="flex-1">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className={`font-medium ${isDisabled ? 'text-gray-400' : 'text-gray-900'}`}>
                              {toolOption === "axe-core" ? "axe-core" : toolOption.toUpperCase()}
                            </span>
                            {toolOption === "axe-core" && (
                              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                                Free
                              </span>
                            )}
                            {toolStatus.status === "ready" && toolOption !== "axe-core" && (
                              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                                Ready
                              </span>
                            )}
                            {toolStatus.status === "api_key_required" && (
                              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                                API Key Required
                              </span>
                            )}
                          </div>
                          <p className={`text-sm mt-1 ${isDisabled ? 'text-gray-400' : 'text-gray-600'}`}>
                            {getToolDescription(toolOption)}
                          </p>
                          {isDisabled && (
                            <p className="text-xs text-red-600 mt-1">
                              Configure API key in backend environment to enable this tool
                            </p>
                          )}
                        </div>
                      </div>
                    </label>
                  </div>
                );
              })}
            </div>
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

        {/* Tool Information Panel */}
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">About Accessibility Scanning Tools</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 border">
              <h4 className="font-semibold text-gray-800 mb-2">axe-core (Recommended)</h4>
              <p className="text-sm text-gray-600">
                Free, open-source accessibility testing engine. Provides comprehensive WCAG compliance checking with detailed violation reports.
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border">
              <h4 className="font-semibold text-gray-800 mb-2">External APIs</h4>
              <p className="text-sm text-gray-600">
                Professional accessibility scanning services like WAVE, EqualWeb, and AccessiBe offer additional features and compliance reporting.
              </p>
            </div>
          </div>
        </div>
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
  const userId = UserManager.getUserId();

  const fetchScans = async () => {
    try {
      // Get all scans for overview, but we could filter by user if needed
      const response = await axios.get(`${API}/scans`);
      setScans(response.data);
    } catch (error) {
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
          Monitor website accessibility scans and compliance reports
        </p>
        <div className="flex justify-center space-x-4">
          <Link
            to="/scan"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Run New Scan
          </Link>
          <Link
            to="/my-scans"
            className="inline-block bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            View My Scans
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Scans (All Users)</h2>
        {scans.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-500">No scans yet. Run your first accessibility scan!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {scans.slice(0, 10).map((scan) => (
              <div key={scan.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-800 break-all">{scan.url}</h3>
                    <p className="text-sm text-gray-500">
                      {new Date(scan.createdAt).toLocaleString()}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <p className="text-sm text-gray-500">
                        Tool: {scan.tool || "axe-core"}
                      </p>
                      {scan.user_id === userId && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          Your Scan
                        </span>
                      )}
                    </div>
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
                        {scan.issues.passed ? scan.issues.passed.length : 0}
                      </div>
                      <div className="text-xs text-green-700">Passed</div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-red-600">
                        {scan.issues.failed ? scan.issues.failed.length : 0}
                      </div>
                      <div className="text-xs text-red-700">Failed</div>
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
          <Route path="/my-scans" element={<MyScansPage />} />
          <Route path="/scan-results/:id" element={<ScanResultsPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;