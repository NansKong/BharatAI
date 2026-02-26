"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import api from "@/lib/api";

const ACH_TYPES = ["hackathon", "internship", "publication", "competition", "certification", "coding", "community"];
const STATUS_COLOR: Record<string, string> = {
    pending: "badge-saffron", approved: "badge-emerald", rejected: "badge-red",
};

interface Achievement { id: string; type: string; title: string; description: string; status: string; created_at: string; }
interface AchievementForm { type: string; title: string; description: string; proof_url: string; }

export default function AchievementsPage() {
    const qc = useQueryClient();
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState<AchievementForm>({ type: "", title: "", description: "", proof_url: "" });
    const [formErr, setFormErr] = useState("");

    const { data: achievements = [], isLoading } = useQuery<Achievement[]>({
        queryKey: ["achievements"],
        queryFn: () => api.get("/community/achievements").then((r) => r.data.items ?? r.data),
    });

    const submit = useMutation({
        mutationFn: (body: AchievementForm) => api.post("/community/achievements", body),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["achievements"] });
            setShowForm(false);
            setForm({ type: "", title: "", description: "", proof_url: "" });
        },
    });

    const handleSubmitForm = () => {
        if (!form.type) { setFormErr("Select a type"); return; }
        if (form.title.length < 3) { setFormErr("Title must be at least 3 characters"); return; }
        if (form.description.length < 10) { setFormErr("Description must be at least 10 characters"); return; }
        setFormErr("");
        submit.mutate(form);
    };

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Achievements</h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>Submit and track verified achievements</p>
                </div>
                <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
                    + Submit Achievement
                </button>
            </div>

            {showForm && (
                <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} className="glass card" style={{ marginBottom: 24 }}>
                    <h3 style={{ fontWeight: 700, marginBottom: 16 }}>New Achievement</h3>
                    <div style={{ display: "grid", gap: 12 }}>
                        <select value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))} className="input">
                            <option value="">Select type…</option>
                            {ACH_TYPES.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                        </select>
                        <input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="Achievement title" className="input" />
                        <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Describe your achievement…" className="input" style={{ minHeight: 80, resize: "vertical" }} />
                        <input value={form.proof_url} onChange={(e) => setForm((f) => ({ ...f, proof_url: e.target.value }))} placeholder="Proof URL (optional)" className="input" />
                        {formErr && <p style={{ color: "#ff5050", fontSize: "0.75rem" }}>{formErr}</p>}
                        <button onClick={handleSubmitForm} className="btn btn-primary" disabled={submit.isPending}>
                            {submit.isPending ? "Submitting…" : "Submit"}
                        </button>
                    </div>
                </motion.div>
            )}

            {isLoading ? (
                <p style={{ color: "var(--text-muted)" }}>Loading…</p>
            ) : achievements.length === 0 ? (
                <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-secondary)" }}>
                    <p style={{ fontSize: "2.5rem", marginBottom: 12 }}>🎖️</p>
                    <p>No achievements yet. Submit your first one!</p>
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {achievements.map((a) => (
                        <motion.div key={a.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass card" style={{ padding: "16px 20px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <div>
                                    <p style={{ fontWeight: 700, marginBottom: 2 }}>{a.title}</p>
                                    <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{a.description}</p>
                                </div>
                                <span className={`badge ${STATUS_COLOR[a.status] ?? "badge-gray"}`}>{a.status}</span>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
}
