"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import axios from "axios";
import { Search, Building2 } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { TopNav } from "@/components/layout/Sidebar";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DOMAINS = [
  { code: "All", label: "ALL DOMAINS", color: "sticker-yellow" },
  { code: "ai_ds", label: "AI & DATA SCIENCE", color: "sticker-blue" },
  { code: "cs", label: "COMPUTER SCIENCE", color: "sticker-pink" },
  { code: "ece", label: "ELECTRONICS", color: "sticker-teal" },
  { code: "me", label: "MECHANICAL", color: "sticker-green" },
  { code: "management", label: "MANAGEMENT", color: "sticker-yellow" },
  { code: "govt", label: "GOVERNMENT", color: "sticker-teal" },
  { code: "humanities", label: "HUMANITIES", color: "sticker-pink" },
  { code: "biotech", label: "BIOTECH", color: "sticker-green" },
  { code: "unclassified", label: "RESEARCH", color: "sticker-blue" },
];

const DOMAIN_LABELS: Record<string, string> = {
  ai_ds: "AI & Data Science",
  cs: "Computer Science",
  ece: "Electronics",
  me: "Mechanical",
  management: "Management",
  govt: "Government & Policy",
  govt_policy: "Government & Policy",
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
  eligibility?: string;
  description?: string;
  relevance_score: number;
  is_authenticated: boolean;
}

function OpportunityCard({
  item,
  index,
  onApply,
}: {
  item: FeedItem;
  index: number;
  onApply: (item: FeedItem) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const domainLabel = DOMAIN_LABELS[item.domain] ?? item.domain;
  const numStr = String(index + 1).padStart(2, "0");
  const circleColors = ["#FDE047", "#3B82F6", "#F472B6", "#2DD4BF", "#34D399"];

  const days = item.deadline
    ? Math.ceil((new Date(item.deadline).getTime() - Date.now()) / 86400000)
    : null;

  return (
    <div className="field-card">
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <div className="num-circle" style={{ backgroundColor: circleColors[index % circleColors.length] }}>
            {numStr}
          </div>
          <span className="sticker-badge sticker-teal" style={{ fontSize: "0.65rem" }}>
            {domainLabel.toUpperCase()}
          </span>
        </div>

        <h3 style={{ fontSize: "1.1rem", fontWeight: 800, lineHeight: 1.35, marginBottom: "8px", color: "#0F0F11" }}>
          {item.title}
        </h3>

        {item.institution && (
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.78rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
            <Building2 size={13} /> {item.institution}
          </p>
        )}

        {item.eligibility && (
          <div style={{ backgroundColor: "var(--bg-surface)", border: "var(--border-hard)", borderRadius: "var(--radius-box)", padding: "8px 12px", marginBottom: "12px" }}>
            <p style={{ fontSize: "0.75rem", fontFamily: "'JetBrains Mono', monospace", color: "#0F0F11", margin: 0 }}>
              ELIGIBILITY: {item.eligibility.length > 110 ? item.eligibility.slice(0, 110) + "…" : item.eligibility}
            </p>
          </div>
        )}

        {expanded && item.description && (
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.5, marginBottom: "12px" }}>
            {item.description}
          </p>
        )}

        {item.description && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "0.72rem",
              fontWeight: 700,
              color: "#0F0F11",
              marginBottom: "12px",
              padding: 0,
            }}
          >
            {expanded ? "▲ LESS DETAILS" : "▼ MORE DETAILS"}
          </button>
        )}
      </div>

      <div style={{ paddingTop: "14px", borderTop: "var(--border-hard)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72rem", fontWeight: 700, color: days && days <= 7 ? "#EF4444" : "var(--text-muted)" }}>
          {days !== null && days >= 0 ? `${days} DAYS LEFT` : "VERIFIED LISTING"}
        </span>

        <button
          type="button"
          onClick={() => onApply(item)}
          className="btn-hard-primary"
          style={{ padding: "6px 14px", fontSize: "0.7rem" }}
        >
          APPLY ↗
        </button>
      </div>
    </div>
  );
}

function OpportunitiesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, accessToken } = useAuthStore();

  const [domain, setDomain] = useState(searchParams.get("domain") ?? "All");
  const [search, setSearch] = useState(searchParams.get("q") ?? "");

  const isLoggedIn = !!user && !!accessToken;

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
    <div style={{ maxWidth: 1240, margin: "0 auto", padding: "48px 40px" }}>
      {/* Page Header */}
      <div style={{ marginBottom: "36px" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "16px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            DIRECTORY 2026
          </span>
          <span className="sticker-badge sticker-blue" style={{ transform: "rotate(1deg)" }}>
            VERIFIED INDEX
          </span>
        </div>

        <h1 className="font-serif-headline" style={{ fontSize: "clamp(2.8rem, 6vw, 4.8rem)", lineHeight: 1.05, fontWeight: 400, marginBottom: "12px" }}>
          Browse the opportunity index.
        </h1>
        <p style={{ fontSize: "1.05rem", color: "var(--text-muted)", maxWidth: "600px" }}>
          Explore hackathons, research fellowships, and government scholarships aggregated across top Indian academic institutions.
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={(e) => e.preventDefault()} style={{ position: "relative", marginBottom: "28px" }}>
        <Search size={20} style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "#0F0F11" }} />
        <input
          type="text"
          className="field-input"
          placeholder="Search by title, institution, or keywords..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </form>

      {/* Filter Buttons */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "36px" }}>
        {DOMAINS.map((d) => (
          <button
            key={d.code}
            type="button"
            className={`sticker-badge ${domain === d.code ? d.color : ""}`}
            style={{
              cursor: "pointer",
              backgroundColor: domain === d.code ? undefined : "#FFFFFF",
              color: domain === d.code ? undefined : "#0F0F11",
            }}
            onClick={() => setDomain(d.code)}
          >
            {d.label}
          </button>
        ))}
      </div>

      {/* Grid */}
      {isLoading ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "24px" }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="field-card" style={{ height: 260, backgroundColor: "#EFECE6" }} />
          ))}
        </div>
      ) : isError ? (
        <div className="field-card" style={{ textAlign: "center", padding: "64px", backgroundColor: "#FFFFFF" }}>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 800, marginBottom: "8px" }}>COULD NOT LOAD LISTINGS</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Please verify the backend server connection and try again.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="field-card" style={{ textAlign: "center", padding: "64px", backgroundColor: "#FFFFFF" }}>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 800, marginBottom: "8px" }}>NO MATCHING LISTINGS FOUND</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Try adjusting your search keywords or switching category filters.</p>
        </div>
      ) : (
        <div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, marginBottom: "20px" }}>
            SHOWING {items.length} VERIFIED OPPORTUNITIES
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "24px" }}>
            {items.map((item, index) => (
              <OpportunityCard key={item.opportunity_id} item={item} index={index} onApply={handleApply} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function OpportunitiesPage() {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-base)" }}>
      <TopNav />
      <Suspense fallback={<div style={{ padding: "60px", textAlign: "center", fontFamily: "'JetBrains Mono', monospace" }}>LOADING INDEX...</div>}>
        <OpportunitiesContent />
      </Suspense>
    </div>
  );
}
