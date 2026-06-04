import axios from "axios";
import { getToken, clearAuth } from "./auth";

const api = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      clearAuth();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
export { api };
