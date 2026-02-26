"use client";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import axios from "axios";
import { useAuthStore } from "@/lib/store";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
    is_authenticated: boolean;
}

function DeadlineBadge({ deadline }: { deadline?: string }) {
    if (!deadline) return null;
    const days = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000);
    if (days < 0) return <span className="badge badge-red">Expired</span>;
    if (days <= 3) return <span className="badge badge-red">{days}d left 🔥</span>;
    if (days <= 7) return <span className="badge badge-saffron">{days}d left</span>;
    if (days <= 30) return <span className="badge badge-gray">{days}d left</span>;
    return <span className="badge badge-gray">{Math.ceil(days / 30)}mo left</span>;
}

function OpportunityCard({ item, onApply }: { item: FeedItem; onApply: (item: FeedItem) => void }) {
    const [expanded, setExpanded] = useState(false);
    const domainColor = DOMAIN_COLORS[item.domain] ?? "#6b7280";
    const domainLabel = DOMAINS.find((d) => d.code === item.domain)?.label ?? item.domain;
    const applyLink = item.application_link || item.source_url;

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -4, boxShadow: "0 16px 48px rgba(0,0,0,0.25)" }}
            transition={{ duration: 0.22 }}
            className="glass"
            style={{ borderRadius: "var(--radius-lg)", padding: 22, display: "flex", flexDirection: "column", gap: 12 }}
        >
            {/* Top row */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                <span style={{
                    fontSize: "0.68rem", fontWeight: 700, letterSpacing: "0.05em",
                    padding: "3px 10px", borderRadius: "9999px",
                    background: `${domainColor}22`, color: domainColor, border: `1px solid ${domainColor}44`,
                    textTransform: "uppercase",
                }}>
                    {domainLabel}
                </span>
                <DeadlineBadge deadline={item.deadline} />
            </div>

            <h3 style={{ fontWeight: 700, fontSize: "0.96rem", lineHeight: 1.45, margin: 0 }}>{item.title}</h3>

            {item.institution && (
                <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: 0 }}>
                    🏛 {item.institution}
                </p>
            )}

            {item.eligibility && (
                <p style={{
                    fontSize: "0.75rem", color: "var(--text-muted)", margin: 0,
                    background: "var(--bg-elevated)", borderRadius: "var(--radius-md)",
                    padding: "6px 10px", lineHeight: 1.45,
                }}>
                    ✅ {item.eligibility.length > 100 ? item.eligibility.slice(0, 100) + "…" : item.eligibility}
                </p>
            )}

            <AnimatePresence>
                {expanded && item.description && (
                    <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.65, margin: 0 }}
                    >
                        {item.description}
                    </motion.p>
                )}
            </AnimatePresence>

            {item.description && (
                <button
                    onClick={() => setExpanded((e) => !e)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: "0.75rem", padding: 0, textAlign: "left" }}
                >
                    {expanded ? "▲ Show less" : "▼ Read more"}
                </button>
            )}

            {/* Action row */}
            <div style={{ display: "flex", gap: 8, marginTop: "auto", paddingTop: 4 }}>
                {item.source_url && (
                    <a
                        href={item.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-ghost"
                        style={{ flex: 1, justifyContent: "center", fontSize: "0.8rem", border: "1px solid var(--border)" }}
                    >
                        Details ↗
                    </a>
                )}
                {applyLink ? (
                    <a
                        href={applyLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => {
                            // Gate unauthenticated users
                            if (!item.is_authenticated) {
                                e.preventDefault();
                                onApply(item);
                            }
                        }}
                        className="btn btn-primary"
                        style={{ flex: 1, justifyContent: "center", fontSize: "0.8rem" }}
                    >
                        Apply Now
                    </a>
                ) : (
                    <button
                        onClick={() => onApply(item)}
                        className="btn btn-primary"
                        style={{ flex: 1, justifyContent: "center", fontSize: "0.8rem" }}
                    >
                        Apply Now
                    </button>
                )}
            </div>
        </motion.div>
    );
}

function OpportunitiesContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { user, accessToken } = useAuthStore();

    const [domain, setDomain] = useState(searchParams.get("domain") ?? "All");
    const [search, setSearch] = useState(searchParams.get("q") ?? "");

    const isLoggedIn = !!user && !!accessToken;

    // Sync domain from URL param on mount
    useEffect(() => {
        const d = searchParams.get("domain");
        if (d) setDomain(d);
        const q = searchParams.get("q");
        if (q) setSearch(q);
    }, [searchParams]);

    const { data, isLoading, isError } = useQuery({
        queryKey: ["public-feed", domain],
        queryFn: async () => {
            const headers: Record<string, string> = {};
            if (isLoggedIn && accessToken) headers.Authorization = `Bearer ${accessToken}`;
            const params: Record<string, string> = { limit: "60" };
            if (domain !== "All") params.domain = domain;
            const res = await axios.get(`${API_URL}/api/v1/feed`, { headers, params });
            return res.data;
        },
        staleTime: 3 * 60 * 1000,
    });

    const items: FeedItem[] = (data?.items ?? []).filter((item: FeedItem) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return item.title.toLowerCase().includes(q) || (item.institution ?? "").toLowerCase().includes(q);
    });

    const handleApply = (item: FeedItem) => {
        if (!isLoggedIn) {
            router.push(`/login?redirect=/opportunities`);
            return;
        }
        const link = item.application_link || item.source_url;
        if (link) window.open(link, "_blank", "noopener,noreferrer");
    };

    return (
        <div style={{ maxWidth: 1240, margin: "0 auto", padding: "36px 24px" }}>

            {/* ── Page header ── */}
            <div style={{ marginBottom: 32 }}>
                <h1 style={{
                    fontFamily: "Montserrat, sans-serif",
                    fontSize: "clamp(1.6rem, 4vw, 2.2rem)",
                    fontWeight: 900, marginBottom: 8, letterSpacing: "-0.02em",
                }}>
                    🚀 Opportunities for <span className="gradient-text">Indian Students</span>
                </h1>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                    {isLoggedIn
                        ? "Your personalized feed — ranked by AI based on your profile"
                        : "Browse hackathons, internships, research programs & more — free, no login needed"}
                </p>
                {!isLoggedIn && (
                    <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
                        <Link href="/register" className="btn btn-primary" style={{ fontSize: "0.84rem" }}>
                            ✨ Sign up for AI-personalized feed
                        </Link>
                        <Link href="/login" className="btn btn-ghost" style={{ fontSize: "0.84rem", border: "1px solid var(--border)" }}>
                            Already have an account? Log in
                        </Link>
                    </div>
                )}
            </div>

            {/* ── Search ── */}
            <div style={{ position: "relative", marginBottom: 20 }}>
                <span style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)", fontSize: "1rem", pointerEvents: "none" }}>
                    🔍
                </span>
                <input
                    type="text"
                    placeholder="Search by title or institution…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{
                        width: "100%", padding: "13px 16px 13px 44px",
                        borderRadius: "var(--radius-full)",
                        background: "var(--bg-elevated)", border: "1px solid var(--border)",
                        color: "var(--text-primary)", fontSize: "0.9rem",
                        outline: "none", transition: "border-color 0.2s",
                        fontFamily: "inherit",
                    }}
                    onFocus={(e) => e.target.style.borderColor = "var(--border-focus)"}
                    onBlur={(e) => e.target.style.borderColor = "var(--border)"}
                />
            </div>

            {/* ── Domain filter chips ── */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 28 }}>
                {DOMAINS.map((d) => (
                    <button
                        key={d.code}
                        onClick={() => setDomain(d.code)}
                        className={`btn ${domain === d.code ? "btn-primary" : "btn-ghost"}`}
                        style={{
                            fontSize: "0.76rem", padding: "7px 16px",
                            border: domain === d.code ? "none" : "1px solid var(--border)",
                            borderRadius: "var(--radius-full)",
                        }}
                    >
                        {d.label}
                    </button>
                ))}
            </div>

            {/* ── Guest banner ── */}
            {!isLoggedIn && (
                <div style={{
                    marginBottom: 28, padding: "14px 20px", borderRadius: "var(--radius-lg)",
                    background: "linear-gradient(135deg, rgba(0,191,165,0.08), rgba(255,153,51,0.08))",
                    border: "1px solid rgba(0,191,165,0.2)",
                    display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap",
                }}>
                    <p style={{ margin: 0, fontSize: "0.86rem", color: "var(--text-primary)" }}>
                        🔐 <strong>Sign in to apply, and unlock AI-ranked recommendations</strong> tailored to your skills &amp; interests.
                    </p>
                    <Link href="/register" className="btn btn-primary" style={{ fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                        Create Free Account
                    </Link>
                </div>
            )}

            {/* ── Grid ── */}
            {isLoading ? (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 18 }}>
                    {Array.from({ length: 9 }).map((_, i) => (
                        <div key={i} className="glass" style={{ borderRadius: "var(--radius-lg)", height: 240, opacity: 0.35, animation: "pulse 1.5s ease infinite" }} />
                    ))}
                </div>
            ) : isError ? (
                <div style={{ textAlign: "center", padding: "80px 0", color: "var(--text-secondary)" }}>
                    <p style={{ fontSize: "2.5rem", marginBottom: 12 }}>⚠️</p>
                    <p style={{ fontWeight: 600 }}>Could not load opportunities.</p>
                    <p style={{ fontSize: "0.875rem", marginTop: 8 }}>Make sure the backend is running and try again.</p>
                </div>
            ) : items.length === 0 ? (
                <div style={{ textAlign: "center", padding: "80px 0", color: "var(--text-secondary)" }}>
                    <p style={{ fontSize: "2.5rem", marginBottom: 12 }}>🔍</p>
                    <p style={{ fontWeight: 600 }}>No opportunities found.</p>
                    <p style={{ fontSize: "0.875rem", marginTop: 8 }}>Try a different filter or search term.</p>
                </div>
            ) : (
                <>
                    <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 18 }}>
                        {items.length} opportunit{items.length === 1 ? "y" : "ies"} found
                    </p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 18 }}>
                        {items.map((item) => (
                            <OpportunityCard key={item.opportunity_id} item={item} onApply={handleApply} />
                        ))}
                    </div>
                </>
            )}

            {/* ── Footer CTA ── */}
            {!isLoggedIn && items.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    style={{
                        marginTop: 60, textAlign: "center", padding: "48px 24px",
                        borderRadius: "var(--radius-xl)",
                        background: "linear-gradient(135deg, rgba(255,153,51,0.06), rgba(0,191,165,0.06))",
                        border: "1px solid var(--border)",
                    }}
                >
                    <h2 style={{ fontFamily: "Montserrat, sans-serif", fontWeight: 800, fontSize: "1.4rem", marginBottom: 10 }}>
                        Get your AI-personalized feed
                    </h2>
                    <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: "0.9rem" }}>
                        Sign up in 30 seconds — BharatAI learns your skills to surface the most relevant opportunities first.
                    </p>
                    <Link href="/register" className="btn btn-primary" style={{ fontSize: "0.95rem", padding: "13px 32px" }}>
                        Sign Up Free →
                    </Link>
                </motion.div>
            )}
        </div>
    );
}

export default function OpportunitiesPage() {
    return (
        <div style={{ minHeight: "100vh", background: "var(--bg-base)" }}>
            {/* ── Sticky Navbar ── */}
            <nav style={{
                position: "sticky", top: 0, zIndex: 50,
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "0 32px", height: 60,
                background: "rgba(6,14,30,0.92)", borderBottom: "1px solid var(--border)",
                backdropFilter: "blur(14px)",
            }}>
                <Link href="/" style={{ textDecoration: "none" }}>
                    <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: "1.25rem", fontWeight: 900 }} className="gradient-text">
                        BharatAI
                    </span>
                </Link>

                <Suspense fallback={null}>
                    <NavActions />
                </Suspense>
            </nav>

            <Suspense fallback={
                <div style={{ display: "flex", justifyContent: "center", padding: "60px", color: "var(--text-muted)" }}>Loading…</div>
            }>
                <OpportunitiesContent />
            </Suspense>
        </div>
    );
}

function NavActions() {
    const { user, accessToken } = useAuthStore();
    const isLoggedIn = !!user && !!accessToken;
    return (
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            {isLoggedIn ? (
                <>
                    <Link href="/feed" className="btn btn-ghost" style={{ fontSize: "0.82rem" }}>My Feed</Link>
                    <Link href="/profile" className="btn btn-secondary" style={{ fontSize: "0.82rem" }}>
                        {user.name.split(" ")[0]}
                    </Link>
                </>
            ) : (
                <>
                    <Link href="/login" className="btn btn-ghost" style={{ fontSize: "0.82rem" }}>Log In</Link>
                    <Link href="/register" className="btn btn-primary" style={{ fontSize: "0.82rem" }}>Sign Up Free →</Link>
                </>
            )}
        </div>
    );
}
