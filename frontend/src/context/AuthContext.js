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
import React, { useState, useEffect, createContext, useContext } from 'react';
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
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  // Load user profile on mount or token change
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await authAPI.getProfile();
          setUser(userData);
        } catch (error) {
          // Token is invalid or expired
          console.error('Failed to load user profile:', error);
          logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

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
      
      // Store token
      localStorage.setItem('access_token', access_token);
      setToken(access_token);
      
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
      localStorage.setItem('access_token', access_token);
      setToken(access_token);
      
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
   * Logout user - clears token and user data
   */
  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  /**
   * Refresh user profile data
   * Useful after plan upgrades or profile updates
   */
  const refreshUser = async () => {
    if (token) {
      try {
        const userData = await authAPI.getProfile();
        setUser(userData);
      } catch (error) {
        console.error('Failed to refresh user:', error);
      }
    }
  };

  const value = {
    user,
    login,
    signup,
    logout,
    loading,
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
