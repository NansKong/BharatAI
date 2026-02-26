"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { use } from "react";
import { motion } from "framer-motion";
import api from "@/lib/api";

interface Opportunity {
    id: string;
    title: string;
    institution?: string;
    domain: string;
    deadline?: string;
    description?: string;
    eligibility?: string;
    link?: string;
}

export default function OpportunityDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);

    const { data: opp, isLoading } = useQuery<Opportunity>({
        queryKey: ["opportunity", id],
        queryFn: () => api.get(`/opportunities/${id}`).then((r) => r.data),
    });

    const apply = useMutation({
        mutationFn: () => api.post(`/applications`, { opportunity_id: id }),
    });

    if (isLoading) return <div style={{ color: "var(--text-muted)" }}>Loading…</div>;
    if (!opp) return <div style={{ color: "var(--text-muted)" }}>Opportunity not found.</div>;

    const daysLeft = opp.deadline
        ? Math.ceil((new Date(opp.deadline).getTime() - Date.now()) / 86400000)
        : null;

    return (
        <div style={{ maxWidth: 720 }}>
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                {/* Header */}
                <div className="glass card" style={{ marginBottom: 20 }}>
                    <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 14 }}>
                        <span className="badge badge-emerald">{opp.domain}</span>
                        {daysLeft !== null && (
                            <span className={`badge ${daysLeft <= 3 ? "badge-red" : daysLeft <= 7 ? "badge-saffron" : "badge-gray"}`}>
                                {daysLeft <= 0 ? "Deadline passed" : `${daysLeft} days left`}
                            </span>
                        )}
                    </div>
                    <h1 style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: 8, lineHeight: 1.3 }}>{opp.title}</h1>
                    {opp.institution && <p style={{ color: "var(--text-secondary)" }}>🏛 {opp.institution}</p>}
                    {opp.deadline && (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
                            ⏰ Deadline: {new Date(opp.deadline).toLocaleDateString("en-IN", { dateStyle: "long" })}
                        </p>
                    )}
                </div>

                {/* Description */}
                {opp.description && (
                    <div className="glass card" style={{ marginBottom: 16 }}>
                        <h3 style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-secondary)", marginBottom: 10 }}>DESCRIPTION</h3>
                        <p style={{ lineHeight: 1.8, fontSize: "0.95rem" }}>{opp.description}</p>
                    </div>
                )}

                {/* Eligibility */}
                {opp.eligibility && (
                    <div className="glass card" style={{ marginBottom: 16 }}>
                        <h3 style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-secondary)", marginBottom: 10 }}>ELIGIBILITY</h3>
                        <p style={{ lineHeight: 1.8, fontSize: "0.95rem" }}>{opp.eligibility}</p>
                    </div>
                )}

                {/* Actions */}
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    {opp.link && (
                        <a href={opp.link} target="_blank" rel="noreferrer" className="btn btn-secondary">
                            🔗 Official Website
                        </a>
                    )}
                    <button
                        onClick={() => apply.mutate()}
                        className="btn btn-primary"
                        disabled={apply.isPending || apply.isSuccess}
                        style={{ minWidth: 140 }}
                    >
                        {apply.isSuccess ? "✅ Applied!" : apply.isPending ? "Applying…" : "Apply Now →"}
                    </button>
                </div>
                {apply.isError && <p style={{ color: "#ff5050", marginTop: 10, fontSize: "0.85rem" }}>Failed to apply. Please try again.</p>}
            </motion.div>
        </div>
    );
}
