/**
 * Centralized API Service
 *
 * Creates an Axios instance with:
 * - Base URL configuration from environment
 * - JWT token interceptor for authenticated requests
 * - Response error handling
 * - Token refresh/logout on 401 errors (deduplicated)
 *
 * Exposes `setAuthHandlers` so the auth context can register callbacks
 * (onLogin/onLogout) to keep client state in sync when tokens are refreshed or revoked.
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

// ------------ Auth handler hooks (registered by AuthContext) ------------
let authHandlers = {
  onLogout: null, // called when refresh fails and we need to clear client state
  onLogin: null,  // optional: called when a new token is obtained
};

export const setAuthHandlers = (handlers = {}) => {
  authHandlers = { ...authHandlers, ...handlers };
};

// Helper to safely read token from storage (so cross-tab updates are respected)
const getToken = () => {
  try {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  } catch (e) {
    return null;
  }
};

// Helper to persist token
const setToken = (token) => {
  try {
    if (typeof window === 'undefined') return;
    if (token) localStorage.setItem('access_token', token);
    else localStorage.removeItem('access_token');
  } catch (e) {
    // ignore storage errors
  }
};

// Attach token to outgoing requests
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Token refresh dedupe
let isRefreshing = false;
let refreshPromise = null;

// Response interceptor - handles errors globally and attempts refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If request config has _retry flag, do not retry again
    if (error.response?.status === 401 && !originalRequest?._retry) {
      // Attempt refresh
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = (async () => {
          try {
            // Try to refresh via auth endpoint. This may rely on httpOnly refresh cookie
            const res = await api.post('/auth/refresh');
            const newToken = res.data?.access_token;
            if (newToken) {
              setToken(newToken);
              if (typeof authHandlers.onLogin === 'function') {
                try { authHandlers.onLogin(newToken); } catch (e) { /* ignore */ }
              }
              return newToken;
            }
            // If no token returned, treat as failure
            throw new Error('No token from refresh');
          } catch (refreshErr) {
            // Refresh failed -> invoke logout handler if present
            if (typeof authHandlers.onLogout === 'function') {
              try { authHandlers.onLogout(); } catch (e) { /* ignore */ }
            }
            throw refreshErr;
          } finally {
            isRefreshing = false;
            refreshPromise = null;
          }
        })();
      }

      try {
        const newToken = await refreshPromise;
        // Retry original request with new token
        originalRequest._retry = true;
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh failed, propagate original error (logout handler already called)
        return Promise.reject(error);
      }
    }

    // For other errors or retry attempts, just reject
    return Promise.reject(error);
  }
);

// ============================================
// Authentication API
// ============================================
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  signup: async (email, password, fullName) => {
    const response = await api.post('/auth/signup', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Refresh endpoint - expected to return a fresh access token (or set httpOnly cookie)
  refresh: async () => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  // Logout/revoke endpoint - invalidate refresh tokens server-side if supported
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
};

// ============================================
// Other API groups remain unchanged but go through the same axios instance
// ============================================

export const scansAPI = {
  getAll: async () => {
    const response = await api.get('/scans');
    return response.data;
  },
  getById: async (scanId) => {
    const response = await api.get(`/scans/${scanId}`);
    return response.data;
  },
  create: async (url, tool = 'axe-core') => {
    const response = await api.post('/scans', { url, tool });
    return response.data;
  },
  delete: async (scanId) => {
    const response = await api.delete(`/scans/${scanId}`);
    return response.data;
  },
  exportPDF: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/export/pdf`, { responseType: 'blob' });
    return response.data;
  },
  exportJSON: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/export/json`);
    return response.data;
  },
  getScreenshot: async (scanId) => {
    const response = await api.get(`/scans/${scanId}/screenshot`, { responseType: 'blob' });
    return response.data;
  },
  getHistoryByUrl: async (url) => {
    const response = await api.get('/scans/history/by-url', { params: { url } });
    return response.data;
  },
  compare: async (scanId1, scanId2) => {
    const response = await api.get(`/scans/compare/${scanId1}/${scanId2}`);
    return response.data;
  },
  getStats: async () => {
    const response = await api.get('/scans/stats');
    return response.data;
  },
  getScannedUrls: async () => {
    const response = await api.get('/scans/urls');
    return response.data;
  },
};

export const subscriptionAPI = {
  createCheckoutSession: async () => {
    const response = await api.post('/subscription/create-checkout-session');
    return response.data;
  },
};

export const scheduledScansAPI = {
  getAll: async () => { const response = await api.get('/scheduled-scans'); return response.data; },
  getById: async (scheduledId) => { const response = await api.get(`/scheduled-scans/${scheduledId}`); return response.data; },
  create: async (url, intervalDays) => { const response = await api.post('/scheduled-scans', { url, interval_days: intervalDays }); return response.data; },
  update: async (scheduledId, data) => { const response = await api.put(`/scheduled-scans/${scheduledId}`, data); return response.data; },
  delete: async (scheduledId) => { const response = await api.delete(`/scheduled-scans/${scheduledId}`); return response.data; },
  toggle: async (scheduledId) => { const response = await api.post(`/scheduled-scans/${scheduledId}/toggle`); return response.data; },
  getLimits: async () => { const response = await api.get('/scheduled-scans/limits/info'); return response.data; },
};

export const notificationsAPI = {
  getAll: async (unreadOnly = false) => { const response = await api.get('/notifications', { params: { unread_only: unreadOnly } }); return response.data; },
  getUnreadCount: async () => { const response = await api.get('/notifications/unread-count'); return response.data; },
  markAsRead: async (notificationId) => { const response = await api.put(`/notifications/${notificationId}/read`); return response.data; },
  markAllAsRead: async () => { const response = await api.put('/notifications/read-all'); return response.data; },
  delete: async (notificationId) => { const response = await api.delete(`/notifications/${notificationId}`); return response.data; },
  clearAll: async () => { const response = await api.delete('/notifications/clear-all'); return response.data; },
};

export const healthAPI = {
  check: async () => { const response = await api.get('/health'); return response.data; },
};

export const organizationsAPI = {
  getCurrent: async () => { const response = await api.get('/organizations/current'); return response.data; },
  create: async (name) => { const response = await api.post('/organizations', { name }); return response.data; },
  get: async (orgId) => { const response = await api.get(`/organizations/${orgId}`); return response.data; },
  update: async (orgId, data) => { const response = await api.put(`/organizations/${orgId}`, data); return response.data; },
  delete: async (orgId) => { const response = await api.delete(`/organizations/${orgId}`); return response.data; },
  inviteMember: async (orgId, email) => { const response = await api.post(`/organizations/${orgId}/invite`, { email }); return response.data; },
  cancelInvite: async (orgId, inviteId) => { const response = await api.delete(`/organizations/${orgId}/invites/${inviteId}`); return response.data; },
  getPendingInvites: async () => { const response = await api.get('/organizations/invites/pending'); return response.data; },
  acceptInvite: async (token) => { const response = await api.post(`/organizations/invites/${token}/accept`); return response.data; },
  declineInvite: async (token) => { const response = await api.post(`/organizations/invites/${token}/decline`); return response.data; },
  removeMember: async (orgId, userId) => { const response = await api.delete(`/organizations/${orgId}/members/${userId}`); return response.data; },
  leave: async () => { const response = await api.post('/organizations/leave'); return response.data; },
  transferOwnership: async (orgId, newOwnerId) => { const response = await api.post(`/organizations/${orgId}/transfer-ownership`, { new_owner_id: newOwnerId }); return response.data; },
};

// Export the axios instance and helpers
export { api as axiosInstance, getToken, setToken };
export default api;
