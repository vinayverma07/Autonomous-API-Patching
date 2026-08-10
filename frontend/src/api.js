import axios from 'axios';

const API = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

// Interceptor to attach JWT token to headers if present in localStorage
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default API;