"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
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

export default function LeaderboardPage() {
  const [tab, setTab] = useState<Tab>("Overall");
  const [domain, setDomain] = useState(DOMAINS[0]);

  const myScore = useQuery<Score>({
    queryKey: ["my-score"],
    queryFn: () => api.get("/incoscore/me").then((r) => r.data),
  });

  const boardQuery = useQuery<LeaderboardEntry[]>({
    queryKey: ["leaderboard", tab, domain],
    queryFn: () => {
      const url =
        tab === "Domain"
          ? `/incoscore/leaderboard/domain?domain=${domain}&limit=25`
          : tab === "College"
          ? `/incoscore/leaderboard/college?limit=25`
          : `/incoscore/leaderboard?limit=25`;
      return api.get(url).then((r) => r.data.entries ?? r.data);
    },
  });

  return (
    <div style={{ maxWidth: 1080, margin: "0 auto", padding: "36px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            MERIT PROTOCOL
          </span>
          <span className="sticker-badge sticker-blue" style={{ transform: "rotate(1deg)" }}>
            INCOSCORE INDEX
          </span>
        </div>

        <h1 className="font-serif-headline" style={{ fontSize: "clamp(2.4rem, 5vw, 4rem)", lineHeight: 1.05, fontWeight: 400, marginBottom: "8px" }}>
          National merit rankings.
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          Standardized 1000-point merit scores calculated across Indian academic institutions.
        </p>
      </div>

      {/* My Score Card */}
      {myScore.data && (
        <div
          className="field-card"
          style={{
            backgroundColor: "#FFFFFF",
            marginBottom: "32px",
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "24px 32px",
          }}
        >
          <div>
            <span className="sticker-badge sticker-pink" style={{ marginBottom: "8px" }}>
              YOUR CURRENT MERIT SCORE
            </span>
            <div style={{ fontSize: "2.6rem", fontWeight: 900, fontFamily: "'JetBrains Mono', monospace", color: "#0F0F11" }}>
              {Math.round(myScore.data.total_score)} <span style={{ fontSize: "1rem", color: "var(--text-muted)" }}>/ 1000</span>
            </div>
            <p style={{ fontSize: "0.78rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)", marginTop: "4px" }}>
              UPDATED: {new Date(myScore.data.computed_at).toLocaleDateString("en-IN")}
            </p>
          </div>

          <div style={{ textAlign: "right" }}>
            <span className="sticker-badge sticker-teal">
              VERIFIED CANDIDATE
            </span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            className={`sticker-badge ${tab === t ? "sticker-yellow" : ""}`}
            style={{
              cursor: "pointer",
              backgroundColor: tab === t ? undefined : "#FFFFFF",
              color: tab === t ? undefined : "#0F0F11",
            }}
            onClick={() => setTab(t)}
          >
            {t.toUpperCase()} RANKINGS
          </button>
        ))}
      </div>

      {tab === "Domain" && (
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "20px" }}>
          {DOMAINS.map((d) => (
            <button
              key={d}
              type="button"
              className={`sticker-badge ${domain === d ? "sticker-blue" : ""}`}
              style={{
                cursor: "pointer",
                backgroundColor: domain === d ? undefined : "#FFFFFF",
                color: domain === d ? undefined : "#0F0F11",
                fontSize: "0.68rem",
              }}
              onClick={() => setDomain(d)}
            >
              {d.toUpperCase()}
            </button>
          ))}
        </div>
      )}

      {/* Leaderboard Table */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {(boardQuery.data ?? []).map((entry, i) => {
          const numStr = String(i + 1).padStart(2, "0");
          const colors = ["#FDE047", "#2DD4BF", "#F472B6"];
          return (
            <div
              key={entry.user_id}
              className="field-card"
              style={{
                backgroundColor: "#FFFFFF",
                padding: "16px 24px",
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div
                  className="num-circle"
                  style={{
                    backgroundColor: i < 3 ? colors[i] : "#EFECE6",
                    fontWeight: 800,
                  }}
                >
                  {numStr}
                </div>
                <div>
                  <h4 style={{ fontSize: "1rem", fontWeight: 800, color: "#0F0F11", margin: 0 }}>
                    {entry.name}
                  </h4>
                  {entry.college && (
                    <p style={{ fontSize: "0.78rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)", margin: 0 }}>
                      {entry.college}
                    </p>
                  )}
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "1.3rem", fontWeight: 900, fontFamily: "'JetBrains Mono', monospace", color: "#0F0F11" }}>
                  {Math.round(entry.total_score)}
                </span>
                <span style={{ fontSize: "0.7rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)", display: "block" }}>
                  PTS
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
