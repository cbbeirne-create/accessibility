/**
 * Authentication Context
 * 
 * Provides authentication state and methods throughout the app:
 * - User profile data
 * - Login/Signup/Logout functions
 * - Loading state for auth operations
 * - Protected route support
 * 
 * Accessibility: This context maintains proper loading states
 * to ensure screen readers receive appropriate feedback.
 */
import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { authAPI } from '../services/api';

// Create the context
const AuthContext = createContext(null);

/**
 * Custom hook to access auth context
 * @returns {AuthContextValue}
 * @throws {Error} If used outside AuthProvider
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

/**
 * Authentication Provider Component
 * Wraps the application to provide auth state and methods
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // initial bootstrap loading
  const [refreshingUser, setRefreshingUser] = useState(false); // local refresh flag for profile updates
  const [token, setToken] = useState(null);

  // Helper to persist token in storage and state (defensive)
  const persistToken = (t) => {
    try {
      if (t) {
        localStorage.setItem('access_token', t);
      } else {
        localStorage.removeItem('access_token');
      }
    } catch (e) {
      // ignore storage errors
      console.warn('Failed to access localStorage for token', e);
    }
    setToken(t || null);
  };

  // On mount: read token from localStorage (guard SSR) and load user
  useEffect(() => {
    let mounted = true;

    const init = async () => {
      let t = null;
      try {
        if (typeof window !== 'undefined') {
          t = localStorage.getItem('access_token');
        }
      } catch (e) {
        // ignore
      }

      if (!mounted) return;
      setToken(t);

      if (t) {
        try {
          const userData = await authAPI.getProfile();
          if (!mounted) return;
          setUser(userData);
        } catch (error) {
          console.error('Failed to load user profile:', error);
          // try server-side revoke if possible
          try {
            await authAPI.logout();
          } catch (e) {
            // ignore
          }
          persistToken(null);
          setUser(null);
        }
      }

      if (mounted) setLoading(false);
    };

    init();

    // Sync across tabs: listen for access_token changes in localStorage
    const onStorage = (e) => {
      if (e.key === 'access_token') {
        const newToken = e.newValue;
        setToken(newToken);
        if (!newToken) {
          setUser(null);
        }
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('storage', onStorage);
    }

    return () => {
      mounted = false;
      if (typeof window !== 'undefined') {
        window.removeEventListener('storage', onStorage);
      }
    };
  }, []);

  /**
   * Login user with email and password
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  const login = async (email, password) => {
    try {
      const data = await authAPI.login(email, password);
      const { access_token } = data;

      // Store token and update state
      persistToken(access_token);

      // Fetch user profile
      const userData = await authAPI.getProfile();
      setUser(userData);

      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please check your credentials.' 
      };
    }
  };

  /**
   * Register new user
   * @param {string} email 
   * @param {string} password 
   * @param {string} fullName 
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  const signup = async (email, password, fullName) => {
    try {
      const data = await authAPI.signup(email, password, fullName);
      const { access_token } = data;
      
      // Store token
      persistToken(access_token);
      
      // Fetch user profile
      const userData = await authAPI.getProfile();
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Signup failed. Please try again.' 
      };
    }
  };

  /**
   * Logout user - clears token and user data. Attempts server-side revoke if available.
   */
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (e) {
      // ignore server errors on logout
    }
    try { persistToken(null); } catch (e) {}
    setUser(null);
  };

  /**
   * Refresh user profile data
   * Useful after joining/leaving teams, plan upgrades, or profile updates.
   * Uses a separate `refreshingUser` flag so we don't show the global bootstrap loader.
   * Returns the refreshed user object on success, or null on failure.
   */
  const refreshUser = useCallback(async () => {
    if (!token) {
      setUser(null);
      return null;
    }

    try {
      setRefreshingUser(true);
      const userData = await authAPI.getProfile();
      setUser(userData);
      return userData;
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh failed due to auth, clear token
      if (error.response?.status === 401) {
        try { await authAPI.logout(); } catch (e) {}
        persistToken(null);
        setUser(null);
      }
      return null;
    } finally {
      setRefreshingUser(false);
    }
  }, [token]);

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

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Protected Route Component
 * Wraps routes that require authentication
 * Shows loading spinner while checking auth state
 * Redirects to login if not authenticated
 * 
 * Accessibility: Uses proper ARIA attributes for loading state
 */
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
