/**
 * Forgot Password Page
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader announcements for errors
 */
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';

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
              you&apos;ll receive a password reset link shortly.
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
          <p className="text-slate-300">Enter your email and we&apos;ll send you a reset link</p>
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

export default ForgotPasswordPage;
