"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
import api from "@/lib/api";

interface Score {
    total_score: number;
    domain?: string;
    components: Record<string, number>;
    computed_at: string;
}

interface LeaderboardEntry {
    rank: number;
    user_id: string;
    name: string;
    college?: string;
    total_score: number;
    domain?: string;
}

const TABS = ["Overall", "Domain", "College"] as const;
type Tab = (typeof TABS)[number];
const DOMAINS = ["ai_ds", "cs", "management", "research", "engineering", "social"];

function ScoreBadge({ score }: { score: number }) {
    const pct = (score / 1000) * 100;
    const color = score >= 700 ? "var(--saffron)" : score >= 400 ? "var(--emerald)" : "#6383ff";
    return (
        <div style={{ position: "relative", width: 80, height: 80 }}>
            <svg viewBox="0 0 80 80" style={{ position: "absolute", inset: 0, transform: "rotate(-90deg)" }}>
                <circle cx="40" cy="40" r="32" fill="none" stroke="var(--bg-surface)" strokeWidth="6" />
                <circle cx="40" cy="40" r="32" fill="none" stroke={color} strokeWidth="6"
                    strokeDasharray={`${2 * Math.PI * 32}`}
                    strokeDashoffset={`${2 * Math.PI * 32 * (1 - pct / 100)}`}
                    strokeLinecap="round"
                />
            </svg>
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
                <span style={{ fontSize: "1rem", fontWeight: 800, color }}>{Math.round(score)}</span>
                <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>/ 1000</span>
            </div>
        </div>
    );
}

export default function LeaderboardPage() {
    const [tab, setTab] = useState<Tab>("Overall");
    const [domain, setDomain] = useState(DOMAINS[0]);

    const myScore = useQuery<Score>({ queryKey: ["my-score"], queryFn: () => api.get("/incoscore/me").then((r) => r.data) });

    const boardQuery = useQuery<LeaderboardEntry[]>({
        queryKey: ["leaderboard", tab, domain],
        queryFn: () => {
            const url = tab === "Domain"
                ? `/incoscore/leaderboard/domain?domain=${domain}&limit=25`
                : tab === "College"
                    ? `/incoscore/leaderboard/college?limit=25`
                    : `/incoscore/leaderboard?limit=25`;
            return api.get(url).then((r) => r.data.entries ?? r.data);
        },
    });

    return (
        <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 6 }}>Leaderboard</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: 24 }}>InCoScore rankings across India</p>

            {/* My Score Card */}
            {myScore.data && (
                <div className="glass card" style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 28, borderLeft: "3px solid var(--saffron)" }}>
                    <ScoreBadge score={myScore.data.total_score} />
                    <div>
                        <p style={{ fontWeight: 700, fontSize: "1.05rem" }}>Your InCoScore</p>
                        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                            Last updated: {new Date(myScore.data.computed_at).toLocaleDateString("en-IN")}
                        </p>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
                {TABS.map((t) => (
                    <button key={t} onClick={() => setTab(t)} className={`btn ${tab === t ? "btn-primary" : "btn-ghost"}`} style={{ fontSize: "0.82rem", padding: "7px 16px", border: tab !== t ? "1px solid var(--border)" : "" }}>
                        {t}
                    </button>
                ))}
            </div>

            {tab === "Domain" && (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
                    {DOMAINS.map((d) => (
                        <button key={d} onClick={() => setDomain(d)} className={`btn ${domain === d ? "btn-secondary" : "btn-ghost"}`} style={{ fontSize: "0.75rem", padding: "5px 12px", border: "1px solid var(--border)" }}>
                            {d}
                        </button>
                    ))}
                </div>
            )}

            {/* Board */}
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {(boardQuery.data ?? []).map((entry, i) => (
                    <motion.div key={entry.user_id} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}
                        className="glass"
                        style={{ borderRadius: "var(--radius-md)", padding: "14px 18px", display: "flex", alignItems: "center", gap: 16 }}
                    >
                        <span style={{ width: 28, textAlign: "center", fontWeight: 700, color: i < 3 ? "var(--saffron)" : "var(--text-muted)", fontSize: i < 3 ? "1.1rem" : "0.9rem" }}>
                            {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : i + 1}
                        </span>
                        <div style={{ flex: 1 }}>
                            <p style={{ fontWeight: 600, fontSize: "0.9rem" }}>{entry.name}</p>
                            {entry.college && <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{entry.college}</p>}
                        </div>
                        <span style={{ fontWeight: 800, fontSize: "1.1rem", color: "var(--saffron)" }}>{Math.round(entry.total_score)}</span>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
