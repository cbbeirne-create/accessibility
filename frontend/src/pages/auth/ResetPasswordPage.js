import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle, Eye, EyeOff, Lock, X } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';

const ResetPasswordPage = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const token = useMemo(() => new URLSearchParams(location.search).get('token'), [location.search]);

  useEffect(() => {
    if (isAuthenticated) navigate('/');
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token) {
        if (active) { setVerifying(false); setTokenValid(false); }
        return;
      }
      try {
        const result = await authAPI.verifyResetToken(token);
        if (active) setTokenValid(Boolean(result.valid));
      } catch (_) {
        if (active) setTokenValid(false);
      } finally {
        if (active) setVerifying(false);
      }
    })();
    return () => { active = false; };
  }, [token]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 12) {
      setError('Password must be at least 12 characters long');
      return;
    }
    setLoading(true);
    try {
      const result = await authAPI.resetPassword(token, password);
      if (result.success) setSuccess(true);
      else setError(result.message || 'Failed to reset password');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password. Please request a new reset link and try again.');
    } finally {
      setLoading(false);
    }
  };

  if (verifying) return <CenteredStatus title="Verifying reset link…" />;

  if (!tokenValid) {
    return (
      <CenteredCard icon={<X className="w-8 h-8 text-red-400" aria-hidden="true" />} title="Invalid or expired reset link">
        <p className="text-slate-300 mb-6">Request a new password reset link to continue.</p>
        <Link to="/forgot-password" className="block w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-6 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">Request new reset link</Link>
      </CenteredCard>
    );
  }

  if (success) {
    return (
      <CenteredCard icon={<CheckCircle className="w-8 h-8 text-emerald-400" aria-hidden="true" />} title="Password reset successful">
        <p className="text-slate-300 mb-6">Your existing sessions have been revoked. Sign in again with your new password.</p>
        <Link to="/login" className="block w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-6 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">Sign in</Link>
      </CenteredCard>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4 py-8">
      <main id="main-content" className="w-full max-w-md" aria-labelledby="reset-password-heading">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4" aria-hidden="true"><Lock className="w-9 h-9 text-white" aria-hidden="true" /></div>
          <h1 id="reset-password-heading" className="text-3xl font-bold text-white mb-2">Reset password</h1>
          <p className="text-slate-300">Choose a new unique password for your account.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5" aria-labelledby="reset-password-heading">
            {error && <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert">{error}</div>}

            <div>
              <label htmlFor="reset-password" className="block text-sm font-medium text-slate-200 mb-2">New password</label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} id="reset-password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" minLength={12} maxLength={128} required aria-describedby="reset-password-help" className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400" />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 p-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword}>{showPassword ? <EyeOff className="w-5 h-5" aria-hidden="true" /> : <Eye className="w-5 h-5" aria-hidden="true" />}</button>
              </div>
              <p id="reset-password-help" className="text-xs text-slate-400 mt-2">Use at least 12 characters. A unique passphrase is recommended.</p>
            </div>

            <div>
              <label htmlFor="reset-confirm-password" className="block text-sm font-medium text-slate-200 mb-2">Confirm new password</label>
              <input type={showPassword ? 'text' : 'password'} id="reset-confirm-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" minLength={12} maxLength={128} required className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400" />
            </div>

            <button type="submit" disabled={loading} aria-busy={loading} className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-600 text-white font-semibold py-3 px-6 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">{loading ? 'Resetting password…' : 'Reset password'}</button>
          </form>
        </div>
      </main>
    </div>
  );
};

const CenteredStatus = ({ title }) => (
  <main id="main-content" className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4" role="status" aria-live="polite">
    <div className="text-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" /><p className="mt-4 text-slate-300">{title}</p></div>
  </main>
);

const CenteredCard = ({ icon, title, children }) => (
  <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4"><main id="main-content" className="w-full max-w-md"><div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center"><div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6" aria-hidden="true">{icon}</div><h1 className="text-2xl font-bold text-white mb-4">{title}</h1>{children}</div></main></div>
);

export default ResetPasswordPage;
