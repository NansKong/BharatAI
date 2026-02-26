"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import api from "@/lib/api";
import { useNotifStore } from "@/lib/store";

interface Notification {
    id: string;
    type: string;
    title: string;
    message: string;
    read: boolean;
    created_at: string;
}

const TYPE_ICONS: Record<string, string> = {
    opportunity_match: "⚡",
    deadline_reminder: "⏰",
    achievement_verified: "🎖️",
    score_change: "📊",
    community_reply: "💬",
    application_update: "📋",
    system: "🔔",
};

export default function NotificationsPage() {
    const qc = useQueryClient();
    const reset = useNotifStore((s) => s.reset);

    const { data: notifs = [], isLoading } = useQuery<Notification[]>({
        queryKey: ["notifications"],
        queryFn: () => api.get("/notifications").then((r) => r.data),
    });

    const markAll = useMutation({
        mutationFn: () => api.post("/notifications/read-all"),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ["notifications"] }); reset(); },
    });

    const markOne = useMutation({
        mutationFn: (id: string) => api.post(`/notifications/${id}/read`),
        onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
    });

    const unread = notifs.filter((n) => !n.read).length;

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Notifications</h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>{unread} unread</p>
                </div>
                {unread > 0 && (
                    <button onClick={() => markAll.mutate()} className="btn btn-secondary" style={{ fontSize: "0.82rem" }}>
                        Mark all read
                    </button>
                )}
            </div>

            {isLoading ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="glass" style={{ borderRadius: "var(--radius-md)", height: 64, opacity: 0.5 }} />
                    ))}
                </div>
            ) : notifs.length === 0 ? (
                <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-secondary)" }}>
                    <p style={{ fontSize: "2.5rem", marginBottom: 12 }}>🔔</p>
                    <p>You&apos;re all caught up!</p>
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {notifs.map((n) => (
                        <motion.div
                            key={n.id}
                            initial={{ opacity: 0, x: -12 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="glass"
                            style={{
                                borderRadius: "var(--radius-md)",
                                padding: "14px 18px",
                                display: "flex",
                                alignItems: "flex-start",
                                gap: 14,
                                cursor: n.read ? "default" : "pointer",
                                borderLeft: n.read ? "3px solid transparent" : "3px solid var(--emerald)",
                                opacity: n.read ? 0.7 : 1,
                            }}
                            onClick={() => { if (!n.read) markOne.mutate(n.id); }}
                        >
                            <span style={{ fontSize: "1.3rem", flexShrink: 0 }}>{TYPE_ICONS[n.type] ?? "🔔"}</span>
                            <div style={{ flex: 1 }}>
                                <p style={{ fontWeight: n.read ? 400 : 600, fontSize: "0.9rem", marginBottom: 2 }}>{n.title}</p>
                                <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{n.message}</p>
                                <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 4 }}>
                                    {new Date(n.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                                </p>
                            </div>
                            {!n.read && <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--emerald)", flexShrink: 0, marginTop: 4 }} />}
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
}
