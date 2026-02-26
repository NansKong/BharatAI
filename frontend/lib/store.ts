import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── Auth slice ───────────────────────────────────────────────
interface AuthUser {
    id: string;
    name: string;
    email: string;
    role: string;
    college?: string;
}

interface AuthState {
    user: AuthUser | null;
    accessToken: string | null;
    login: (user: AuthUser, accessToken: string, refreshToken: string) => void;
    logout: () => void;
    setUser: (user: AuthUser) => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            login: (user, accessToken, refreshToken) => {
                if (typeof window !== "undefined") {
                    localStorage.setItem("access_token", accessToken);
                    localStorage.setItem("refresh_token", refreshToken);
                }
                set({ user, accessToken });
            },
            logout: () => {
                if (typeof window !== "undefined") {
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");
                }
                set({ user: null, accessToken: null });
            },
            setUser: (user) => set({ user }),
        }),
        { name: "bharatai-auth", partialize: (s) => ({ user: s.user, accessToken: s.accessToken }) }
    )
);

// ── Notifications slice ──────────────────────────────────────
interface NotifState {
    unreadCount: number;
    setUnreadCount: (n: number) => void;
    increment: () => void;
    reset: () => void;
}

export const useNotifStore = create<NotifState>()((set) => ({
    unreadCount: 0,
    setUnreadCount: (n) => set({ unreadCount: n }),
    increment: () => set((s) => ({ unreadCount: s.unreadCount + 1 })),
    reset: () => set({ unreadCount: 0 }),
}));
