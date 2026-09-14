"use client";

import { useQuery } from "@tanstack/react-query";
import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Building2 } from "lucide-react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

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

const POLL_INTERVAL_MS = 60_000;

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

function OpportunityCard({ item, index, isNew }: { item: FeedItem; index: number; isNew?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const domainLabel = DOMAIN_LABELS[item.domain] ?? item.domain;
  const numStr = String(index + 1).padStart(2, "0");
  const circleColors = ["#FDE047", "#3B82F6", "#F472B6", "#2DD4BF", "#34D399"];

  const days = item.deadline
    ? Math.ceil((new Date(item.deadline).getTime() - Date.now()) / 86400000)
    : null;

  const handleApply = () => {
    const link = item.application_link || item.source_url;
    if (link) window.open(link, "_blank", "noopener,noreferrer");
  };

  return (
    <div
      className="field-card"
      style={{
        backgroundColor: "#FFFFFF",
        ...(isNew && { borderColor: "#3B82F6", boxShadow: "4px 4px 0px #3B82F6" }),
      }}
    >
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <div className="num-circle" style={{ backgroundColor: circleColors[index % circleColors.length] }}>
            {numStr}
          </div>
          <div style={{ display: "flex", gap: "6px" }}>
            {isNew && (
              <span className="sticker-badge sticker-blue" style={{ fontSize: "0.6rem" }}>
                NEW
              </span>
            )}
            <span className="sticker-badge sticker-teal" style={{ fontSize: "0.65rem" }}>
              {domainLabel.toUpperCase()}
            </span>
          </div>
        </div>

        <h3 style={{ fontSize: "1.1rem", fontWeight: 800, lineHeight: 1.35, marginBottom: "8px", color: "#0F0F11" }}>
          {item.title}
        </h3>

        {item.institution && (
          <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.78rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
            <Building2 size={13} /> {item.institution}
          </p>
        )}

        {item.relevance_score > 0 && (
          <div style={{ marginBottom: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)", marginBottom: "4px" }}>
              <span>VECTOR MATCH</span>
              <span style={{ fontWeight: 800, color: "#0F0F11" }}>{Math.round(item.relevance_score * 100)}%</span>
            </div>
            <div style={{ height: "6px", backgroundColor: "#EFECE6", borderRadius: "3px", overflow: "hidden", border: "1px solid #0F0F11" }}>
              <div style={{ width: `${item.relevance_score * 100}%`, height: "100%", backgroundColor: "#FDE047" }} />
            </div>
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
          onClick={handleApply}
          className="btn-hard-primary"
          style={{ padding: "6px 14px", fontSize: "0.7rem" }}
        >
          APPLY ↗
        </button>
      </div>
    </div>
  );
}

export default function FeedPage() {
  const [domain, setDomain] = useState("All");
  const [search, setSearch] = useState("");
  const { user } = useAuthStore();
  const prevIdsRef = useRef<Set<string>>(new Set());
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const [pendingCount, setPendingCount] = useState(0);

  const fetchFeed = useCallback(() => {
    const params: Record<string, string> = { limit: "50" };
    if (domain !== "All") params.domain = domain;
    return api.get("/feed", { params }).then((r) => r.data);
  }, [domain]);

  const { data, isLoading } = useQuery({
    queryKey: ["feed", domain],
    queryFn: fetchFeed,
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: false,
  });

  useEffect(() => {
    if (!data?.items) return;
    const currentIds = new Set<string>(data.items.map((i: FeedItem) => i.opportunity_id));

    if (prevIdsRef.current.size === 0) {
      prevIdsRef.current = currentIds;
      return;
    }

    const fresh = new Set<string>();
    for (const id of currentIds) {
      if (!prevIdsRef.current.has(id)) fresh.add(id);
    }

    if (fresh.size > 0) {
      setPendingCount((prev) => prev + fresh.size);
      setNewIds((prev) => new Set([...prev, ...fresh]));
    }
    prevIdsRef.current = currentIds;
  }, [data]);

  const handleLoadNew = () => {
    setPendingCount(0);
    setTimeout(() => setNewIds(new Set()), 8_000);
  };

  const isColdStart = data?.cold_start ?? false;
  const items: FeedItem[] = (data?.items ?? []).filter((item: FeedItem) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return item.title.toLowerCase().includes(q) || (item.institution ?? "").toLowerCase().includes(q);
  });

  return (
    <div style={{ maxWidth: 1240, margin: "0 auto", padding: "48px 40px" }}>
      {/* Header */}
      <div style={{ marginBottom: "36px" }}>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            PERSONALIZED FEED
          </span>
          <span className="sticker-badge sticker-blue" style={{ transform: "rotate(1deg)" }}>
            AUTO REFRESH
          </span>
        </div>

        <h1 className="font-serif-headline" style={{ fontSize: "clamp(2.6rem, 5.5vw, 4.4rem)", lineHeight: 1.05, fontWeight: 400, marginBottom: "8px" }}>
          {isColdStart ? "Explore opportunity index." : `Welcome back, ${user?.name?.split(" ")[0] ?? "Fellow"}.`}
        </h1>
        <p style={{ fontSize: "1.05rem", color: "var(--text-muted)", maxWidth: "600px" }}>
          {isColdStart
            ? "Complete your profile to get AI-ranked opportunities matched to your degree and skills."
            : "Your custom index feed — opportunities matched to your skill profile and deadlines."}
        </p>
      </div>

      {/* Search Input */}
      <form onSubmit={(e) => e.preventDefault()} style={{ position: "relative", marginBottom: "28px" }}>
        <Search size={20} style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "#0F0F11" }} />
        <input
          type="text"
          className="field-input"
          placeholder="Filter feed by title, university, or keywords..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </form>

      {/* Domain Filters */}
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

      {/* Content Grid */}
      {isLoading ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "24px" }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="field-card" style={{ height: 260, backgroundColor: "#EFECE6" }} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="field-card" style={{ textAlign: "center", padding: "64px", backgroundColor: "#FFFFFF" }}>
          <h3 style={{ fontSize: "1.2rem", fontWeight: 800, marginBottom: "8px" }}>NO MATCHES IN YOUR FEED</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Try switching category filters or searching with different terms.</p>
        </div>
      ) : (
        <div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, marginBottom: "20px" }}>
            SHOWING {items.length} MATCHED FEED ITEMS
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "24px" }}>
            {items.map((item, index) => (
              <OpportunityCard
                key={item.opportunity_id}
                item={item}
                index={index}
                isNew={newIds.has(item.opportunity_id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Live Toast */}
      {pendingCount > 0 && (
        <div
          onClick={handleLoadNew}
          className="sticker-badge sticker-yellow"
          style={{
            position: "fixed",
            bottom: "32px",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 100,
            padding: "12px 24px",
            fontSize: "0.85rem",
            cursor: "pointer",
            boxShadow: "var(--shadow-hard-lg)",
          }}
        >
          ⚡ {pendingCount} NEW OPPORTUNITIES AVAILABLE — CLICK TO LOAD ↗
        </div>
      )}
    </div>
  );
}
