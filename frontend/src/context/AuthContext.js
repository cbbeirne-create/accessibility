import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { authAPI, setAuthHandlers, setToken } from '../services/api';
import { friendlyError } from '../utils/errors';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshingUser, setRefreshingUser] = useState(false);

  useEffect(() => {
    setAuthHandlers({
      onLogin: (token) => setToken(token),
      onLogout: () => { setToken(null); setUser(null); },
    });
    let active = true;
    (async () => {
      try {
        await authAPI.refresh();
        const profile = await authAPI.getProfile();
        if (active) setUser(profile);
      } catch (_) {
        setToken(null);
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const login = async (email, password) => {
    try {
      const { access_token } = await authAPI.login(email, password);
      setToken(access_token);
      setUser(await authAPI.getProfile());
      return { success: true };
    } catch (error) {
      return { success: false, error: friendlyError(error, 'Login failed. Please check your credentials.') };
    }
  };

  const signup = async (email, password, fullName) => {
    try {
      const { access_token } = await authAPI.signup(email, password, fullName);
      setToken(access_token);
      setUser(await authAPI.getProfile());
      return { success: true };
    } catch (error) {
      return { success: false, error: friendlyError(error, 'Signup failed. Please try again.') };
    }
  };

  const logout = async () => {
    try { await authAPI.logout(); } catch (_) { setToken(null); }
    setUser(null);
  };

  const refreshUser = useCallback(async () => {
    try {
      setRefreshingUser(true);
      const profile = await authAPI.getProfile();
      setUser(profile);
      return profile;
    } catch (error) {
      if (error.response?.status === 401) setUser(null);
      return null;
    } finally {
      setRefreshingUser(false);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading, refreshingUser, isAuthenticated: !!user, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center" role="status" aria-live="polite">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto" aria-hidden="true" />
          <p className="mt-4 text-slate-400 text-sm">Checking your session…</p>
        </div>
      </div>
    );
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

export default AuthContext;
