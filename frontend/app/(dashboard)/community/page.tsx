"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

interface Post {
  id: string;
  content: string;
  author_name?: string;
  like_count: number;
  comment_count: number;
  created_at: string;
}

interface Group {
  id: string;
  name: string;
  description?: string;
  member_count?: number;
}

export default function CommunityPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [newPost, setNewPost] = useState("");

  const { data: posts = [], refetch } = useQuery<Post[]>({
    queryKey: ["posts"],
    queryFn: () => api.get("/community/posts").then((r) => r.data.items ?? r.data),
  });

  const { data: groups = [] } = useQuery<Group[]>({
    queryKey: ["groups"],
    queryFn: () => api.get("/community/groups").then((r) => r.data.items ?? r.data),
  });

  const handlePost = async () => {
    if (!newPost.trim()) return;
    await api.post("/community/posts", { content: newPost });
    setNewPost("");
    setShowCreate(false);
    refetch();
  };

  return (
    <div style={{ maxWidth: 1120, margin: "0 auto", padding: "36px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
          <span className="sticker-badge sticker-teal" style={{ transform: "rotate(-2deg)" }}>
            PEER NETWORK
          </span>
          <span className="sticker-badge sticker-pink" style={{ transform: "rotate(1deg)" }}>
            STUDENT COMMUNITY
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 className="font-serif-headline" style={{ fontSize: "clamp(2.4rem, 5vw, 3.8rem)", lineHeight: 1.05, fontWeight: 400 }}>
              Peer discussion & groups.
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", marginTop: "4px" }}>
              Connect with fellow applicants across Indian technical and research universities.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowCreate(!showCreate)}
            className="btn-hard-primary"
          >
            {showCreate ? "CANCEL" : "NEW POST ↗"}
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "28px", alignItems: "start" }}>
        {/* Main Feed */}
        <div>
          {showCreate && (
            <div className="field-card" style={{ backgroundColor: "#FFFFFF", marginBottom: "24px" }}>
              <textarea
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                placeholder="Share research opportunities, hackathon team calls, or scholarship queries…"
                style={{
                  width: "100%",
                  minHeight: "100px",
                  padding: "12px",
                  border: "var(--border-hard)",
                  borderRadius: "var(--radius-box)",
                  fontFamily: "'Inter', sans-serif",
                  fontSize: "0.9rem",
                  marginBottom: "12px",
                  outline: "none",
                }}
              />
              <button
                type="button"
                onClick={handlePost}
                className="btn-hard-primary"
                disabled={!newPost.trim()}
              >
                POST TO INDEX ↗
              </button>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {posts.length === 0 ? (
              <div className="field-card" style={{ backgroundColor: "#FFFFFF", textAlign: "center", padding: "48px" }}>
                <p style={{ color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
                  NO COMMUNITY POSTS YET. BE THE FIRST TO START A DISCUSSION!
                </p>
              </div>
            ) : (
              posts.map((p, i) => {
                const colors = ["#FDE047", "#3B82F6", "#F472B6", "#2DD4BF"];
                return (
                  <div key={p.id} className="field-card" style={{ backgroundColor: "#FFFFFF" }}>
                    <div style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                      <div
                        className="num-circle"
                        style={{ backgroundColor: colors[i % colors.length], width: 36, height: 36, fontSize: "0.85rem", flexShrink: 0 }}
                      >
                        {(p.author_name ?? "S").charAt(0).toUpperCase()}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                          <span style={{ fontWeight: 800, fontSize: "0.9rem", color: "#0F0F11" }}>
                            {p.author_name ?? "Student Member"}
                          </span>
                          <span style={{ fontSize: "0.72rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
                            {new Date(p.created_at).toLocaleDateString("en-IN")}
                          </span>
                        </div>
                        <p style={{ fontSize: "0.92rem", lineHeight: 1.6, color: "var(--text-main)", marginBottom: "12px" }}>
                          {p.content}
                        </p>
                        <div style={{ display: "flex", gap: "16px", fontSize: "0.75rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
                          <span>❤️ {p.like_count} LIKES</span>
                          <span>💬 {p.comment_count} REPLIES</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Groups Sidebar */}
        <div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.1em", marginBottom: "12px", textTransform: "uppercase" }}>
            SPECIAL INTEREST GROUPS
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {groups.length === 0 ? (
              <div className="field-card" style={{ backgroundColor: "#FFFFFF", padding: "16px" }}>
                <p style={{ fontSize: "0.78rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
                  NO GROUPS FOUND
                </p>
              </div>
            ) : (
              groups.map((g) => (
                <Link key={g.id} href={`/community/groups/${g.id}`} style={{ textDecoration: "none" }}>
                  <div className="field-card" style={{ backgroundColor: "#FFFFFF", padding: "16px" }}>
                    <h4 style={{ fontSize: "0.9rem", fontWeight: 800, color: "#0F0F11", marginBottom: "4px" }}>
                      {g.name}
                    </h4>
                    {g.member_count && (
                      <p style={{ fontSize: "0.72rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
                        {g.member_count} MEMBERS
                      </p>
                    )}
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
