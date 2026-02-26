"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STATS = [
  { value: "50,000+", label: "Opportunities" },
  { value: "2 Lakh+", label: "Students" },
  { value: "500+", label: "Institutions" },
  { value: "₹10 Cr+", label: "Scholarships" },
];

const TRUST_LOGOS = [
  { name: "IIT Bombay", emoji: "🎓" },
  { name: "IIT Delhi", emoji: "🎓" },
  { name: "IISc", emoji: "🔬" },
  { name: "NIT Trichy", emoji: "🏛" },
  { name: "BITS Pilani", emoji: "🎓" },
  { name: "IIIT Hyderabad", emoji: "💻" },
  { name: "VIT Vellore", emoji: "🏛" },
  { name: "IIM-A", emoji: "📊" },
];

const FEATURES = [
  { icon: "⚡", title: "AI-Powered Feed", desc: "Personalized opportunities ranked by your skills and interests in real time." },
  { icon: "🏆", title: "InCoScore", desc: "Your dynamic credibility score that grows with every achievement you verify." },
  { icon: "💬", title: "Community", desc: "Connect with students from IITs, NITs, and top colleges across India." },
  { icon: "📋", title: "Application Tracker", desc: "Kanban-style board to never miss a deadline again." },
];

const DOMAIN_COLORS: Record<string, string> = {
  ai_ds: "#6366f1", cs: "#3b82f6", ece: "#f59e0b",
  me: "#10b981", management: "#8b5cf6", govt: "#ef4444",
  humanities: "#ec4899", biotech: "#14b8a6", unclassified: "#6b7280",
};

const DOMAIN_LABELS: Record<string, string> = {
  ai_ds: "AI & Data Science", cs: "Computer Science", ece: "Electronics",
  me: "Mechanical", management: "Management", govt: "Government",
  humanities: "Humanities", biotech: "Biotech", unclassified: "Research",
};

interface FeedItem {
  opportunity_id: string;
  title: string;
  institution?: string;
  domain: string;
  deadline?: string;
  source_url?: string;
  application_link?: string;
  description?: string;
  relevance_score: number;
}

function TrendingCard({ item }: { item: FeedItem }) {
  const domainColor = DOMAIN_COLORS[item.domain] ?? "#6b7280";
  const domainLabel = DOMAIN_LABELS[item.domain] ?? item.domain;
  const link = item.application_link || item.source_url;

  const days = item.deadline
    ? Math.ceil((new Date(item.deadline).getTime() - Date.now()) / 86400000)
    : null;

  // Generate a gradient per domain for the card's visual top area
  const gradients: Record<string, string> = {
    ai_ds: "linear-gradient(135deg, #312e81 0%, #1e1b4b 100%)",
    cs: "linear-gradient(135deg, #1e3a8a 0%, #0f1f3d 100%)",
    ece: "linear-gradient(135deg, #78350f 0%, #0f1f3d 100%)",
    me: "linear-gradient(135deg, #064e3b 0%, #0f1f3d 100%)",
    management: "linear-gradient(135deg, #4c1d95 0%, #0f1f3d 100%)",
    govt: "linear-gradient(135deg, #7f1d1d 0%, #0f1f3d 100%)",
    humanities: "linear-gradient(135deg, #831843 0%, #0f1f3d 100%)",
    biotech: "linear-gradient(135deg, #134e4a 0%, #0f1f3d 100%)",
    unclassified: "linear-gradient(135deg, #1f2937 0%, #0f1f3d 100%)",
  };

  return (
    <motion.div
      className="trending-card"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35 }}
      onClick={() => link && window.open(link, "_blank", "noopener,noreferrer")}
    >
      {/* Visual header area */}
      <div style={{
        height: 140,
        background: gradients[item.domain] ?? "linear-gradient(135deg, #1f2937, #0f1f3d)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Decorative circles */}
        <div style={{
          position: "absolute", right: -24, top: -24,
          width: 120, height: 120, borderRadius: "50%",
          background: `${domainColor}22`,
          border: `1px solid ${domainColor}33`,
        }} />
        <div style={{
          position: "absolute", left: -16, bottom: -16,
          width: 80, height: 80, borderRadius: "50%",
          background: `${domainColor}15`,
        }} />

        <span style={{
          fontSize: "3rem",
          filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.4))",
          position: "relative", zIndex: 1,
        }}>
          {item.domain === "ai_ds" ? "🤖" :
            item.domain === "cs" ? "💻" :
              item.domain === "ece" ? "⚡" :
                item.domain === "me" ? "⚙️" :
                  item.domain === "management" ? "📊" :
                    item.domain === "govt" ? "🏛" :
                      item.domain === "humanities" ? "📚" :
                        item.domain === "biotech" ? "🧬" : "🔬"}
        </span>

        {/* Domain pill */}
        <span style={{
          position: "absolute", top: 12, left: 12,
          fontSize: "0.65rem", fontWeight: 700, letterSpacing: "0.06em",
          padding: "3px 10px", borderRadius: "9999px", textTransform: "uppercase",
          background: `${domainColor}30`, color: domainColor, border: `1px solid ${domainColor}50`,
        }}>
          {domainLabel}
        </span>

        {days !== null && days >= 0 && (
          <span style={{
            position: "absolute", top: 12, right: 12,
            fontSize: "0.65rem", fontWeight: 700,
            padding: "3px 10px", borderRadius: "9999px",
            background: days <= 7 ? "rgba(239,68,68,0.25)" : "rgba(255,255,255,0.1)",
            color: days <= 7 ? "#f87171" : "rgba(255,255,255,0.7)",
            border: `1px solid ${days <= 7 ? "rgba(239,68,68,0.4)" : "rgba(255,255,255,0.15)"}`,
          }}>
            {days <= 0 ? "Expired" : `${days}d left`}
          </span>
        )}
      </div>

      <div className="trending-card-body">
        <p className="trending-card-title">{item.title}</p>
        {item.institution && (
          <p className="trending-card-sub">🏛 {item.institution}</p>
        )}
        {!item.institution && item.description && (
          <p className="trending-card-sub" style={{ WebkitLineClamp: 2, display: "-webkit-box", WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {item.description}
          </p>
        )}

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {link ? (
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="trending-card-btn"
              onClick={(e) => e.stopPropagation()}
            >
              View Opportunity ↗
            </a>
          ) : (
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>No link available</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function LandingPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const { data: feedData } = useQuery({
    queryKey: ["landing-trending"],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/api/v1/feed`, { params: { limit: "6" } });
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const trendingItems: FeedItem[] = feedData?.items?.slice(0, 6) ?? [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.push(`/opportunities${searchQuery ? `?q=${encodeURIComponent(searchQuery)}` : ""}`);
  };

  return (
    <div style={{ minHeight: "100vh", overflowX: "hidden" }}>

      {/* ── Sticky Nav ── */}
      <nav style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "0 48px", height: 64,
        position: "sticky", top: 0, zIndex: 50,
        background: "rgba(6,14,30,0.9)", backdropFilter: "blur(16px)",
        borderBottom: "1px solid var(--border)",
      }}>
        <Link href="/" style={{ textDecoration: "none" }}>
          <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: "1.4rem", fontWeight: 900, letterSpacing: "-0.02em" }} className="gradient-text">
            BharatAI
          </span>
        </Link>

        <div style={{ display: "flex", gap: 32, alignItems: "center" }}>
          <Link href="/opportunities" className="nav-link">Browse Opportunities</Link>
          <Link href="/opportunities?domain=ai_ds" className="nav-link">AI & Tech</Link>
          <Link href="/opportunities?domain=govt" className="nav-link">Government</Link>
          <Link href="/opportunities?domain=management" className="nav-link">Management</Link>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Link href="/login" className="btn btn-ghost" style={{ fontSize: "0.875rem" }}>Sign in</Link>
          <Link href="/register" className="btn btn-primary" style={{ fontSize: "0.875rem", padding: "10px 22px" }}>
            Get Started →
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero-fullbleed" style={{ padding: "96px 24px 80px", textAlign: "center", position: "relative", zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 36 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.75 }}
          style={{ position: "relative", zIndex: 2 }}
        >
          {/* Country badge */}
          <motion.span
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "6px 18px", borderRadius: "9999px", marginBottom: 32,
              background: "rgba(255,153,51,0.12)", border: "1px solid rgba(255,153,51,0.3)",
              fontSize: "0.8rem", fontWeight: 600, color: "var(--saffron)",
              letterSpacing: "0.03em",
            }}
          >
            🇮🇳 &nbsp;Built for India&apos;s Students
          </motion.span>

          <h1 style={{
            fontFamily: "Montserrat, sans-serif",
            fontSize: "clamp(2.8rem, 7vw, 5rem)",
            fontWeight: 900,
            lineHeight: 1.05,
            marginBottom: 24,
            letterSpacing: "-0.03em",
          }}>
            Unlock Every<br />
            <span className="gradient-text">Indian Opportunity.</span>
          </h1>

          <p style={{
            fontSize: "1.15rem", color: "var(--text-secondary)",
            maxWidth: 560, margin: "0 auto 48px", lineHeight: 1.75,
          }}>
            Scholarships, internships, fellowships &amp; hackathons — surfaced by AI
            and tailored to your skills and goals.
          </p>

          {/* SEARCH BAR */}
          <form onSubmit={handleSearch} className="hero-search-wrap" style={{ marginBottom: 20 }}>
            <input
              type="text"
              className="hero-search"
              placeholder="🔍  Search scholarships, hackathons, internships…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search opportunities"
            />
            <button type="submit" className="hero-search-btn">
              Search
            </button>
          </form>

          {/* Quick links */}
          <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap", marginTop: 20 }}>
            {[
              { label: "🤖 AI & Data Science", q: "ai_ds", isDomain: true },
              { label: "🏛 Government Schemes", q: "govt", isDomain: true },
              { label: "💰 Scholarships", q: "scholarship", isDomain: false },
              { label: "🏆 Hackathons", q: "hackathon", isDomain: false },
            ].map((tag) => (
              <button
                key={tag.label}
                onClick={() => router.push(
                  tag.isDomain
                    ? `/opportunities?domain=${tag.q}`
                    : `/opportunities?q=${encodeURIComponent(tag.q)}`
                )}
                style={{
                  background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "9999px", padding: "6px 16px",
                  color: "var(--text-secondary)", fontSize: "0.82rem", fontWeight: 500,
                  cursor: "pointer", transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.1)";
                  e.currentTarget.style.color = "var(--text-primary)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }}
              >
                {tag.label}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Floating decorative blobs */}
        <div style={{
          position: "absolute", top: "10%", left: "5%", width: 300, height: 300,
          borderRadius: "50%", background: "radial-gradient(circle, rgba(255,153,51,0.08) 0%, transparent 70%)",
          pointerEvents: "none", zIndex: 0,
        }} />
        <div style={{
          position: "absolute", bottom: "5%", right: "8%", width: 250, height: 250,
          borderRadius: "50%", background: "radial-gradient(circle, rgba(0,191,165,0.08) 0%, transparent 70%)",
          pointerEvents: "none", zIndex: 0,
        }} />
      </section>

      {/* ── Trust / Stats Banner ── */}
      <section className="trust-banner">
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "28px 24px" }}>
          {/* Stats row */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: 24,
            marginBottom: 28,
            textAlign: "center",
          }}>
            {STATS.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
              >
                <p style={{ fontSize: "1.9rem", fontWeight: 900, fontFamily: "Montserrat, sans-serif", color: "var(--saffron)", lineHeight: 1 }}>
                  {s.value}
                </p>
                <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: 4, fontWeight: 500 }}>
                  {s.label}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Divider */}
          <div style={{ borderTop: "1px solid var(--border)", marginBottom: 24 }} />

          {/* Logo chips */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginRight: 8 }}>
              Students from
            </span>
            {TRUST_LOGOS.map((logo) => (
              <span key={logo.name} className="trust-logo">
                {logo.emoji} {logo.name}
              </span>
            ))}
            <span className="trust-logo">+ 490 more</span>
          </div>
        </div>
      </section>

      {/* ── Trending Opportunities ── */}
      <section style={{ padding: "80px 24px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 40, flexWrap: "wrap", gap: 16 }}>
          <div>
            <h2 className="section-heading" style={{ marginBottom: 8 }}>
              Trending <span className="gradient-text">Now</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
              Top opportunities right now — click any card to apply directly
            </p>
          </div>
          <Link href="/opportunities" className="btn btn-secondary" style={{ fontSize: "0.85rem" }}>
            View All Opportunities →
          </Link>
        </div>

        {trendingItems.length === 0 ? (
          /* Skeleton placeholders while loading */
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 24 }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="trending-card" style={{ height: 300, opacity: 0.35, animation: "pulse 1.5s ease infinite" }} />
            ))}
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 24 }}>
            {trendingItems.map((item) => (
              <TrendingCard key={item.opportunity_id} item={item} />
            ))}
          </div>
        )}
      </section>

      {/* ── Features ── */}
      <section style={{ padding: "80px 24px", background: "var(--bg-surface)", borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 56 }}>
            <h2 className="section-heading" style={{ marginBottom: 12 }}>
              Everything you need to <span className="gradient-text">get ahead</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", maxWidth: 500, margin: "0 auto" }}>
              One platform built for every ambitious student in India
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 24 }}>
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                className="glass card"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                style={{ border: "1px solid var(--border)" }}
              >
                <div style={{
                  width: 48, height: 48, borderRadius: 14, marginBottom: 18,
                  background: "linear-gradient(135deg, rgba(255,153,51,0.15), rgba(0,191,165,0.15))",
                  border: "1px solid rgba(255,255,255,0.08)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "1.5rem",
                }}>
                  {f.icon}
                </div>
                <h3 style={{ fontWeight: 700, marginBottom: 10, fontSize: "1rem" }}>{f.title}</h3>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.65 }}>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section style={{ textAlign: "center", padding: "100px 24px", position: "relative", overflow: "hidden" }}>
        {/* Glow bg */}
        <div style={{
          position: "absolute", inset: 0,
          background: "radial-gradient(ellipse 70% 60% at 50% 50%, rgba(255,153,51,0.08) 0%, transparent 65%)",
          pointerEvents: "none",
        }} />

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ position: "relative" }}
        >
          <span style={{
            display: "inline-block", padding: "4px 16px", borderRadius: "9999px",
            background: "rgba(0,191,165,0.12)", border: "1px solid rgba(0,191,165,0.25)",
            color: "var(--emerald)", fontSize: "0.78rem", fontWeight: 700,
            letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 24,
          }}>
            Free Forever
          </span>

          <h2 className="section-heading" style={{ fontSize: "clamp(2rem, 5vw, 3.2rem)", marginBottom: 20 }}>
            Ready to find your next<br />
            <span className="gradient-text">opportunity?</span>
          </h2>

          <p style={{ color: "var(--text-secondary)", marginBottom: 40, fontSize: "1.05rem", maxWidth: 460, margin: "0 auto 40px" }}>
            Join 2 lakh students already on BharatAI. Free forever, no credit card required.
          </p>

          <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/register" className="btn btn-primary" style={{ fontSize: "1rem", padding: "14px 32px" }}>
              Create Free Account →
            </Link>
            <Link href="/opportunities" className="btn btn-secondary" style={{ fontSize: "1rem", padding: "14px 32px" }}>
              Browse Without Login
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ borderTop: "1px solid var(--border)", padding: "40px 48px", background: "var(--bg-surface)" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 24 }}>
          <div>
            <span style={{ fontFamily: "Montserrat, sans-serif", fontSize: "1.2rem", fontWeight: 900 }} className="gradient-text">
              BharatAI
            </span>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 6 }}>
              Built with ❤️ for every Indian student
            </p>
          </div>

          <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
            <Link href="/opportunities" style={{ color: "var(--text-secondary)", fontSize: "0.85rem", textDecoration: "none" }}>Opportunities</Link>
            <Link href="/register" style={{ color: "var(--text-secondary)", fontSize: "0.85rem", textDecoration: "none" }}>Sign Up</Link>
            <Link href="/login" style={{ color: "var(--text-secondary)", fontSize: "0.85rem", textDecoration: "none" }}>Login</Link>
          </div>

          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
            © {new Date().getFullYear()} BharatAI
          </p>
        </div>
      </footer>
    </div>
  );
}
