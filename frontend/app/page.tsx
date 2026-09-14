"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Search, ArrowUpRight, ArrowDownRight, Building2, Calendar, Sparkles } from "lucide-react";
import { TopNav } from "@/components/layout/Sidebar";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DOMAIN_LABELS: Record<string, string> = {
  ai_ds: "AI & Data Science",
  cs: "Computer Science",
  ece: "Electronics",
  me: "Mechanical",
  management: "Management",
  govt_policy: "Government & Policy",
  govt: "Government & Policy",
  humanities: "Humanities",
  biotech: "Biotechnology",
  unclassified: "Research",
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

export default function LandingPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeDomain, setActiveDomain] = useState<string>("all");

  const { data: feedData, isLoading } = useQuery({
    queryKey: ["field-opportunities", activeDomain],
    queryFn: async () => {
      const params: Record<string, string> = { limit: "6" };
      if (activeDomain !== "all") {
        params.domain = activeDomain;
      }
      const res = await axios.get(`${API_URL}/api/v1/feed`, { params });
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const opportunities: FeedItem[] = feedData?.items ?? [];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/opportunities?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-base)", color: "var(--text-main)" }}>
      <TopNav />

      {/* ── Main Hero Section ── */}
      <main style={{ maxWidth: "1240px", margin: "0 auto", padding: "64px 40px" }}>
        {/* Tilted Sticker Badges */}
        <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "28px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            ACADEMIC OPPORTUNITY INDEX
          </span>
          <span className="sticker-badge sticker-blue" style={{ transform: "rotate(1.5deg)" }}>
            INDIA / NATIONWIDE
          </span>
        </div>

        {/* Giant Editorial Headline */}
        <h1
          className="font-serif-headline"
          style={{
            fontSize: "clamp(3.5rem, 8.5vw, 6.8rem)",
            lineHeight: 0.95,
            fontWeight: 400,
            marginBottom: "36px",
            letterSpacing: "-0.02em",
            color: "var(--text-main)",
          }}
        >
          Opportunities that<br />
          <span className="yellow-highlight">mean something.</span>
        </h1>

        {/* Mission + Action Strip */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.1fr 0.9fr",
            gap: "48px",
            alignItems: "flex-end",
            marginBottom: "64px",
          }}
        >
          {/* Mission Subtext */}
          <div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.12em", color: "var(--text-muted)", marginBottom: "12px" }}>
              MISSION 001
            </div>
            <p style={{ fontSize: "1.1rem", color: "var(--text-main)", lineHeight: 1.6, maxWidth: "540px", fontWeight: 500 }}>
              BharatAI is an independent academic opportunity index for students, research fellows, and category-defining teams across Indian institutions who refuse to settle.
            </p>
            <div style={{ marginTop: "16px" }}>
              <span className="sticker-badge sticker-green" style={{ transform: "rotate(-4deg)" }}>
                INDEPENDENT SINCE 2026
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "14px", justifyContent: "flex-end" }}>
            <Link href="/opportunities" className="btn-hard-primary">
              SEARCH INDEX ↗
            </Link>
            <a href="#capabilities" className="btn-hard-secondary">
              SEE THE WORK ↘
            </a>
          </div>
        </div>

        {/* ── Search & Capabilities Section ── */}
        <section id="capabilities" style={{ marginBottom: "64px" }}>
          {/* Hard Input Bar */}
          <form onSubmit={handleSearch} style={{ position: "relative", marginBottom: "28px" }}>
            <Search
              size={20}
              style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "#0F0F11" }}
            />
            <input
              type="text"
              className="field-input"
              placeholder="Search by institution, fellowship, scholarship, or hackathon (e.g. IISc, PMRF, Hackathon)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="btn-hard-primary" style={{ position: "absolute", right: "6px", top: "6px", bottom: "6px", padding: "0 20px" }}>
              SEARCH ↗
            </button>
          </form>

          {/* Monospace Filter Grid */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" }}>
              CAPABILITIES / DOMAIN FILTER
            </span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              SHOWING 6 VERIFIED LISTINGS
            </span>
          </div>

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "40px" }}>
            {[
              { label: "ALL DOMAINS", key: "all", color: "sticker-yellow" },
              { label: "AI & DATA SCIENCE", key: "ai_ds", color: "sticker-blue" },
              { label: "COMPUTER SCIENCE", key: "cs", color: "sticker-pink" },
              { label: "GOVERNMENT & POLICY", key: "govt_policy", color: "sticker-teal" },
              { label: "MANAGEMENT", key: "management", color: "sticker-green" },
            ].map((domain) => (
              <button
                key={domain.key}
                type="button"
                className={`sticker-badge ${activeDomain === domain.key ? domain.color : ""}`}
                style={{
                  cursor: "pointer",
                  backgroundColor: activeDomain === domain.key ? undefined : "#FFFFFF",
                  color: activeDomain === domain.key ? undefined : "#0F0F11",
                }}
                onClick={() => setActiveDomain(domain.key)}
              >
                {domain.label}
              </button>
            ))}
          </div>

          {/* ── Opportunity Grid Cards (Field Cards) ── */}
          {isLoading ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "24px" }}>
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="field-card" style={{ height: 260, backgroundColor: "#EFECE6" }} />
              ))}
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "24px" }}>
              {opportunities.map((item, index) => {
                const domainLabel = DOMAIN_LABELS[item.domain] ?? item.domain;
                const link = item.application_link || item.source_url;
                const circleColors = ["#FDE047", "#3B82F6", "#F472B6", "#2DD4BF", "#34D399", "#FDE047"];
                const numStr = String(index + 1).padStart(2, "0");

                const days = item.deadline
                  ? Math.ceil((new Date(item.deadline).getTime() - Date.now()) / 86400000)
                  : null;

                return (
                  <div key={item.opportunity_id} className="field-card">
                    <div>
                      {/* Top Circle + Domain Badge Row */}
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                        <div className="num-circle" style={{ backgroundColor: circleColors[index % circleColors.length] }}>
                          {numStr}
                        </div>
                        <span className="sticker-badge sticker-teal" style={{ fontSize: "0.65rem" }}>
                          {domainLabel}
                        </span>
                      </div>

                      {/* Opportunity Title */}
                      <h3 style={{ fontSize: "1.15rem", fontWeight: 800, lineHeight: 1.3, marginBottom: "8px", color: "var(--text-main)" }}>
                        {item.title}
                      </h3>

                      {item.institution && (
                        <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.78rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px" }}>
                          <Building2 size={13} /> {item.institution}
                        </p>
                      )}

                      {item.description && (
                        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.5, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden", marginBottom: "20px" }}>
                          {item.description}
                        </p>
                      )}
                    </div>

                    {/* Footer Row */}
                    <div style={{ paddingTop: "14px", borderTop: "var(--border-hard)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72rem", fontWeight: 700, color: days && days <= 7 ? "#EF4444" : "var(--text-muted)" }}>
                        {days !== null && days >= 0 ? `${days} DAYS LEFT` : "VERIFIED LISTING"}
                      </span>

                      {link && (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-hard-primary"
                          style={{ padding: "6px 14px", fontSize: "0.7rem" }}
                        >
                          APPLY ↗
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* ── 3 Numbered System Blocks (Field Notes Style) ── */}
        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "24px",
            marginBottom: "64px",
          }}
        >
          <div className="field-card" style={{ backgroundColor: "#FFFFFF" }}>
            <div className="num-circle" style={{ backgroundColor: "#FDE047", marginBottom: "16px" }}>01</div>
            <h4 style={{ fontSize: "1.1rem", fontWeight: 800, marginBottom: "8px" }}>DIRECT INGESTION</h4>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
              Ingests academic notices directly from IITs, IISc, NITs, and central government scholarship portals across India.
            </p>
          </div>

          <div className="field-card" style={{ backgroundColor: "#FFFFFF" }}>
            <div className="num-circle" style={{ backgroundColor: "#3B82F6", color: "#FFFFFF", marginBottom: "16px" }}>02</div>
            <h4 style={{ fontSize: "1.1rem", fontWeight: 800, marginBottom: "8px" }}>INCOSCORE PROTOCOL</h4>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
              A unified 1000-point merit system tracking hackathons, publications, and verified research internships.
            </p>
          </div>

          <div className="field-card" style={{ backgroundColor: "#FFFFFF" }}>
            <div className="num-circle" style={{ backgroundColor: "#F472B6", marginBottom: "16px" }}>03</div>
            <h4 style={{ fontSize: "1.1rem", fontWeight: 800, marginBottom: "8px" }}>KANBAN PIPELINE</h4>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
              Organize applications by stages with automated deadline decay alerts so you never miss a submission window.
            </p>
          </div>
        </section>

        {/* ── Field Notes CTA Banner ── */}
        <section
          className="field-card"
          style={{
            backgroundColor: "#0F0F11",
            color: "#FFFFFF",
            padding: "48px 40px",
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "24px",
          }}
        >
          <div>
            <span className="sticker-badge sticker-yellow" style={{ marginBottom: "16px" }}>
              FREE FOR STUDENTS
            </span>
            <h2 className="font-serif-headline" style={{ fontSize: "2.8rem", color: "#FFFFFF", lineHeight: 1.05 }}>
              Ready to change your academic trajectory?
            </h2>
            <p style={{ color: "#A1A1AA", fontSize: "0.95rem", marginTop: "8px" }}>
              Join thousands of students on India&apos;s primary academic opportunity index.
            </p>
          </div>

          <Link href="/register" className="btn-hard-secondary" style={{ backgroundColor: "#FDE047", color: "#0F0F11" }}>
            CREATE FREE PROFILE ↗
          </Link>
        </section>
      </main>

      {/* ── Field Notes Footer ── */}
      <footer style={{ borderTop: "var(--border-hard)", padding: "32px 40px", backgroundColor: "var(--bg-base)" }}>
        <div style={{ maxWidth: "1240px", margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: 28, height: 28, backgroundColor: "#0F0F11", color: "#FFFFFF", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: "0.8rem", fontFamily: "'JetBrains Mono', monospace" }}>
              BA
            </div>
            <span style={{ fontWeight: 800, fontSize: "0.9rem" }}>BHARATAI INDEX</span>
          </div>

          <div style={{ display: "flex", gap: "20px", fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700 }}>
            <Link href="/opportunities" style={{ color: "var(--text-main)", textDecoration: "none" }}>OPPORTUNITIES</Link>
            <Link href="/login" style={{ color: "var(--text-main)", textDecoration: "none" }}>SIGN IN</Link>
            <Link href="/register" style={{ color: "var(--text-main)", textDecoration: "none" }}>REGISTER</Link>
          </div>

          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            © {new Date().getFullYear()} BHARATAI · ALL RIGHTS RESERVED
          </span>
        </div>
      </footer>
    </div>
  );
}
