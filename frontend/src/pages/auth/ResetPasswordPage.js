/**
 * Reset Password Page
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader announcements for errors
 */
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Lock, CheckCircle, X, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';

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

export default ResetPasswordPage;
