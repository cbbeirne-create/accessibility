import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const SignupPage = () => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { signup, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate('/');
  }, [isAuthenticated, navigate]);

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
    const result = await signup(email.trim(), password, fullName.trim());
    setLoading(false);
    if (result.success) navigate('/');
    else setError(result.error);
  };

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 flex items-center justify-center px-4 py-8">
      <main id="main-content" className="w-full max-w-md" aria-labelledby="signup-heading">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4" aria-hidden="true">
            <Shield className="w-9 h-9 text-white" aria-hidden="true" />
          </div>
          <h1 id="signup-heading" className="text-3xl font-bold text-white mb-2">Create your account</h1>
          <p className="text-slate-300">Create an account, verify your email, then run your first accessibility scan.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5" aria-labelledby="signup-heading">
            {error && <div className="bg-red-500/10 border border-red-500/20 text-red-300 px-4 py-3 rounded-lg text-sm" role="alert">{error}</div>}

            <div>
              <label htmlFor="signup-name" className="block text-sm font-medium text-slate-200 mb-2">Full name</label>
              <input id="signup-name" name="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} autoComplete="name" className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400" />
            </div>

            <div>
              <label htmlFor="signup-email" className="block text-sm font-medium text-slate-200 mb-2">Email address <span aria-hidden="true" className="text-red-400">*</span></label>
              <input type="email" id="signup-email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required aria-required="true" className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400" />
            </div>

            <div>
              <label htmlFor="signup-password" className="block text-sm font-medium text-slate-200 mb-2">Password <span aria-hidden="true" className="text-red-400">*</span></label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} id="signup-password" name="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" minLength={12} maxLength={128} required aria-required="true" aria-describedby="signup-password-help" className="w-full px-4 py-3 pr-12 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400" />
                <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 p-1 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword}>
                  {showPassword ? <EyeOff className="w-5 h-5" aria-hidden="true" /> : <Eye className="w-5 h-5" aria-hidden="true" />}
                </button>
              </div>
              <p id="signup-password-help" className="text-xs text-slate-400 mt-2">Use at least 12 characters. A unique passphrase is recommended.</p>
            </div>

            <div>
              <label htmlFor="signup-confirm-password" className="block text-sm font-medium text-slate-200 mb-2">Confirm password <span aria-hidden="true" className="text-red-400">*</span></label>
              <input type={showPassword ? 'text' : 'password'} id="signup-confirm-password" name="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} autoComplete="new-password" minLength={12} maxLength={128} required aria-required="true" className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-400" />
            </div>

            <button type="submit" disabled={loading} aria-busy={loading} className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold py-3 px-6 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="mt-6 text-center text-slate-300 text-sm">Already have an account? <Link to="/login" className="text-emerald-300 underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded">Sign in</Link></p>
        </div>
      </main>
    </div>
  );
};

export default SignupPage;
