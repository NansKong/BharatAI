import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: { "Content-Type": "application/json" },
    timeout: 30_000,
});

// ── Request interceptor: attach access token ─────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("access_token");
        if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ── Response interceptor: auto-refresh on 401 ────────────────
let _refreshing: Promise<string> | null = null;

api.interceptors.response.use(
    (res) => res,
    async (error: AxiosError) => {
        const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        if (error.response?.status !== 401 || original._retry) {
            return Promise.reject(error);
        }
        original._retry = true;

        try {
            if (!_refreshing) {
                const refresh_token = typeof window !== "undefined"
                    ? localStorage.getItem("refresh_token")
                    : null;

                _refreshing = axios
                    .post(`${API_URL}/api/v1/auth/refresh`, { refresh_token })
                    .then((r) => {
                        const { access_token, refresh_token: newRefresh } = r.data;
                        localStorage.setItem("access_token", access_token);
                        if (newRefresh) localStorage.setItem("refresh_token", newRefresh);
                        return access_token;
                    })
                    .finally(() => { _refreshing = null; });
            }

            const newToken = await _refreshing;
            original.headers.Authorization = `Bearer ${newToken}`;
            return api(original);
        } catch {
            // Refresh failed → clear tokens
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            window.location.href = "/login";
            return Promise.reject(error);
        }
    }
);

export default api;
