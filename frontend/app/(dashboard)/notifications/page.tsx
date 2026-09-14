"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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

const TYPE_STICKERS: Record<string, { label: string; color: string }> = {
  opportunity_match: { label: "OPPORTUNITY MATCH", color: "sticker-yellow" },
  deadline_reminder: { label: "DEADLINE ALERT", color: "sticker-pink" },
  achievement_verified: { label: "ACHIEVEMENT VERIFIED", color: "sticker-teal" },
  score_change: { label: "INCOSCORE UPDATE", color: "sticker-blue" },
  community_reply: { label: "COMMUNITY REPLY", color: "sticker-green" },
  application_update: { label: "APPLICATION UPDATE", color: "sticker-yellow" },
  system: { label: "SYSTEM NOTICE", color: "sticker-blue" },
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
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      reset();
    },
  });

  const markOne = useMutation({
    mutationFn: (id: string) => api.post(`/notifications/${id}/read`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const unread = notifs.filter((n) => !n.read).length;

  return (
    <div style={{ maxWidth: 880, margin: "0 auto", padding: "36px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            NOTIFICATION FEED
          </span>
          <span className="sticker-badge sticker-blue" style={{ transform: "rotate(1deg)" }}>
            {unread} UNREAD
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 className="font-serif-headline" style={{ fontSize: "clamp(2.4rem, 5vw, 3.8rem)", lineHeight: 1.05, fontWeight: 400 }}>
              Recent updates.
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginTop: "4px" }}>
              Alerts on matched opportunities, application updates, and community activity.
            </p>
          </div>

          {unread > 0 && (
            <button
              type="button"
              onClick={() => markAll.mutate()}
              className="btn-hard-primary"
            >
              MARK ALL AS READ ↗
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div style={{ padding: "48px", textAlign: "center", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
          LOADING NOTIFICATIONS...
        </div>
      ) : notifs.length === 0 ? (
        <div className="field-card" style={{ backgroundColor: "#FFFFFF", textAlign: "center", padding: "64px" }}>
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.9rem", color: "var(--text-muted)" }}>
            YOU&apos;RE ALL CAUGHT UP! NO UNREAD NOTIFICATIONS.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {notifs.map((n) => {
            const sticker = TYPE_STICKERS[n.type] ?? { label: "NOTIFICATION", color: "sticker-yellow" };
            return (
              <div
                key={n.id}
                className="field-card"
                style={{
                  backgroundColor: n.read ? "#F7F4EE" : "#FFFFFF",
                  cursor: n.read ? "default" : "pointer",
                  opacity: n.read ? 0.8 : 1,
                }}
                onClick={() => {
                  if (!n.read) markOne.mutate(n.id);
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                  <span className={`sticker-badge ${sticker.color}`} style={{ fontSize: "0.65rem" }}>
                    {sticker.label}
                  </span>
                  <span style={{ fontSize: "0.72rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
                    {new Date(n.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                  </span>
                </div>

                <h4 style={{ fontSize: "1rem", fontWeight: n.read ? 700 : 900, color: "#0F0F11", marginBottom: "4px" }}>
                  {n.title}
                </h4>
                <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>
                  {n.message}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
