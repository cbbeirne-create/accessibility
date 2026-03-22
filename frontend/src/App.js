import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate, Navigate, useLocation } from "react-router-dom";
import axios from "axios";
import { CheckCircle, Shield, Zap, BarChart3, FileText, Lock, ChevronRight, Check, X, Eye, EyeOff } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  // Setup axios interceptor for auth
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Load user profile on mount
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/auth/me`);
          setUser(response.data);
        } catch (error) {
          // Token is invalid
          logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      setToken(access_token);
      
      // Fetch user profile
      const userResponse = await axios.get(`${API}/auth/me`);
      setUser(userResponse.data);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const signup = async (email, password, fullName) => {
    try {
      const response = await axios.post(`${API}/auth/signup`, {
        email,
        password,
        full_name: fullName
      });
      
      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      setToken(access_token);
      
      // Fetch user profile
      const userResponse = await axios.get(`${API}/auth/me`);
      setUser(userResponse.data);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Signup failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    login,
    signup,
    logout,
    loading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
};

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

// Navigation Component - Premium Enterprise Style
const Navigation = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  return (
    <nav className="bg-slate-900 border-b border-slate-800">
      <div className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3" data-testid="nav-logo">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold text-white tracking-tight">Auditly</span>
              <span className="text-xs text-slate-400 block -mt-1">Accessibility Scanner</span>
            </div>
          </Link>
          
          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {isAuthenticated ? (
              <>
                <Link 
                  to="/" 
                  data-testid="nav-dashboard"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive('/') 
                      ? 'bg-slate-800 text-white' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  Dashboard
                </Link>
                <Link 
                  to="/scan" 
                  data-testid="nav-new-scan"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive('/scan') 
                      ? 'bg-slate-800 text-white' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  New Scan
                </Link>
                <Link 
                  to="/my-scans" 
                  data-testid="nav-my-scans"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive('/my-scans') 
                      ? 'bg-slate-800 text-white' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  My Scans
                </Link>
                <Link 
                  to="/pricing" 
                  data-testid="nav-pricing"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive('/pricing') 
                      ? 'bg-slate-800 text-white' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  Pricing
                </Link>
                
                {/* User Menu */}
                <div className="flex items-center ml-4 pl-4 border-l border-slate-700">
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <div className="text-sm font-medium text-white">{user?.full_name || user?.email?.split('@')[0]}</div>
                      <div className="flex items-center justify-end space-x-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          user?.plan === 'pro' 
                            ? 'bg-emerald-500/20 text-emerald-400' 
                            : 'bg-slate-700 text-slate-400'
                        }`}>
                          {user?.plan?.toUpperCase()}
                        </span>
                        {user?.scans_remaining !== -1 && (
                          <span className="text-xs text-slate-500">
                            {user?.scans_remaining} left
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={logout}
                      data-testid="nav-logout"
                      className="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-2 rounded-lg text-sm font-medium transition-all"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <Link 
                  to="/pricing" 
                  data-testid="nav-pricing-guest"
                  className="px-4 py-2 text-slate-400 hover:text-white text-sm font-medium transition-colors"
                >
                  Pricing
                </Link>
                <Link 
                  to="/login" 
                  data-testid="nav-login"
                  className="px-4 py-2 text-slate-400 hover:text-white text-sm font-medium transition-colors"
                >
                  Login
                </Link>
                <Link 
                  to="/signup" 
                  data-testid="nav-signup"
                  className="ml-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-emerald-500/25"
                >
                  Start Free
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Login Page Component
const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const result = await login(email, password);
    
    if (result.success) {
      const from = location.state?.from?.pathname || '/';
      navigate(from);
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Welcome back</h1>
          <p className="text-slate-400">Sign in to your Auditly account</p>
        </div>

        {/* Login Form */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm" data-testid="login-error">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email address
              </label>
              <input
                type="email"
                id="email"
                data-testid="login-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                placeholder="you@company.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  data-testid="login-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              data-testid="login-submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </span>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Don't have an account?{" "}
              <Link to="/signup" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                Sign up for free
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Signup Page Component
const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { signup, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    const result = await signup(email, password, fullName);
    
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Create your account</h1>
          <p className="text-slate-400">Start scanning for free with 2 scans/month</p>
        </div>

        {/* Signup Form */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm" data-testid="signup-error">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-slate-300 mb-2">
                Full name
              </label>
              <input
                type="text"
                id="fullName"
                data-testid="signup-fullname"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                placeholder="John Doe"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Work email
              </label>
              <input
                type="email"
                id="email"
                data-testid="signup-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                placeholder="you@company.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  data-testid="signup-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  placeholder="At least 8 characters"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
                Confirm password
              </label>
              <input
                type={showPassword ? "text" : "password"}
                id="confirmPassword"
                data-testid="signup-confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                placeholder="Confirm your password"
                required
              />
            </div>

            <button
              type="submit"
              data-testid="signup-submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </span>
              ) : (
                "Create account"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{" "}
              <Link to="/login" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Trust Badges */}
        <div className="mt-8 flex items-center justify-center space-x-6 text-slate-500">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4" />
            <span className="text-xs">SSL Secured</span>
          </div>
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4" />
            <span className="text-xs">WCAG Compliant</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Pricing Page Component
const PricingPage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      navigate('/signup');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/subscription/create-checkout-session`);
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      console.error('Failed to create checkout session:', error);
      alert('Unable to start checkout. Please try again or contact support.');
    }
    setLoading(false);
  };

  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for trying out Auditly",
      features: [
        { text: "2 scans per month", included: true },
        { text: "axe-core scanning engine", included: true },
        { text: "Basic accessibility reports", included: true },
        { text: "JSON export", included: true },
        { text: "PDF export", included: false },
        { text: "Visual evidence screenshots", included: true },
        { text: "Priority support", included: false },
        { text: "API access", included: false },
      ],
      cta: isAuthenticated && user?.plan === 'free' ? "Current Plan" : "Get Started",
      ctaAction: () => !isAuthenticated && navigate('/signup'),
      highlighted: false,
      disabled: isAuthenticated && user?.plan === 'free',
    },
    {
      name: "Pro",
      price: "$29",
      period: "/month",
      description: "For teams serious about accessibility",
      features: [
        { text: "Unlimited scans", included: true },
        { text: "All scanning engines", included: true },
        { text: "Comprehensive reports", included: true },
        { text: "JSON export", included: true },
        { text: "PDF export", included: true },
        { text: "Visual evidence screenshots", included: true },
        { text: "Priority support", included: true },
        { text: "API access", included: true },
      ],
      cta: user?.plan === 'pro' ? "Current Plan" : "Upgrade to Pro",
      ctaAction: handleUpgrade,
      highlighted: true,
      disabled: user?.plan === 'pro',
    },
  ];

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950">
      {/* Hero Section */}
      <div className="pt-16 pb-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-medium mb-6">
            <Zap className="w-4 h-4 mr-2" />
            Simple, transparent pricing
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Choose your plan
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Start free and upgrade when you need more. No hidden fees, cancel anytime.
          </p>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-5xl mx-auto px-4 pb-16">
        <div className="grid md:grid-cols-2 gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              data-testid={`pricing-card-${plan.name.toLowerCase()}`}
              className={`relative rounded-2xl p-8 ${
                plan.highlighted
                  ? 'bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border-2 border-emerald-500/50'
                  : 'bg-slate-900 border border-slate-800'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-xs font-bold px-4 py-1.5 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-slate-400 text-sm">{plan.description}</p>
              </div>

              <div className="mb-6">
                <span className="text-4xl font-bold text-white">{plan.price}</span>
                <span className="text-slate-400 ml-1">{plan.period}</span>
              </div>

              <button
                onClick={plan.ctaAction}
                disabled={plan.disabled || loading}
                data-testid={`pricing-cta-${plan.name.toLowerCase()}`}
                className={`w-full py-3 px-6 rounded-xl font-semibold transition-all mb-8 ${
                  plan.highlighted
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/25'
                    : 'bg-slate-800 hover:bg-slate-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loading && plan.highlighted ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Processing...
                  </span>
                ) : (
                  plan.cta
                )}
              </button>

              <ul className="space-y-3">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center">
                    {feature.included ? (
                      <Check className="w-5 h-5 text-emerald-400 mr-3 flex-shrink-0" />
                    ) : (
                      <X className="w-5 h-5 text-slate-600 mr-3 flex-shrink-0" />
                    )}
                    <span className={feature.included ? 'text-slate-300' : 'text-slate-500'}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-3xl mx-auto px-4 pb-16">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Frequently asked questions</h2>
        <div className="space-y-4">
          {[
            {
              q: "What happens when I reach my scan limit?",
              a: "On the Free plan, you'll need to wait until the next month or upgrade to Pro for unlimited scans. We'll notify you when you're approaching your limit.",
            },
            {
              q: "Can I cancel my Pro subscription anytime?",
              a: "Yes! You can cancel anytime. You'll continue to have Pro access until the end of your billing period.",
            },
            {
              q: "What accessibility standards do you test against?",
              a: "We test against WCAG 2.1 Level A and AA guidelines using the axe-core engine, which is trusted by major tech companies worldwide.",
            },
          ].map((faq, index) => (
            <div key={index} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-white font-medium mb-2">{faq.q}</h3>
              <p className="text-slate-400 text-sm">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// My Scans Page Component - Premium Enterprise Style
const MyScansPage = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    fetchUserScans();
    const interval = setInterval(fetchUserScans, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchUserScans = async () => {
    try {
      const response = await axios.get(`${API}/scans`);
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
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'error':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'pending':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-red-400';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-emerald-500/20';
    if (score >= 60) return 'bg-amber-500/20';
    return 'bg-red-500/20';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading your scans...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My Scans</h1>
            <p className="text-slate-400">
              {scans.length} {scans.length === 1 ? 'scan' : 'scans'} in your history
            </p>
          </div>
          <Link
            to="/scan"
            data-testid="my-scans-new-scan"
            className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 flex items-center"
          >
            <Zap className="w-5 h-5 mr-2" />
            New Scan
          </Link>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {scans.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <div className="w-20 h-20 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <BarChart3 className="w-10 h-10 text-slate-600" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">No scans yet</h2>
            <p className="text-slate-400 mb-6">Start your first accessibility scan to see results here.</p>
            <Link
              to="/scan"
              className="inline-flex items-center bg-emerald-500 hover:bg-emerald-600 text-white font-medium py-3 px-6 rounded-xl transition-colors"
            >
              <Zap className="w-5 h-5 mr-2" />
              Run Your First Scan
            </Link>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            {/* Table Header */}
            <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-4 bg-slate-800/50 border-b border-slate-800 text-xs font-medium text-slate-400 uppercase tracking-wider">
              <div className="col-span-5">Website</div>
              <div className="col-span-2">Date</div>
              <div className="col-span-2">Tool</div>
              <div className="col-span-1">Status</div>
              <div className="col-span-1 text-center">Score</div>
              <div className="col-span-1"></div>
            </div>

            {/* Table Rows */}
            <div className="divide-y divide-slate-800">
              {scans.map((scan) => (
                <div
                  key={scan.id}
                  className="grid grid-cols-1 md:grid-cols-12 gap-4 px-6 py-5 hover:bg-slate-800/30 transition-colors items-center"
                  data-testid={`my-scan-row-${scan.id}`}
                >
                  {/* Mobile: Full card view */}
                  <div className="md:hidden">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-white font-medium truncate">{scan.url}</h3>
                        <p className="text-xs text-slate-500 mt-1">{formatDate(scan.createdAt)}</p>
                      </div>
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(scan.status)}`}>
                        {scan.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-slate-800 text-slate-400">
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
                        className="bg-slate-800 hover:bg-slate-700 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm flex items-center"
                      >
                        View
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </button>
                    </div>
                  </div>

                  {/* Desktop: Table row */}
                  <div className="hidden md:block col-span-5">
                    <div className="text-white font-medium truncate">{scan.url}</div>
                  </div>
                  <div className="hidden md:block col-span-2">
                    <div className="text-sm text-slate-400">{formatDate(scan.createdAt)}</div>
                  </div>
                  <div className="hidden md:block col-span-2">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-slate-800 text-slate-400">
                      {scan.tool || "axe-core"}
                    </span>
                  </div>
                  <div className="hidden md:block col-span-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(scan.status)}`}>
                      {scan.status}
                    </span>
                  </div>
                  <div className="hidden md:flex col-span-1 justify-center">
                    {scan.score !== null ? (
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${getScoreBg(scan.score)}`}>
                        <span className={`text-sm font-bold ${getScoreColor(scan.score)}`}>{scan.score}</span>
                      </div>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </div>
                  <div className="hidden md:flex col-span-1 justify-end">
                    <button
                      onClick={() => navigate(`/scan-results/${scan.id}`)}
                      className="bg-slate-800 hover:bg-slate-700 text-white p-2 rounded-lg transition-colors"
                    >
                      <ChevronRight className="w-5 h-5" />
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

// Scan Page Component - Premium Enterprise Style
const ScanPage = () => {
  const [url, setUrl] = useState("");
  const [tool, setTool] = useState("axe-core");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [apiStatus, setApiStatus] = useState({});
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    fetchApiStatus();
  }, []);

  const fetchApiStatus = async () => {
    try {
      const response = await axios.get(`${API}/external-apis/status`);
      setApiStatus(response.data);
    } catch (error) {
      // Silent fail
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Check if user can scan
    if (user?.scans_remaining === 0) {
      setMessage("You've reached your monthly scan limit. Upgrade to Pro for unlimited scans.");
      setMessageType("error");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await axios.post(`${API}/scans`, {
        url: url.trim(),
        tool: tool
      });

      setMessage("Scan started successfully! Redirecting...");
      setMessageType("success");
      setUrl("");

      setTimeout(() => {
        navigate(`/scan-results/${response.data.id}`);
      }, 1500);

    } catch (error) {
      if (error.response?.status === 403) {
        setMessage(error.response.data.detail || "Scan limit exceeded. Upgrade to Pro for unlimited scans.");
      } else {
        setMessage("Failed to start scan. Please check the URL and try again.");
      }
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  };

  const getToolDescription = (toolName) => {
    switch (toolName) {
      case "axe-core":
        return "Industry-leading open-source accessibility engine with comprehensive WCAG coverage";
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
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">New Accessibility Scan</h1>
          <p className="text-slate-400">
            Enter a URL to scan for accessibility issues
            {user?.plan === 'free' && (
              <span className="text-slate-500"> • {user?.scans_remaining} scans remaining</span>
            )}
          </p>
        </div>

        {/* Scan Form */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* URL Input */}
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-slate-300 mb-2">
                Website URL
              </label>
              <input
                type="url"
                id="url"
                data-testid="scan-url-input"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-4 py-4 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-lg"
                required
                disabled={loading}
              />
            </div>

            {/* Tool Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Scanning Engine
              </label>
              <div className="space-y-3">
                {["axe-core", "wave", "equalweb", "accessibe"].map((toolOption) => {
                  const toolStatus = getToolStatus(toolOption);
                  const isDisabled = !toolStatus.available && toolOption !== "axe-core";
                  
                  return (
                    <label
                      key={toolOption}
                      className={`flex items-start space-x-4 p-4 rounded-xl border transition-all cursor-pointer ${
                        tool === toolOption && !isDisabled
                          ? 'bg-emerald-500/10 border-emerald-500/50'
                          : isDisabled
                            ? 'bg-slate-800/50 border-slate-700/50 opacity-50 cursor-not-allowed'
                            : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <input
                        type="radio"
                        name="tool"
                        value={toolOption}
                        checked={tool === toolOption}
                        onChange={(e) => setTool(e.target.value)}
                        disabled={loading || isDisabled}
                        className="mt-1 h-4 w-4 text-emerald-500 focus:ring-emerald-500 border-slate-600 bg-slate-700"
                      />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className={`font-medium ${isDisabled ? 'text-slate-500' : 'text-white'}`}>
                            {toolOption === "axe-core" ? "axe-core" : toolOption.toUpperCase()}
                          </span>
                          {toolOption === "axe-core" && (
                            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-500/20 text-emerald-400">
                              Recommended
                            </span>
                          )}
                          {isDisabled && (
                            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-700 text-slate-400">
                              API Key Required
                            </span>
                          )}
                        </div>
                        <p className={`text-sm mt-1 ${isDisabled ? 'text-slate-600' : 'text-slate-400'}`}>
                          {getToolDescription(toolOption)}
                        </p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              data-testid="scan-submit-btn"
              disabled={loading || !url.trim() || user?.scans_remaining === 0}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none flex items-center justify-center"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Starting Scan...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-2" />
                  Run Accessibility Scan
                </>
              )}
            </button>
          </form>

          {/* Messages */}
          {message && (
            <div className={`mt-6 p-4 rounded-xl ${
              messageType === "success" 
                ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" 
                : "bg-red-500/10 border border-red-500/20 text-red-400"
            }`}>
              {message}
              {messageType === "error" && user?.plan === 'free' && (
                <Link to="/pricing" className="block mt-2 text-emerald-400 hover:text-emerald-300 font-medium">
                  Upgrade to Pro →
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Info Panel */}
        <div className="mt-8 grid md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-400 mb-4">
              <Shield className="w-5 h-5" />
            </div>
            <h3 className="text-white font-semibold mb-2">WCAG 2.1 Compliance</h3>
            <p className="text-slate-400 text-sm">
              Tests against Level A and AA guidelines, covering color contrast, keyboard navigation, ARIA, and more.
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-400 mb-4">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-white font-semibold mb-2">Detailed Reports</h3>
            <p className="text-slate-400 text-sm">
              Get visual evidence, code snippets, and step-by-step remediation guides for every issue found.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component - Premium Enterprise Style
const Dashboard = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const fetchScans = async () => {
    try {
      const response = await axios.get(`${API}/scans`);
      setScans(response.data);
    } catch (error) {
      if (error.response?.status === 401) {
        // Not authenticated - that's OK for the public dashboard
      } else {
        setError("Failed to fetch scan results");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchScans();
      const interval = setInterval(fetchScans, 5000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'error':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'pending':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-red-400';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-emerald-500/20';
    if (score >= 60) return 'bg-amber-500/20';
    return 'bg-red-500/20';
  };

  // Landing page for non-authenticated users
  if (!isAuthenticated) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950">
        {/* Hero Section */}
        <div className="pt-20 pb-16 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-sm font-medium mb-8">
              <CheckCircle className="w-4 h-4 mr-2" />
              WCAG 2.1 AA Compliance Testing
            </div>
            <h1 className="text-5xl sm:text-6xl font-bold text-white mb-6 leading-tight">
              Website Accessibility<br />
              <span className="bg-gradient-to-r from-emerald-400 to-teal-400 text-transparent bg-clip-text">
                Made Simple
              </span>
            </h1>
            <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
              Scan any website for accessibility issues in seconds. Get actionable insights and detailed remediation guidance powered by industry-leading testing engines.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/signup"
                data-testid="hero-cta-signup"
                className="w-full sm:w-auto bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-4 px-8 rounded-xl transition-all shadow-lg shadow-emerald-500/25 flex items-center justify-center"
              >
                Start Free Trial
                <ChevronRight className="w-5 h-5 ml-2" />
              </Link>
              <Link
                to="/pricing"
                data-testid="hero-cta-pricing"
                className="w-full sm:w-auto bg-slate-800 hover:bg-slate-700 text-white font-semibold py-4 px-8 rounded-xl transition-all flex items-center justify-center"
              >
                View Pricing
              </Link>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="max-w-6xl mx-auto px-4 pb-20">
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: <Zap className="w-6 h-6" />,
                title: "Lightning Fast",
                description: "Get comprehensive accessibility reports in under 30 seconds using headless browser technology.",
              },
              {
                icon: <FileText className="w-6 h-6" />,
                title: "Detailed Reports",
                description: "PDF and JSON exports with visual evidence, WCAG references, and step-by-step remediation guides.",
              },
              {
                icon: <BarChart3 className="w-6 h-6" />,
                title: "Actionable Insights",
                description: "Clear prioritization of issues by impact level with specific code-level fix suggestions.",
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all"
              >
                <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Section */}
        <div className="border-t border-slate-800 bg-slate-900/50">
          <div className="max-w-4xl mx-auto px-4 py-12 text-center">
            <p className="text-slate-500 text-sm mb-4">Powered by trusted accessibility engines</p>
            <div className="flex items-center justify-center space-x-8 text-slate-400">
              <span className="font-mono text-lg">axe-core</span>
              <span className="text-slate-700">|</span>
              <span className="font-mono text-lg">WAVE</span>
              <span className="text-slate-700">|</span>
              <span className="font-mono text-lg">WCAG 2.1</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard for authenticated users
  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back, {user?.full_name || user?.email?.split('@')[0]}
          </h1>
          <p className="text-slate-400">
            {user?.plan === 'pro' 
              ? "You have unlimited scans on the Pro plan." 
              : `You have ${user?.scans_remaining} scans remaining this month.`
            }
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">Total Scans</div>
            <div className="text-3xl font-bold text-white">{scans.length}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">Scans This Month</div>
            <div className="text-3xl font-bold text-white">{user?.scans_used_this_month || 0}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="text-slate-400 text-sm mb-1">Plan</div>
            <div className="flex items-center space-x-2">
              <span className="text-3xl font-bold text-white capitalize">{user?.plan}</span>
              {user?.plan === 'free' && (
                <Link 
                  to="/pricing" 
                  className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded-full hover:bg-emerald-500/30 transition-colors"
                >
                  Upgrade
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-4 mb-8">
          <Link
            to="/scan"
            data-testid="dashboard-new-scan"
            className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 flex items-center"
          >
            <Zap className="w-5 h-5 mr-2" />
            New Scan
          </Link>
          <Link
            to="/my-scans"
            data-testid="dashboard-my-scans"
            className="bg-slate-800 hover:bg-slate-700 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center"
          >
            <BarChart3 className="w-5 h-5 mr-2" />
            View All Scans
          </Link>
        </div>

        {/* Recent Scans */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800">
            <h2 className="text-lg font-semibold text-white">Recent Scans</h2>
          </div>

          {error && (
            <div className="p-6 text-center">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {scans.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-slate-600" />
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No scans yet</h3>
              <p className="text-slate-400 mb-6">Run your first accessibility scan to get started.</p>
              <Link
                to="/scan"
                className="inline-flex items-center bg-emerald-500 hover:bg-emerald-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                <Zap className="w-4 h-4 mr-2" />
                Run Your First Scan
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {scans.slice(0, 5).map((scan) => (
                <div
                  key={scan.id}
                  className="p-6 hover:bg-slate-800/50 transition-colors cursor-pointer"
                  onClick={() => navigate(`/scan-results/${scan.id}`)}
                  data-testid={`scan-row-${scan.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0 mr-4">
                      <h3 className="text-white font-medium truncate mb-1">{scan.url}</h3>
                      <div className="flex items-center space-x-4 text-sm text-slate-400">
                        <span>{new Date(scan.createdAt).toLocaleDateString()}</span>
                        <span className="text-slate-600">•</span>
                        <span>{scan.tool || "axe-core"}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(scan.status)}`}>
                        {scan.status}
                      </span>
                      {scan.score !== null && (
                        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${getScoreBg(scan.score)}`}>
                          <span className={`text-lg font-bold ${getScoreColor(scan.score)}`}>{scan.score}</span>
                        </div>
                      )}
                      <ChevronRight className="w-5 h-5 text-slate-600" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {scans.length > 5 && (
            <div className="px-6 py-4 border-t border-slate-800 text-center">
              <Link to="/my-scans" className="text-emerald-400 hover:text-emerald-300 font-medium text-sm">
                View all {scans.length} scans →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-slate-950">
        <BrowserRouter>
          <Navigation />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/scan" element={
              <ProtectedRoute>
                <ScanPage />
              </ProtectedRoute>
            } />
            <Route path="/my-scans" element={
              <ProtectedRoute>
                <MyScansPage />
              </ProtectedRoute>
            } />
            <Route path="/scan-results/:id" element={
              <ProtectedRoute>
                <ScanResultsPage />
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;