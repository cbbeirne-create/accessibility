/**
 * Auditly - Website Accessibility Scanner
 * 
 * Main Application Component
 * 
 * This is a refactored version using modular architecture:
 * - /services/api.js - Centralized API client with JWT interceptor
 * - /context/AuthContext.js - Authentication state management
 * - /components/layout - Navigation, SkipLink
 * - /utils/wcag.js - WCAG remediation guidance
 * 
 * Accessibility: WCAG 2.1 AA Compliant
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Semantic HTML structure
 */
import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate, useLocation } from "react-router-dom";
import { 
  CheckCircle, Shield, Zap, BarChart3, FileText, Lock, 
  ChevronRight, Check, X, Eye, EyeOff, AlertTriangle, 
  ExternalLink, Download, Calendar, Globe, ArrowRight,
  Info, Search, Trash2, Mail, RefreshCw 
} from "lucide-react";

// Import modular services and context
import { authAPI, scansAPI, subscriptionAPI } from "./services/api";
import { AuthProvider, useAuth, ProtectedRoute } from "./context/AuthContext";
import { Navigation } from "./components/layout";
import { 
  WCAG_REMEDIATION, 
  getRemediationGuidance, 
  UserManager,
  formatDate,
  getScoreColorClass,
  getScoreBgClass,
  getImpactColorClass 
} from "./utils/wcag";

// ============================================
// Auth Pages
// ============================================

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
      <main id="main-content" className="w-full max-w-md" role="main" aria-labelledby="login-heading">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4" aria-hidden="true">
            <Shield className="w-9 h-9 text-white" aria-hidden="true" />
          </div>
          <h1 id="login-heading" className="text-3xl font-bold text-white mb-2">Welcome back</h1>
          <p className="text-slate-300">Sign in to your Auditly account</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5" aria-labelledby="login-heading">
            {error && (
              <div 
                className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" 
                data-testid="login-error"
                role="alert"
                aria-live="polite"
              >
                {error}
              </div>
            )}

            <div>
              <label htmlFor="login-email" className="block text-sm font-medium text-slate-200 mb-2">
                Email address <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                type="email"
                id="login-email"
                name="email"
                data-testid="login-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                placeholder="you@company.com"
                required
                aria-required="true"
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="login-password" className="block text-sm font-medium text-slate-200 mb-2">
                Password <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="login-password"
                  name="password"
                  data-testid="login-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="Enter your password"
                  required
                  aria-required="true"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-white transition-colors p-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" aria-hidden="true" /> : <Eye className="w-5 h-5" aria-hidden="true" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              data-testid="login-submit"
              disabled={loading}
              aria-busy={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Signing in...</span>
                </span>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-300 text-sm">
              Don't have an account?{" "}
              <Link to="/signup" className="text-emerald-300 hover:text-emerald-200 font-medium transition-colors underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">
                Sign up for free
              </Link>
            </p>
          </div>
          
          <div className="mt-4 text-center">
            <Link 
              to="/forgot-password" 
              className="text-slate-400 hover:text-slate-300 text-sm transition-colors underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded"
              data-testid="forgot-password-link"
            >
              Forgot your password?
            </Link>
          </div>
        </div>
      </main>
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
      setError("Password must be at least 8 characters long");
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
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4 py-8">
      <main id="main-content" className="w-full max-w-md" role="main" aria-labelledby="signup-heading">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4" aria-hidden="true">
            <Shield className="w-9 h-9 text-white" aria-hidden="true" />
          </div>
          <h1 id="signup-heading" className="text-3xl font-bold text-white mb-2">Create your account</h1>
          <p className="text-slate-300">Start scanning for accessibility issues today</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5" aria-labelledby="signup-heading">
            {error && (
              <div 
                className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" 
                data-testid="signup-error"
                role="alert"
                aria-live="polite"
              >
                {error}
              </div>
            )}

            <div>
              <label htmlFor="signup-name" className="block text-sm font-medium text-slate-200 mb-2">
                Full name
              </label>
              <input
                type="text"
                id="signup-name"
                name="fullName"
                data-testid="signup-name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                placeholder="John Doe"
                autoComplete="name"
              />
            </div>

            <div>
              <label htmlFor="signup-email" className="block text-sm font-medium text-slate-200 mb-2">
                Email address <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                type="email"
                id="signup-email"
                name="email"
                data-testid="signup-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                placeholder="you@company.com"
                required
                aria-required="true"
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="signup-password" className="block text-sm font-medium text-slate-200 mb-2">
                Password <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="signup-password"
                  name="password"
                  data-testid="signup-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="Min. 8 characters"
                  required
                  aria-required="true"
                  autoComplete="new-password"
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-white transition-colors p-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" aria-hidden="true" /> : <Eye className="w-5 h-5" aria-hidden="true" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="signup-confirm-password" className="block text-sm font-medium text-slate-200 mb-2">
                Confirm password <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                type={showPassword ? "text" : "password"}
                id="signup-confirm-password"
                name="confirmPassword"
                data-testid="signup-confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                placeholder="Confirm your password"
                required
                aria-required="true"
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              data-testid="signup-submit"
              disabled={loading}
              aria-busy={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Creating account...</span>
                </span>
              ) : (
                "Create account"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-300 text-sm">
              Already have an account?{" "}
              <Link to="/login" className="text-emerald-300 hover:text-emerald-200 font-medium transition-colors underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center text-slate-400 text-xs mt-6">
          By signing up, you agree to our Terms of Service and Privacy Policy
        </p>
      </main>
    </div>
  );
};

// Forgot Password Page
const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await authAPI.forgotPassword(email);
      setSubmitted(true);
    } catch (err) {
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
        <main id="main-content" className="w-full max-w-md" role="main">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6" aria-hidden="true">
              <CheckCircle className="w-8 h-8 text-emerald-400" aria-hidden="true" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Check Your Email</h1>
            <p className="text-slate-300 mb-6">
              If an account exists for <span className="text-white font-medium">{email}</span>, 
              you'll receive a password reset link shortly.
            </p>
            <p className="text-slate-400 text-sm mb-6">
              The link will expire in 1 hour for security reasons.
            </p>
            <div className="space-y-3">
              <Link
                to="/login"
                className="block w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
              >
                Back to Login
              </Link>
              <button
                onClick={() => { setSubmitted(false); setEmail(""); }}
                className="block w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-3 px-6 rounded-xl transition-all text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
              >
                Try Different Email
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
      <main id="main-content" className="w-full max-w-md" role="main" aria-labelledby="forgot-password-heading">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4" aria-hidden="true">
            <Lock className="w-9 h-9 text-white" aria-hidden="true" />
          </div>
          <h1 id="forgot-password-heading" className="text-3xl font-bold text-white mb-2">Forgot Password?</h1>
          <p className="text-slate-300">Enter your email and we'll send you a reset link</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5" aria-labelledby="forgot-password-heading">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert" aria-live="polite">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="forgot-email" className="block text-sm font-medium text-slate-200 mb-2">
                Email address <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                type="email"
                id="forgot-email"
                name="email"
                data-testid="forgot-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                placeholder="you@company.com"
                required
                aria-required="true"
                autoComplete="email"
                autoFocus
              />
            </div>

            <button
              type="submit"
              data-testid="forgot-submit"
              disabled={loading || !email.trim()}
              aria-busy={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Sending...</span>
                </span>
              ) : (
                "Send Reset Link"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-300 text-sm">
              Remember your password?{" "}
              <Link to="/login" className="text-emerald-300 hover:text-emerald-200 font-medium transition-colors underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

// Reset Password Page
const ResetPasswordPage = () => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get('token');

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setVerifying(false);
        setTokenValid(false);
        return;
      }

      try {
        const response = await authAPI.verifyResetToken(token);
        setTokenValid(response.valid);
      } catch (err) {
        setTokenValid(false);
      } finally {
        setVerifying(false);
      }
    };

    verifyToken();
  }, [token]);

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
      setError("Password must be at least 8 characters long");
      setLoading(false);
      return;
    }

    try {
      const response = await authAPI.resetPassword(token, password);
      if (response.success) {
        setSuccess(true);
      } else {
        setError(response.message || "Failed to reset password");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to reset password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (verifying) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
        <div className="text-center" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" />
          <p className="mt-4 text-slate-300">Verifying reset link...</p>
        </div>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
        <main id="main-content" className="w-full max-w-md" role="main">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6" aria-hidden="true">
              <X className="w-8 h-8 text-red-400" aria-hidden="true" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Invalid Reset Link</h1>
            <p className="text-slate-300 mb-6">
              This password reset link is invalid or has expired. Please request a new one.
            </p>
            <Link
              to="/forgot-password"
              className="block w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              Request New Reset Link
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
        <main id="main-content" className="w-full max-w-md" role="main">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6" aria-hidden="true">
              <CheckCircle className="w-8 h-8 text-emerald-400" aria-hidden="true" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Password Reset Successful!</h1>
            <p className="text-slate-300 mb-6">
              Your password has been changed. You can now sign in with your new password.
            </p>
            <Link
              to="/login"
              className="block w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              Sign In
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
      <main id="main-content" className="w-full max-w-md" role="main" aria-labelledby="reset-password-heading">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4" aria-hidden="true">
            <Lock className="w-9 h-9 text-white" aria-hidden="true" />
          </div>
          <h1 id="reset-password-heading" className="text-3xl font-bold text-white mb-2">Reset Password</h1>
          <p className="text-slate-300">Enter your new password below</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5" aria-labelledby="reset-password-heading">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert" aria-live="polite">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="reset-password" className="block text-sm font-medium text-slate-200 mb-2">
                New Password <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="reset-password"
                  name="password"
                  data-testid="reset-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="Min. 8 characters"
                  required
                  aria-required="true"
                  autoComplete="new-password"
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 hover:text-white transition-colors p-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" aria-hidden="true" /> : <Eye className="w-5 h-5" aria-hidden="true" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="reset-confirm-password" className="block text-sm font-medium text-slate-200 mb-2">
                Confirm New Password <span className="text-red-400" aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                type={showPassword ? "text" : "password"}
                id="reset-confirm-password"
                name="confirmPassword"
                data-testid="reset-confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                placeholder="Confirm your new password"
                required
                aria-required="true"
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              data-testid="reset-submit"
              disabled={loading}
              aria-busy={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Resetting...</span>
                </span>
              ) : (
                "Reset Password"
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};

// ============================================
// Email Verification Page
// ============================================

const VerifyEmailPage = () => {
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const location = useLocation();
  const navigate = useNavigate();

  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get('token');

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setError("No verification token provided.");
        setLoading(false);
        return;
      }

      try {
        const response = await authAPI.verifyEmail(token);
        if (response.success) {
          setSuccess(true);
        } else {
          setError(response.message || "Verification failed.");
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Verification failed. The link may have expired.");
      } finally {
        setLoading(false);
      }
    };

    verifyEmail();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
        <div className="text-center" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" />
          <p className="mt-4 text-slate-300">Verifying your email...</p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
        <main id="main-content" className="w-full max-w-md" role="main">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-emerald-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6" aria-hidden="true">
              <CheckCircle className="w-8 h-8 text-emerald-400" aria-hidden="true" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Email Verified!</h1>
            <p className="text-slate-300 mb-6">
              Your email has been successfully verified. You now have full access to all Auditly features.
            </p>
            <Link
              to="/"
              className="block w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              Go to Dashboard
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4">
      <main id="main-content" className="w-full max-w-md" role="main">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6" aria-hidden="true">
            <X className="w-8 h-8 text-red-400" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-4">Verification Failed</h1>
          <p className="text-slate-300 mb-6">{error}</p>
          <div className="space-y-3">
            <Link
              to="/login"
              className="block w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold py-3 px-6 rounded-xl transition-all text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              Go to Login
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
};

// Email Verification Banner Component
const EmailVerificationBanner = () => {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  if (!user || user.email_verified) {
    return null;
  }

  const handleResend = async () => {
    setLoading(true);
    try {
      await authAPI.resendVerification(user.email);
      setSent(true);
      setTimeout(() => setSent(false), 5000);
    } catch (err) {
      alert('Failed to resend verification email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20" role="alert">
      <div className="container mx-auto px-6 py-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center space-x-3">
            <Mail className="w-5 h-5 text-amber-400 flex-shrink-0" aria-hidden="true" />
            <p className="text-amber-200 text-sm">
              Please verify your email address to unlock all features.
            </p>
          </div>
          <button
            onClick={handleResend}
            disabled={loading || sent}
            className="flex items-center space-x-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 px-4 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
            aria-busy={loading}
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Sending...</span>
              </>
            ) : sent ? (
              <>
                <CheckCircle className="w-4 h-4" aria-hidden="true" />
                <span>Email Sent!</span>
              </>
            ) : (
              <>
                <Mail className="w-4 h-4" aria-hidden="true" />
                <span>Resend Verification</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// Pricing Page
// ============================================

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
      const data = await subscriptionAPI.createCheckoutSession();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
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
        { text: "Visual evidence capture", included: true },
        { text: "JSON export", included: true },
        { text: "PDF reports", included: false },
        { text: "Priority support", included: false },
      ],
      cta: isAuthenticated && user?.plan === 'free' ? "Current Plan" : "Get Started",
      ctaDisabled: isAuthenticated && user?.plan === 'free',
      highlight: false,
    },
    {
      name: "Pro",
      price: "$19",
      period: "per month",
      description: "For professionals and teams",
      features: [
        { text: "Unlimited scans", included: true },
        { text: "All scanning engines", included: true },
        { text: "Visual evidence capture", included: true },
        { text: "JSON export", included: true },
        { text: "PDF reports", included: true },
        { text: "Priority support", included: true },
      ],
      cta: isAuthenticated && user?.plan === 'pro' ? "Current Plan" : "Upgrade to Pro",
      ctaDisabled: isAuthenticated && user?.plan === 'pro',
      highlight: true,
    },
  ];

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-16 px-4">
      <main id="main-content" className="container mx-auto max-w-5xl" role="main" aria-labelledby="pricing-heading">
        <div className="text-center mb-12">
          <h1 id="pricing-heading" className="text-4xl font-bold text-white mb-4">Simple, Transparent Pricing</h1>
          <p className="text-slate-300 text-lg max-w-2xl mx-auto">
            Choose the plan that works best for you. Start free and upgrade when you need more.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`bg-slate-900 border rounded-2xl p-8 relative ${
                plan.highlight 
                  ? 'border-emerald-500/50 shadow-lg shadow-emerald-500/10' 
                  : 'border-slate-800'
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}
              
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-white mb-2">{plan.name}</h2>
                <div className="flex items-baseline justify-center space-x-1">
                  <span className="text-4xl font-bold text-white">{plan.price}</span>
                  <span className="text-slate-400">/{plan.period}</span>
                </div>
                <p className="text-slate-400 text-sm mt-2">{plan.description}</p>
              </div>

              <ul className="space-y-3 mb-8" aria-label={`${plan.name} plan features`}>
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center space-x-3">
                    {feature.included ? (
                      <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" aria-hidden="true" />
                    ) : (
                      <X className="w-5 h-5 text-slate-600 flex-shrink-0" aria-hidden="true" />
                    )}
                    <span className={feature.included ? 'text-slate-200' : 'text-slate-500'}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => {
                  if (plan.name === 'Pro' && !plan.ctaDisabled) {
                    handleUpgrade();
                  } else if (plan.name === 'Free' && !isAuthenticated) {
                    navigate('/signup');
                  }
                }}
                disabled={plan.ctaDisabled || (plan.name === 'Pro' && loading)}
                className={`w-full py-3 px-6 rounded-xl font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
                  plan.highlight
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/25 disabled:from-slate-600 disabled:to-slate-600 disabled:shadow-none'
                    : 'bg-slate-800 hover:bg-slate-700 text-white disabled:bg-slate-800 disabled:text-slate-500'
                }`}
                aria-busy={plan.name === 'Pro' && loading}
              >
                {plan.name === 'Pro' && loading ? 'Loading...' : plan.cta}
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

// ============================================
// Scanner Pages
// ============================================

// New Scan Page
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
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-12 px-4">
      <main id="main-content" className="container mx-auto max-w-2xl" role="main" aria-labelledby="scan-heading">
        <div className="text-center mb-8">
          <h1 id="scan-heading" className="text-3xl font-bold text-white mb-4">Start New Scan</h1>
          <p className="text-slate-300">Enter a URL to analyze for accessibility issues</p>
        </div>

        {!canScan && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-6 mb-8 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" aria-hidden="true" />
            <p className="text-amber-200 font-medium mb-2">Scan Limit Reached</p>
            <p className="text-amber-300/80 text-sm mb-4">
              You've used all your free scans this month. Upgrade to Pro for unlimited scans.
            </p>
            <Link
              to="/pricing"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-2 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-600 transition-all"
            >
              <span>Upgrade to Pro</span>
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </Link>
          </div>
        )}

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6" aria-labelledby="scan-heading">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="scan-url" className="block text-sm font-medium text-slate-200 mb-2">
                Website URL <span className="text-red-400" aria-hidden="true">*</span>
              </label>
              <div className="relative">
                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" aria-hidden="true" />
                <input
                  type="url"
                  id="scan-url"
                  data-testid="scan-url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all"
                  placeholder="https://example.com"
                  required
                  disabled={!canScan}
                />
              </div>
              <p className="text-slate-400 text-sm mt-2">
                Enter the full URL including https://
              </p>
            </div>

            <button
              type="submit"
              data-testid="scan-submit"
              disabled={loading || !canScan || !url.trim()}
              aria-busy={loading}
              className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-lg shadow-emerald-500/25 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Starting Scan...</span>
                </span>
              ) : (
                <span className="flex items-center justify-center space-x-2">
                  <Search className="w-5 h-5" aria-hidden="true" />
                  <span>Start Accessibility Scan</span>
                </span>
              )}
            </button>
          </form>

          {user && (
            <div className="mt-6 pt-6 border-t border-slate-800 text-center">
              <p className="text-slate-400 text-sm">
                {user.scans_remaining === -1 ? (
                  <span className="text-emerald-400">Unlimited scans available</span>
                ) : (
                  <>
                    <span className="text-white font-medium">{user.scans_remaining}</span> scans remaining this month
                  </>
                )}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

// My Scans Page
const MyScansPage = () => {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const data = await scansAPI.getAll();
        setScans(data);
      } catch (err) {
        setError('Failed to load scans');
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, []);

  const handleDelete = async (scanId) => {
    if (!window.confirm('Are you sure you want to delete this scan?')) return;
    try {
      await scansAPI.delete(scanId);
      setScans(scans.filter(s => s.id !== scanId));
    } catch (err) {
      alert('Failed to delete scan');
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
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-12 px-4">
      <main id="main-content" className="container mx-auto max-w-4xl" role="main" aria-labelledby="my-scans-heading">
        <div className="flex justify-between items-center mb-8">
          <h1 id="my-scans-heading" className="text-3xl font-bold text-white">My Scans</h1>
          <Link
            to="/scan"
            className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-6 py-2 rounded-lg font-medium transition-all"
          >
            New Scan
          </Link>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg mb-6" role="alert">
            {error}
          </div>
        )}

        {scans.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" aria-hidden="true" />
            <h2 className="text-xl font-semibold text-white mb-2">No scans yet</h2>
            <p className="text-slate-400 mb-6">Start your first accessibility scan to see results here.</p>
            <Link
              to="/scan"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-6 py-3 rounded-lg font-medium hover:from-emerald-600 hover:to-teal-600 transition-all"
            >
              <Search className="w-5 h-5" aria-hidden="true" />
              <span>Start New Scan</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {scans.map((scan) => (
              <div
                key={scan.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/scan-results/${scan.id}`}
                      className="text-white font-medium hover:text-emerald-400 transition-colors truncate block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded"
                    >
                      {scan.url}
                    </Link>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" aria-hidden="true" />
                        <span>{formatDate(scan.createdAt)}</span>
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        scan.status === 'completed' 
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : scan.status === 'pending'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-red-500/20 text-red-300'
                      }`}>
                        {scan.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 ml-4">
                    {scan.score !== null && scan.score !== undefined && (
                      <div className={`text-2xl font-bold ${getScoreColorClass(scan.score)}`}>
                        {scan.score}
                      </div>
                    )}
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/scan-results/${scan.id}`}
                        className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                        aria-label={`View scan results for ${scan.url}`}
                      >
                        <ExternalLink className="w-5 h-5" aria-hidden="true" />
                      </Link>
                      <button
                        onClick={() => handleDelete(scan.id)}
                        className="p-2 text-slate-400 hover:text-red-400 transition-colors rounded-lg hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                        aria-label={`Delete scan for ${scan.url}`}
                      >
                        <Trash2 className="w-5 h-5" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

// Scan Results Page
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

// ============================================
// Scan Analytics & History Page
// ============================================

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

// Dashboard Page
const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchScans = async () => {
      try {
        const data = await scansAPI.getAll();
        setScans(data.slice(0, 5));
      } catch (err) {
        console.error('Failed to fetch scans:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchScans();
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-8 px-4">
      <main id="main-content" className="container mx-auto max-w-6xl" role="main" aria-labelledby="dashboard-heading">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 id="dashboard-heading" className="text-3xl font-bold text-white mb-2">
            Welcome back, {user?.full_name || user?.email?.split('@')[0]}
          </h1>
          <p className="text-slate-400">
            {user?.scans_remaining === -1 
              ? 'You have unlimited scans with your Pro plan' 
              : `You have ${user?.scans_remaining} scans remaining this month`}
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link
            to="/scan"
            className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 rounded-2xl p-6 hover:border-emerald-500/50 transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-500/30 transition-all">
              <Search className="w-6 h-6 text-emerald-400" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">New Scan</h2>
            <p className="text-slate-400 text-sm">Start a new accessibility scan</p>
          </Link>

          <Link
            to="/my-scans"
            className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-slate-700 transition-all">
              <BarChart3 className="w-6 h-6 text-slate-400" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">My Scans</h2>
            <p className="text-slate-400 text-sm">View all your scan history</p>
          </Link>

          {user?.plan === 'free' && (
            <Link
              to="/pricing"
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-emerald-500/30 transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-all">
                <Zap className="w-6 h-6 text-amber-400" aria-hidden="true" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Upgrade to Pro</h2>
              <p className="text-slate-400 text-sm">Get unlimited scans and PDF exports</p>
            </Link>
          )}
        </div>

        {/* Recent Scans */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white">Recent Scans</h2>
            {scans.length > 0 && (
              <Link to="/my-scans" className="text-emerald-400 hover:text-emerald-300 text-sm font-medium">
                View All →
              </Link>
            )}
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400" aria-hidden="true" />
            </div>
          ) : scans.length === 0 ? (
            <div className="text-center py-8">
              <Search className="w-10 h-10 text-slate-600 mx-auto mb-3" aria-hidden="true" />
              <p className="text-slate-400">No scans yet. Start your first scan!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {scans.map((scan) => (
                <Link
                  key={scan.id}
                  to={`/scan-results/${scan.id}`}
                  className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl hover:bg-slate-800 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{scan.url}</p>
                    <p className="text-slate-400 text-sm">{formatDate(scan.createdAt)}</p>
                  </div>
                  <div className="flex items-center space-x-4 ml-4">
                    <span className={`text-2xl font-bold ${getScoreColorClass(scan.score || 0)}`}>
                      {scan.score ?? '-'}
                    </span>
                    <ChevronRight className="w-5 h-5 text-slate-400" aria-hidden="true" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

// ============================================
// Main App Component
// ============================================

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-slate-950">
        <BrowserRouter>
          <Navigation />
          <EmailVerificationBanner />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
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
            <Route path="/analytics" element={
              <ProtectedRoute>
                <ScanAnalyticsPage />
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
