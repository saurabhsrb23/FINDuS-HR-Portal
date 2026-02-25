/**
 * Axios instance for all backend API calls.
 *
 * Features:
 *  - Base URL from NEXT_PUBLIC_API_URL
 *  - Request interceptor: attaches Bearer token from sessionStorage
 *  - Response interceptor: on 401 → attempts silent token refresh → retries
 *    original request once; if refresh fails, clears session and redirects to /login
 */

import axios, {
  AxiosError,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from "axios";

import {
  clearToken,
  getRefreshToken,
  getToken,
  updateAccessToken,
} from "@/lib/auth";

// ─── Axios instance ───────────────────────────────────────────────────────────
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // send cookies on same-origin requests
});

// ─── Request interceptor — attach Bearer token ────────────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // When sending FormData let the browser set Content-Type (with boundary).
    // Leaving Content-Type: application/json causes axios to JSON-serialize the
    // FormData body as "{}" which produces a 422 from FastAPI.
    if (config.data instanceof FormData) {
      delete (config.headers as Record<string, unknown>)["Content-Type"];
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response interceptor — auto refresh on 401 ───────────────────────────────
let _isRefreshing = false;
let _failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (reason?: unknown) => void;
}> = [];

function _processQueue(error: Error | null, token: string | null) {
  _failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  _failedQueue = [];
}

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only handle 401 once per request
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (_isRefreshing) {
      // Queue this request until the refresh is done
      return new Promise<string>((resolve, reject) => {
        _failedQueue.push({ resolve, reject });
      }).then((newToken) => {
        originalRequest.headers!.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      });
    }

    originalRequest._retry = true;
    _isRefreshing = true;

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      await clearToken();
      if (typeof window !== "undefined") window.location.href = "/login";
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post<{
        access_token: string;
        refresh_token: string;
        role: string;
        user_id: string;
      }>(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/refresh`,
        { refresh_token: refreshToken }
      );

      updateAccessToken(data.access_token);

      // Also update httpOnly cookie
      await fetch("/api/set-cookie", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          access_token: data.access_token,
          refresh_token: data.refresh_token,
        }),
      });

      _processQueue(null, data.access_token);
      originalRequest.headers!.Authorization = `Bearer ${data.access_token}`;
      return api(originalRequest);
    } catch (refreshError) {
      _processQueue(refreshError as Error, null);
      await clearToken();
      if (typeof window !== "undefined") window.location.href = "/login";
      return Promise.reject(refreshError);
    } finally {
      _isRefreshing = false;
    }
  }
);

// ─── Auth API helpers ─────────────────────────────────────────────────────────
export interface RegisterPayload {
  email: string;
  password: string;
  confirm_password: string;
  full_name: string;
  role: string;
  company_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: string;
  user_id: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export const authAPI = {
  register: (data: RegisterPayload): Promise<AxiosResponse<UserResponse>> =>
    api.post("/auth/register", data),

  login: (data: LoginPayload): Promise<AxiosResponse<TokenResponse>> =>
    api.post("/auth/login", data),

  logout: (): Promise<AxiosResponse<{ message: string }>> =>
    api.post("/auth/logout"),

  refreshToken: (
    refresh_token: string
  ): Promise<AxiosResponse<TokenResponse>> =>
    api.post("/auth/refresh", { refresh_token }),

  me: (): Promise<AxiosResponse<UserResponse>> =>
    api.get("/auth/me"),

  verifyEmail: (token: string): Promise<AxiosResponse<{ message: string }>> =>
    api.get(`/auth/verify-email?token=${token}`),

  forgotPassword: (
    email: string
  ): Promise<AxiosResponse<{ message: string }>> =>
    api.post("/auth/forgot-password", { email }),

  resetPassword: (
    token: string,
    new_password: string,
    confirm_password: string
  ): Promise<AxiosResponse<{ message: string }>> =>
    api.post("/auth/reset-password", { token, new_password, confirm_password }),
};

export default api;
