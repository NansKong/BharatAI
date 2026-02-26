"use client";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import api from "@/lib/api";

interface Application {
    id: string;
    status: string;
    opportunity_id: string;
    opportunity_title?: string;
    created_at: string;
}

const COLUMNS = [
    { key: "draft", label: "Draft", color: "var(--text-muted)" },
    { key: "submitted", label: "Submitted", color: "#6383ff" },
    { key: "accepted", label: "Accepted", color: "var(--emerald)" },
    { key: "rejected", label: "Rejected", color: "#ff5050" },
];

function KanbanCard({ app }: { app: Application }) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass"
            style={{ borderRadius: "var(--radius-md)", padding: "14px", marginBottom: 8 }}
        >
            <p style={{ fontWeight: 600, fontSize: "0.88rem", marginBottom: 4, lineHeight: 1.4 }}>
                {app.opportunity_title ?? `Opportunity ${app.opportunity_id.slice(0, 8)}`}
            </p>
            <p style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                {new Date(app.created_at).toLocaleDateString("en-IN")}
            </p>
        </motion.div>
    );
}

export default function ApplicationsPage() {
    const { data = [], isLoading } = useQuery<Application[]>({
        queryKey: ["applications"],
        queryFn: () => api.get("/applications").then((r) => r.data.items ?? r.data),
    });

    const grouped = COLUMNS.map(({ key, label, color }) => ({
        key, label, color,
        items: data.filter((a) => a.status === key),
    }));

    return (
        <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 6 }}>Applications</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: 24 }}>Track your application pipeline</p>

            {isLoading ? (
                <p style={{ color: "var(--text-muted)" }}>Loading…</p>
            ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, alignItems: "start" }}>
                    {grouped.map(({ key, label, color, items }) => (
                        <div key={key}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                                <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block" }} />
                                <span style={{ fontWeight: 700, fontSize: "0.85rem", color }}>{label}</span>
                                <span className="badge badge-gray" style={{ marginLeft: "auto" }}>{items.length}</span>
                            </div>
                            {items.length === 0 ? (
                                <div className="glass" style={{ borderRadius: "var(--radius-md)", padding: "20px", textAlign: "center", opacity: 0.5, fontSize: "0.8rem", color: "var(--text-muted)" }}>
                                    Empty
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
