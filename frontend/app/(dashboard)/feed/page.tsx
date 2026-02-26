"use client";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useRef, useCallback } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

const DOMAINS = [
    { code: "All", label: "All" },
    { code: "ai_ds", label: "AI & Data Science" },
    { code: "cs", label: "Computer Science" },
    { code: "ece", label: "Electronics" },
    { code: "me", label: "Mechanical" },
    { code: "management", label: "Management" },
    { code: "govt", label: "Government" },
    { code: "humanities", label: "Humanities" },
    { code: "biotech", label: "Biotech" },
    { code: "unclassified", label: "Research" },
];

const DOMAIN_COLORS: Record<string, string> = {
    ai_ds: "#6366f1", cs: "#3b82f6", ece: "#f59e0b",
    me: "#10b981", management: "#8b5cf6", govt: "#ef4444",
    humanities: "#ec4899", biotech: "#14b8a6", unclassified: "#6b7280",
};

const POLL_INTERVAL_MS = 60_000; // 60 s auto-refresh

interface FeedItem {
    opportunity_id: string;
    title: string;
    institution?: string;
    domain: string;
    deadline?: string;
    source_url?: string;
    application_link?: string;
    eligibility?: string;
    description?: string;
    relevance_score: number;
}

function DeadlineBadge({ deadline }: { deadline?: string }) {
    if (!deadline) return null;
    const days = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000);
    if (days < 0) return <span className="badge badge-red">Expired</span>;
    if (days <= 3) return <span className="badge badge-red">{days}d left 🔥</span>;
    if (days <= 7) return <span className="badge badge-saffron">{days}d left</span>;
    return <span className="badge badge-gray">{days}d left</span>;
}

function OpportunityCard({ item, isNew }: { item: FeedItem; isNew?: boolean }) {
    const [expanded, setExpanded] = useState(false);
    const domainColor = DOMAIN_COLORS[item.domain] ?? "#6b7280";
    const domainLabel = DOMAINS.find((d) => d.code === item.domain)?.label ?? item.domain;

    const handleApply = () => {
        const link = item.application_link || item.source_url;
        if (link) window.open(link, "_blank", "noopener,noreferrer");
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -4 }}
            className="glass"
            style={{
                borderRadius: "var(--radius-lg)", padding: 20,
                display: "flex", flexDirection: "column", gap: 10,
                ...(isNew && {
                    boxShadow: "0 0 0 2px var(--emerald), 0 4px 24px rgba(0,191,165,0.18)",
                }),
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                    <span style={{
                        fontSize: "0.68rem", fontWeight: 700, padding: "3px 10px",
                        borderRadius: "var(--radius-full)", textTransform: "uppercase",
                        background: `${domainColor}22`, color: domainColor, border: `1px solid ${domainColor}44`,
                    }}>{domainLabel}</span>
                    {isNew && (
                        <span style={{
                            fontSize: "0.6rem", fontWeight: 800, padding: "2px 7px",
                            borderRadius: "var(--radius-full)", textTransform: "uppercase",
                            background: "rgba(0,191,165,0.15)", color: "var(--emerald)",
                            border: "1px solid rgba(0,191,165,0.3)",
                        }}>NEW</span>
                    )}
                </div>
                <DeadlineBadge deadline={item.deadline} />
            </div>

            <h3 style={{ fontWeight: 700, fontSize: "0.93rem", lineHeight: 1.4, margin: 0 }}>{item.title}</h3>

            {item.institution && (
                <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", margin: 0 }}>🏛 {item.institution}</p>
            )}

            {item.eligibility && (
                <p style={{ fontSize: "0.73rem", color: "var(--text-muted)", background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)", padding: "5px 8px", margin: 0, lineHeight: 1.4 }}>
                    ✅ {item.eligibility.length > 90 ? item.eligibility.slice(0, 90) + "…" : item.eligibility}
                </p>
            )}

            {/* Relevance bar */}
            {item.relevance_score > 0 && (
                <div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 3 }}>
                        <span>Relevance</span>
                        <span>{Math.round(item.relevance_score * 100)}%</span>
                    </div>
                    <div style={{ background: "var(--bg-base)", borderRadius: "var(--radius-full)", height: 4, overflow: "hidden" }}>
                        <div style={{ width: `${item.relevance_score * 100}%`, height: "100%", background: "linear-gradient(90deg, var(--emerald), var(--saffron))", borderRadius: "var(--radius-full)" }} />
                    </div>
                </div>
            )}

            {/* Expandable description */}
            <AnimatePresence>
                {expanded && item.description && (
                    <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}
                    >{item.description}</motion.p>
                )}
            </AnimatePresence>

            {item.description && (
                <button onClick={() => setExpanded(e => !e)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: "0.72rem", padding: 0, textAlign: "left" }}>
                    {expanded ? "▲ Show less" : "▼ Read more"}
                </button>
            )}

            {/* Actions */}
            <div style={{ display: "flex", gap: 8, marginTop: "auto" }}>
                {item.source_url && (
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer"
                        className="btn btn-ghost"
                        style={{ flex: 1, justifyContent: "center", fontSize: "0.78rem", border: "1px solid var(--border)" }}>
                        Details ↗
                    </a>
                )}
                <button onClick={handleApply} className="btn btn-primary"
                    style={{ flex: 1, justifyContent: "center", fontSize: "0.78rem" }}>
                    Apply Now
                </button>
            </div>
        </motion.div>
    );
}

// ── Live update toast ────────────────────────────────────────────────────────
function LiveToast({ count, onLoad }: { count: number; onLoad: () => void }) {
    return (
        <AnimatePresence>
            {count > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 60 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 60 }}
                    style={{
                        position: "fixed", bottom: 28, left: "50%", transform: "translateX(-50%)",
                        zIndex: 100,
                        background: "linear-gradient(135deg, rgba(0,191,165,0.95), rgba(0,152,121,0.95))",
                        color: "#fff", borderRadius: "var(--radius-full)",
                        padding: "10px 22px", fontSize: "0.85rem", fontWeight: 700,
                        boxShadow: "0 8px 32px rgba(0,191,165,0.4)",
                        display: "flex", alignItems: "center", gap: 10, cursor: "pointer",
                        backdropFilter: "blur(12px)",
                    }}
                    onClick={onLoad}
                >
                    <span style={{ fontSize: "1rem" }}>⚡</span>
                    {count} new opportunit{count === 1 ? "y" : "ies"} — click to refresh
                    <span style={{
                        background: "rgba(255,255,255,0.25)", borderRadius: "var(--radius-full)",
                        padding: "2px 8px", fontSize: "0.7rem",
                    }}>×</span>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

// ── Last-updated ticker ──────────────────────────────────────────────────────
function LastUpdated({ updatedAt }: { updatedAt: Date | null }) {
    const [label, setLabel] = useState("Just now");

    useEffect(() => {
        if (!updatedAt) return;
        const update = () => {
            const s = Math.floor((Date.now() - updatedAt.getTime()) / 1000);
            if (s < 5) setLabel("Just now");
            else if (s < 60) setLabel(`${s}s ago`);
            else setLabel(`${Math.floor(s / 60)}m ago`);
        };
        update();
        const t = setInterval(update, 10_000);
        return () => clearInterval(t);
    }, [updatedAt]);

    return (
        <span style={{
            display: "inline-flex", alignItems: "center", gap: 5,
            fontSize: "0.7rem", color: "var(--text-muted)",
        }}>
            <span style={{
                width: 7, height: 7, borderRadius: "50%",
                background: "var(--emerald)",
                boxShadow: "0 0 0 2px rgba(0,191,165,0.3)",
                animation: "pulse 2s ease infinite",
                display: "inline-block",
            }} />
            Updated {label}
        </span>
    );
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function FeedPage() {
    const [domain, setDomain] = useState("All");
    const [search, setSearch] = useState("");
    const { user } = useAuthStore();
    const prevIdsRef = useRef<Set<string>>(new Set());
    const [newIds, setNewIds] = useState<Set<string>>(new Set());
    const [pendingCount, setPendingCount] = useState(0);
    const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

    const fetchFeed = useCallback(() => {
        const params: Record<string, string> = { limit: "50" };
        if (domain !== "All") params.domain = domain;
        return api.get("/feed", { params }).then(r => r.data);
    }, [domain]);

    const { data, isLoading, refetch } = useQuery({
        queryKey: ["feed", domain],
        queryFn: fetchFeed,
        // Background refetch every 60s
        refetchInterval: POLL_INTERVAL_MS,
        refetchIntervalInBackground: false,
    });

    // Detect new items on each refetch
    useEffect(() => {
        if (!data?.items) return;
        const currentIds = new Set<string>(data.items.map((i: FeedItem) => i.opportunity_id));

        if (prevIdsRef.current.size === 0) {
            // First load — no toast
            prevIdsRef.current = currentIds;
            setUpdatedAt(new Date());
            return;
        }

        const fresh = new Set<string>();
        for (const id of currentIds) {
            if (!prevIdsRef.current.has(id)) fresh.add(id);
        }

        if (fresh.size > 0) {
            // Background update — show toast instead of immediately updating cards
            setPendingCount(prev => prev + fresh.size);
            setNewIds(prev => new Set([...prev, ...fresh]));
        } else {
            setUpdatedAt(new Date());
        }
        prevIdsRef.current = currentIds;
    }, [data]);

    const handleLoadNew = () => {
        setPendingCount(0);
        setUpdatedAt(new Date());
        // Auto-hide new highlight after 8s
        setTimeout(() => setNewIds(new Set()), 8_000);
    };

    const isColdStart = data?.cold_start ?? false;
    const items: FeedItem[] = (data?.items ?? []).filter((item: FeedItem) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return item.title.toLowerCase().includes(q) || (item.institution ?? "").toLowerCase().includes(q);
    });

    return (
        <div>
            {/* Header */}
            <div style={{ marginBottom: 24 }}>
                <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                    <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 4 }}>
                        {isColdStart ? "Explore Opportunities" : `Welcome back, ${user?.name?.split(" ")[0] ?? ""}! 👋`}
                    </h1>
                    <LastUpdated updatedAt={updatedAt} />
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                    {isColdStart
                        ? "Complete your profile to get AI-personalized recommendations"
                        : "Your AI-ranked feed — opportunities matched to your skills & interests · Auto-refreshes every 60s"}
                </p>
                {isColdStart && (
                    <a href="/profile" className="btn btn-secondary" style={{ fontSize: "0.8rem", marginTop: 10, display: "inline-flex" }}>
                        ✏️ Update profile for better recommendations
                    </a>
                )}
            </div>

            {/* Search */}
            <div style={{ marginBottom: 16 }}>
                <input type="text" placeholder="🔍 Search by title or institution…"
                    value={search} onChange={e => setSearch(e.target.value)}
                    style={{
                        width: "100%", padding: "9px 14px", borderRadius: "var(--radius-md)",
                        background: "var(--bg-elevated)", border: "1px solid var(--border)",
                        color: "var(--text-primary)", fontSize: "0.86rem", outline: "none",
                    }} />
            </div>

            {/* Domain filters */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
                {DOMAINS.map((d) => (
                    <button key={d.code} onClick={() => setDomain(d.code)}
                        className={`btn ${domain === d.code ? "btn-primary" : "btn-ghost"}`}
                        style={{ fontSize: "0.76rem", padding: "6px 14px", border: domain === d.code ? "" : "1px solid var(--border)" }}>
                        {d.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            {isLoading ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
                    {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="glass" style={{ borderRadius: "var(--radius-lg)", height: 200, opacity: 0.4, animation: "pulse 1.5s ease infinite" }} />
                    ))}
                </div>
            ) : items.length === 0 ? (
                <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-secondary)" }}>
                    <p style={{ fontSize: "2rem", marginBottom: 12 }}>🔍</p>
                    <p>No opportunities found. Try a different filter or search.</p>
                </div>
            ) : (
                <>
                    <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: 14 }}>
                        {items.length} opportunit{items.length === 1 ? "y" : "ies"}
                    </p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
                        {items.map(item => (
                            <OpportunityCard
                                key={item.opportunity_id}
                                item={item}
                                isNew={newIds.has(item.opportunity_id)}
                            />
                        ))}
                    </div>
                </>
            )}

            {/* Live update toast */}
            <LiveToast count={pendingCount} onLoad={handleLoadNew} />
        </div>
    );
}
