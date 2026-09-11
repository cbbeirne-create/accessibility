import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const baseURL = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
  withCredentials: true,
});

const sessionClient = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
  withCredentials: true,
});

let authHandlers = { onLogout: null, onLogin: null };
let accessToken = null;

export const setAuthHandlers = (handlers = {}) => { authHandlers = { ...authHandlers, ...handlers }; };
export const getToken = () => accessToken;
export const setToken = (token) => { accessToken = token || null; };

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status !== 401 || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    if (!refreshPromise) {
      refreshPromise = sessionClient.post('/auth/refresh')
        .then((response) => {
          const newToken = response.data?.access_token;
          if (!newToken) throw new Error('Refresh response did not contain an access token');
          setToken(newToken);
          authHandlers.onLogin?.(newToken);
          return newToken;
        })
        .catch((refreshError) => {
          setToken(null);
          authHandlers.onLogout?.();
          throw refreshError;
        })
        .finally(() => { refreshPromise = null; });
    }

    try {
      const newToken = await refreshPromise;
      originalRequest.headers = originalRequest.headers || {};
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    } catch {
      return Promise.reject(error);
    }
  }
);

export const authAPI = {
  login: async (email, password) => (await api.post('/auth/login', { email, password })).data,
  signup: async (email, password, fullName) => (await api.post('/auth/signup', { email, password, full_name: fullName })).data,
  getProfile: async () => (await api.get('/auth/me')).data,
  refresh: async () => (await sessionClient.post('/auth/refresh')).data,
  logout: async () => (await sessionClient.post('/auth/logout')).data,
};

export const scansAPI = {
  getAll: async () => (await api.get('/scans')).data,
  getById: async (scanId) => (await api.get(`/scans/${scanId}`)).data,
  create: async (url, tool = 'axe-core') => (await api.post('/scans', { url, tool })).data,
  delete: async (scanId) => (await api.delete(`/scans/${scanId}`)).data,
  exportPDF: async (scanId) => (await api.get(`/scans/${scanId}/export/pdf`, { responseType: 'blob' })).data,
  exportJSON: async (scanId) => (await api.get(`/scans/${scanId}/export/json`)).data,
  getScreenshot: async (scanId) => (await api.get(`/scans/${scanId}/screenshot`, { responseType: 'blob' })).data,
  getHistoryByUrl: async (url) => (await api.get('/scans/history/by-url', { params: { url } })).data,
  compare: async (scanId1, scanId2) => (await api.get(`/scans/compare/${scanId1}/${scanId2}`)).data,
  getStats: async () => (await api.get('/scans/stats')).data,
  getScannedUrls: async () => (await api.get('/scans/urls')).data,
};

export const subscriptionAPI = {
  createCheckoutSession: async () => (await api.post('/subscription/create-checkout-session')).data,
};

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

export const healthAPI = {
  check: async () => (await api.get('/health')).data,
};

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
