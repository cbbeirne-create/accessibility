/**
 * Email Verification Page
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader announcements for state changes
 */
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CheckCircle, X } from 'lucide-react';
import { authAPI } from '../../services/api';

const VerifyEmailPage = () => {
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const location = useLocation();

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

export default VerifyEmailPage;
