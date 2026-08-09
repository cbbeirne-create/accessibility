/**
 * Centralized API Service
 * 
 * Creates an Axios instance with:
 * - Base URL configuration from environment
 * - JWT token interceptor for authenticated requests
 * - Response error handling
 * - Token refresh/logout on 401 errors
 */
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Create axios instance with default config
const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor - adds JWT token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handles errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      
      // Only redirect if not already on auth pages
      const currentPath = window.location.pathname;
      if (!currentPath.includes('/login') && 
          !currentPath.includes('/signup') && 
          !currentPath.includes('/forgot-password') &&
          !currentPath.includes('/reset-password')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ============================================
// Authentication API
// ============================================

export const authAPI = {
  /**
   * Login user with email and password
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<{access_token: string, token_type: string}>}
   */
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  /**
   * Register new user
   * @param {string} email 
   * @param {string} password 
   * @param {string} fullName 
   * @returns {Promise<{access_token: string, token_type: string}>}
   */
  signup: async (email, password, fullName) => {
    const response = await api.post('/auth/signup', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  /**
   * Get current user profile
   * @returns {Promise<UserProfile>}
   */
  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Request password reset email
   * @param {string} email 
   * @returns {Promise<{message: string, success: boolean}>}
   */
  forgotPassword: async (email) => {
    const response = await api.post('/auth/forgot-password', { email });
    return response.data;
  },

  /**
   * Verify if reset token is valid
   * @param {string} token 
   * @returns {Promise<{valid: boolean, message: string}>}
   */
  verifyResetToken: async (token) => {
    const response = await api.get(`/auth/verify-reset-token?token=${token}`);
    return response.data;
  },

  /**
   * Reset password with token
   * @param {string} token 
   * @param {string} newPassword 
   * @returns {Promise<{message: string, success: boolean}>}
   */
  resetPassword: async (token, newPassword) => {
    const response = await api.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  /**
   * Verify email with token
   * @param {string} token 
   * @returns {Promise<{message: string, success: boolean}>}
   */
  verifyEmail: async (token) => {
    const response = await api.post('/auth/verify-email', { token });
    return response.data;
  },

  /**
   * Resend verification email
   * @param {string} email 
   * @returns {Promise<{message: string, success: boolean}>}
   */
  resendVerification: async (email) => {
    const response = await api.post('/auth/resend-verification', { email });
    return response.data;
  },

  /**
   * Get email verification status
   * @returns {Promise<{email_verified: boolean, email: string}>}
   */
  getVerificationStatus: async () => {
    const response = await api.get('/auth/verification-status');
    return response.data;
  },
};

// ============================================
// Scans API
// ============================================

export const scansAPI = {
  /**
   * Get all scans for current user
   * @returns {Promise<Scan[]>}
   */
  getAll: async () => {
    const response = await api.get('/scans');
    return response.data;
  },

  /**
   * Get single scan by ID
   * @param {string} scanId 
   * @returns {Promise<Scan>}
   */
  getById: async (scanId) => {
    const response = await api.get(`/scans/${scanId}`);
    return response.data;
  },

  /**
   * Create new scan request
   * @param {string} url - URL to scan
   * @param {string} tool - Scanning tool (default: axe-core)
   * @returns {Promise<Scan>}
   */
  create: async (url, tool = 'axe-core') => {
    const response = await api.post('/scans', { url, tool });
    return response.data;
  },

  /**
   * Delete scan by ID
   * @param {string} scanId 
   * @returns {Promise<{message: string}>}
   */
  delete: async (scanId) => {
    const response = await api.delete(`/scans/${scanId}`);
    return response.data;
  },

  /**
   * Export scan as PDF
   * @param {string} scanId 
   * @returns {Promise<Blob>}
   */
  exportPDF: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/export/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Export scan as JSON
   * @param {string} scanId 
   * @returns {Promise<Object>}
   */
  exportJSON: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/export/json`);
    return response.data;
  },

  /**
   * Get scan screenshot
   * @param {string} scanId 
   * @returns {Promise<Blob>}
   */
  getScreenshot: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/screenshot`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get scan history for a specific URL
   * @param {string} url 
   * @returns {Promise<{url: string, total_scans: number, scans: Array, trend: Object}>}
   */
  getHistoryByUrl: async (url) => {
    const response = await api.get('/scans/history/by-url', { params: { url } });
    return response.data;
  },

  /**
   * Compare two scans
   * @param {string} scanId1 
   * @param {string} scanId2 
   * @returns {Promise<Object>}
   */
  compare: async (scanId1, scanId2) => {
    const response = await api.get(`/scans/compare/${scanId1}/${scanId2}`);
    return response.data;
  },

  /**
   * Get overall scan statistics
   * @returns {Promise<Object>}
   */
  getStats: async () => {
    const response = await api.get('/scans/stats');
    return response.data;
  },

  /**
   * Get list of unique scanned URLs
   * @returns {Promise<{urls: Array, total: number}>}
   */
  getScannedUrls: async () => {
    const response = await api.get('/scans/urls');
    return response.data;
  },
};

// ============================================
// Subscription API
// ============================================

export const subscriptionAPI = {
  /**
   * Create Stripe checkout session for Pro upgrade
   * @returns {Promise<{checkout_url: string}>}
   */
  createCheckoutSession: async () => {
    const response = await api.post('/subscription/create-checkout-session');
    return response.data;
  },
};

// ============================================
// Health API
// ============================================

export const healthAPI = {
  /**
   * Check API health status
   * @returns {Promise<{status: string, services: Object}>}
   */
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

// Export the axios instance for custom requests
export default api;
