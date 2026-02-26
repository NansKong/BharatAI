"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import api from "@/lib/api";

interface Source { id: string; name: string; url: string; is_active: boolean; }
interface Flag { id: string; reason: string; status: string; }

export default function AdminPage() {
    const sources = useQuery<Source[]>({ queryKey: ["admin-sources"], queryFn: () => api.get("/admin/sources").then((r) => r.data.items ?? r.data) });
    const flags = useQuery<Flag[]>({ queryKey: ["admin-flags"], queryFn: () => api.get("/admin/flags").then((r) => r.data.items ?? r.data) });

    const scrape = useMutation({ mutationFn: () => api.post("/admin/scrape/trigger") });

    return (
        <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 6 }}>Admin Dashboard</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: 28 }}>System management controls</p>

            {/* Scrape trigger */}
            <div className="glass card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontWeight: 700, marginBottom: 12 }}>🕷 Scraper Controls</h3>
                <button onClick={() => scrape.mutate()} className="btn btn-primary" disabled={scrape.isPending}>
                    {scrape.isPending ? "Triggering…" : "Trigger Scrape Now"}
                </button>
                {scrape.isSuccess && <p style={{ marginTop: 10, color: "var(--emerald)", fontSize: "0.85rem" }}>✅ Scrape triggered successfully</p>}
            </div>

            {/* Sources */}
            <div className="glass card" style={{ marginBottom: 24 }}>
                <h3 style={{ fontWeight: 700, marginBottom: 12 }}>📡 Sources</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {(sources.data ?? []).map((s) => (
                        <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                            <div>
                                <p style={{ fontWeight: 600, fontSize: "0.88rem" }}>{s.name}</p>
                                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{s.url}</p>
                            </div>
                            <span className={`badge ${s.is_active ? "badge-emerald" : "badge-gray"}`}>{s.is_active ? "Active" : "Inactive"}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Flags / Moderation */}
            <div className="glass card">
                <h3 style={{ fontWeight: 700, marginBottom: 12 }}>🚩 Moderation Queue</h3>
                {(flags.data ?? []).length === 0 ? (
                    <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No pending flags.</p>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        {(flags.data ?? []).map((f) => (
                            <motion.div key={f.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                style={{ padding: "10px 0", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
                                <p style={{ fontSize: "0.88rem" }}>{f.reason}</p>
                                <span className={`badge ${f.status === "pending" ? "badge-saffron" : "badge-gray"}`}>{f.status}</span>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
