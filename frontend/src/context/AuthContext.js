/**
 * Authentication Context
 *
 * Access tokens are memory-only. Session persistence across reloads is restored from
 * the rotating HttpOnly refresh-token cookie, keeping bearer credentials out of web storage.
 */
import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { authAPI, setAuthHandlers, getToken as apiGetToken, setToken as apiSetToken } from '../services/api';
import { friendlyError } from '../utils/errors';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshingUser, setRefreshingUser] = useState(false);
  const [token, setTokenState] = useState(null);

  const persistToken = useCallback((nextToken) => {
    apiSetToken(nextToken);
    setTokenState(nextToken || null);
  }, []);

  useEffect(() => {
    let mounted = true;

    setAuthHandlers({
      onLogin: (newToken) => {
        if (mounted) persistToken(newToken);
      },
      onLogout: () => {
        if (!mounted) return;
        persistToken(null);
        setUser(null);
      },
    });

    const init = async () => {
      try {
        // The access token intentionally does not survive reloads. Restore the session
        // from the HttpOnly refresh cookie instead.
        const session = await authAPI.refresh();
        if (!mounted) return;
        persistToken(session.access_token);
        const userData = await authAPI.getProfile();
        if (mounted) setUser(userData);
      } catch {
        if (mounted) {
          persistToken(null);
          setUser(null);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    init();
    return () => { mounted = false; };
  }, [persistToken]);

  const login = async (email, password) => {
    try {
      const data = await authAPI.login(email, password);
      persistToken(data.access_token);
      const userData = await authAPI.getProfile();
      setUser(userData);
      return { success: true };
    } catch (error) {
      return { success: false, error: friendlyError(error, 'Login failed. Please check your credentials.') };
    }
  };

  const signup = async (email, password, fullName) => {
    try {
      const data = await authAPI.signup(email, password, fullName);
      persistToken(data.access_token);
      const userData = await authAPI.getProfile();
      setUser(userData);
      return { success: true };
    } catch (error) {
      return { success: false, error: friendlyError(error, 'Signup failed. Please try again.') };
    }
  };

  const logout = async () => {
    try { await authAPI.logout(); } catch { /* clear local state regardless */ }
    persistToken(null);
    setUser(null);
  };

  const refreshUser = useCallback(async () => {
    if (!apiGetToken()) {
      try {
        const session = await authAPI.refresh();
        persistToken(session.access_token);
      } catch {
        setUser(null);
        return null;
      }
    }

    try {
      setRefreshingUser(true);
      const userData = await authAPI.getProfile();
      setUser(userData);
      return userData;
    } catch (error) {
      console.error('Failed to refresh user:', error);
      if (error.response?.status === 401) {
        try { await authAPI.logout(); } catch { /* ignore */ }
        persistToken(null);
        setUser(null);
      }
      return null;
    } finally {
      setRefreshingUser(false);
    }
  }, [persistToken, token]);

  const value = {
    user,
    login,
    signup,
    logout,
    loading,
    refreshingUser,
    isAuthenticated: !!user,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div
        className="min-h-screen bg-slate-950 flex items-center justify-center"
        role="status"
        aria-live="polite"
        aria-label="Checking authentication status"
      >
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto"
            aria-hidden="true"
          />
          <p className="mt-4 text-slate-400 text-sm">Loading...</p>
          <span className="sr-only">Checking authentication, please wait</span>
        </div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

export default AuthContext;
