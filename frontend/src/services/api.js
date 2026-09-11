import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
let accessToken = null;

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
  withCredentials: true,
});

let authHandlers = { onLogout: null, onLogin: null };
export const setAuthHandlers = (handlers = {}) => { authHandlers = { ...authHandlers, ...handlers }; };
export const getToken = () => accessToken;
export const setToken = (token) => { accessToken = token || null; };

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let refreshPromise = null;
const refreshAccessToken = async () => {
  if (!refreshPromise) {
    refreshPromise = axios.post(`${BACKEND_URL}/api/auth/refresh`, {}, { withCredentials: true, timeout: 15000 })
      .then((res) => {
        const token = res.data?.access_token;
        if (!token) throw new Error('No access token returned');
        setToken(token);
        authHandlers.onLogin?.(token);
        return token;
      })
      .catch((error) => {
        setToken(null);
        authHandlers.onLogout?.();
        throw error;
      })
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isAuthEndpoint = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/signup') || original?.url?.includes('/auth/refresh');
    if (error.response?.status === 401 && original && !original._retry && !original._skipAuthRefresh && !isAuthEndpoint) {
      try {
        const token = await refreshAccessToken();
        original._retry = true;
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      } catch (_) {
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  },
);

export const authAPI = {
  login: async (email, password) => (await api.post('/auth/login', { email, password })).data,
  signup: async (email, password, fullName) => (await api.post('/auth/signup', { email, password, full_name: fullName })).data,
  getProfile: async () => (await api.get('/auth/me')).data,
  refresh: async () => {
    const token = await refreshAccessToken();
    return { access_token: token, token_type: 'bearer' };
  },
  logout: async () => {
    try { return (await api.post('/auth/logout', {}, { _skipAuthRefresh: true })).data; }
    finally { setToken(null); }
  },
  forgotPassword: async (email) => (await api.post('/auth/forgot-password', { email }, { _skipAuthRefresh: true })).data,
  verifyResetToken: async (token) => (await api.get('/auth/verify-reset-token', { params: { token }, _skipAuthRefresh: true })).data,
  resetPassword: async (token, newPassword) => (await api.post('/auth/reset-password', { token, new_password: newPassword }, { _skipAuthRefresh: true })).data,
  verifyEmail: async (token) => (await api.post('/auth/verify-email', { token }, { _skipAuthRefresh: true })).data,
  resendVerification: async (email) => (await api.post('/auth/resend-verification', { email }, { _skipAuthRefresh: true })).data,
  getVerificationStatus: async () => (await api.get('/auth/verification-status')).data,
};

export const scansAPI = {
  getAll: async () => (await api.get('/scans')).data,
  getById: async (scanId) => (await api.get(`/scans/${scanId}`)).data,
  create: async (url, tool = 'axe-core') => (await api.post('/scans', { url, tool })).data,
  delete: async (scanId) => (await api.delete(`/scans/${scanId}`)).data,
  exportPDF: async (scanId) => (await api.get(`/scans/${scanId}/export/pdf`, { responseType: 'blob' })).data,
  exportJSON: async (scanId) => (await api.get(`/scans/${scanId}/export/json`)).data,
  getScreenshot: async (scanId) => (await api.get(`/scans/${scanId}/screenshot`, { responseType: 'blob' })).data,
  getEvidenceScreenshot: async (scanId, evidenceId) => (await api.get(`/scans/${scanId}/evidence/${encodeURIComponent(evidenceId)}`, { responseType: 'blob' })).data,
  getHistoryByUrl: async (url) => (await api.get('/scans/history/by-url', { params: { url } })).data,
  compare: async (a, b) => (await api.get(`/scans/compare/${a}/${b}`)).data,
  getStats: async () => (await api.get('/scans/stats')).data,
  getScannedUrls: async () => (await api.get('/scans/urls')).data,
};

export const subscriptionAPI = { createCheckoutSession: async () => (await api.post('/subscription/create-checkout-session')).data };

export const scheduledScansAPI = {
  getAll: async () => (await api.get('/scheduled-scans')).data,
  getById: async (id) => (await api.get(`/scheduled-scans/${id}`)).data,
  create: async (url, intervalDays) => (await api.post('/scheduled-scans', { url, interval_days: intervalDays })).data,
  update: async (id, data) => (await api.put(`/scheduled-scans/${id}`, data)).data,
  delete: async (id) => (await api.delete(`/scheduled-scans/${id}`)).data,
  toggle: async (id) => (await api.post(`/scheduled-scans/${id}/toggle`)).data,
  getLimits: async () => (await api.get('/scheduled-scans/limits/info')).data,
};

export const notificationsAPI = {
  getAll: async (unreadOnly = false) => (await api.get('/notifications', { params: { unread_only: unreadOnly } })).data,
  getUnreadCount: async () => (await api.get('/notifications/unread-count')).data,
  markAsRead: async (id) => (await api.put(`/notifications/${id}/read`)).data,
  markAllAsRead: async () => (await api.put('/notifications/read-all')).data,
  delete: async (id) => (await api.delete(`/notifications/${id}`)).data,
  clearAll: async () => (await api.delete('/notifications/clear-all')).data,
};

export const healthAPI = { check: async () => (await api.get('/health')).data };

export const organizationsAPI = {
  getCurrent: async () => (await api.get('/organizations/current')).data,
  create: async (name) => (await api.post('/organizations', { name })).data,
  get: async (id) => (await api.get(`/organizations/${id}`)).data,
  update: async (id, data) => (await api.put(`/organizations/${id}`, data)).data,
  delete: async (id) => (await api.delete(`/organizations/${id}`)).data,
  inviteMember: async (id, email) => (await api.post(`/organizations/${id}/invite`, { email })).data,
  cancelInvite: async (id, inviteId) => (await api.delete(`/organizations/${id}/invites/${inviteId}`)).data,
  getPendingInvites: async () => (await api.get('/organizations/invites/pending')).data,
  acceptInvite: async (token) => (await api.post(`/organizations/invites/${token}/accept`)).data,
  declineInvite: async (token) => (await api.post(`/organizations/invites/${token}/decline`)).data,
  removeMember: async (id, userId) => (await api.delete(`/organizations/${id}/members/${userId}`)).data,
  leave: async () => (await api.post('/organizations/leave')).data,
  transferOwnership: async (id, newOwnerId) => (await api.post(`/organizations/${id}/transfer-ownership`, { new_owner_id: newOwnerId })).data,
};

export { api as axiosInstance };
export default api;
