"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

interface Application {
  id: string;
  status: string;
  opportunity_id: string;
  opportunity_title?: string;
  created_at: string;
}

const COLUMNS = [
  { key: "draft", label: "DRAFT PIPELINE", sticker: "sticker-yellow" },
  { key: "submitted", label: "SUBMITTED", sticker: "sticker-blue" },
  { key: "accepted", label: "ACCEPTED", sticker: "sticker-teal" },
  { key: "rejected", label: "REJECTED", sticker: "sticker-pink" },
];

function KanbanCard({ app }: { app: Application }) {
  return (
    <div
      className="field-card"
      style={{
        backgroundColor: "#FFFFFF",
        padding: "16px",
        marginBottom: "12px",
      }}
    >
      <p style={{ fontWeight: 800, fontSize: "0.9rem", marginBottom: "6px", lineHeight: 1.35, color: "#0F0F11" }}>
        {app.opportunity_title ?? `Opportunity ${app.opportunity_id.slice(0, 8)}`}
      </p>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "8px", borderTop: "var(--border-hard)" }}>
        <span style={{ fontSize: "0.7rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
          {new Date(app.created_at).toLocaleDateString("en-IN")}
        </span>
        <span style={{ fontSize: "0.68rem", fontFamily: "'JetBrains Mono', monospace", fontWeight: 800 }}>
          LOGGED
        </span>
      </div>
    </div>
  );
}

export default function ApplicationsPage() {
  const { data = [], isLoading } = useQuery<Application[]>({
    queryKey: ["applications"],
    queryFn: () => api.get("/applications").then((r) => r.data.items ?? r.data),
  });

  const grouped = COLUMNS.map(({ key, label, sticker }) => ({
    key,
    label,
    sticker,
    items: data.filter((a) => a.status === key),
  }));

  return (
    <div style={{ maxWidth: 1240, margin: "0 auto", padding: "36px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            APPLICATION TRACKER
          </span>
          <span className="sticker-badge sticker-pink" style={{ transform: "rotate(1deg)" }}>
            KANBAN BOARD
          </span>
        </div>

        <h1 className="font-serif-headline" style={{ fontSize: "clamp(2.4rem, 5vw, 4rem)", lineHeight: 1.05, fontWeight: 400, marginBottom: "8px" }}>
          Application tracking board.
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Track the real-time status of your academic opportunity applications across Indian institutions.
        </p>
      </div>

      {isLoading ? (
        <div style={{ padding: "48px", textAlign: "center", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
          LOADING APPLICATION PIPELINE...
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "20px", alignItems: "start" }}>
          {grouped.map(({ key, label, sticker, items }) => (
            <div key={key} className="field-card" style={{ backgroundColor: "#F7F4EE", padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                <span className={`sticker-badge ${sticker}`} style={{ fontSize: "0.7rem" }}>
                  {label}
                </span>
                <div className="num-circle" style={{ backgroundColor: "#0F0F11", color: "#FFFFFF", width: 26, height: 26, fontSize: "0.72rem" }}>
                  {items.length}
                </div>
              </div>

              {items.length === 0 ? (
                <div
                  style={{
                    border: "2px dashed #0F0F11",
                    borderRadius: "var(--radius-box)",
                    padding: "24px 16px",
                    textAlign: "center",
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                    backgroundColor: "#FFFFFF",
                  }}
                >
                  NO APPLICATIONS IN THIS STAGE
                </div>
              ) : (
                items.map((app) => <KanbanCard key={app.id} app={app} />)
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
