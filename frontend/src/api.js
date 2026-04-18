import axios from 'axios';

// In production (Vercel), set VITE_API_BASE_URL to your Railway backend URL.
// Locally, defaults to http://localhost:8000/api/v1
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Attach JWT token to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('paykarobro_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global error handling — redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('paykarobro_token');
      // In a real SPA you'd redirect to /login
    }
    return Promise.reject(error);
  }
);

export default api;
