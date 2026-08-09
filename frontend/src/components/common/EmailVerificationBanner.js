/**
 * Email Verification Banner Component
 * 
 * Displays a banner prompting unverified users to verify their email.
 * 
 * Accessibility Features:
 * - Proper ARIA role for alert
 * - Screen reader friendly
 */
import React, { useState } from 'react';
import { Mail, RefreshCw, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';

const EmailVerificationBanner = () => {
  const { user } = useAuth();
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

export default EmailVerificationBanner;
