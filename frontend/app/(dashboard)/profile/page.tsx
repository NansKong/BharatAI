"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

interface ProfileData {
  bio?: string;
  skills: string[];
  interests: string[];
  github_url?: string;
  linkedin_url?: string;
}

interface ProfileMeResponse {
  name: string;
  email: string;
  college?: string;
  profile: ProfileData;
}

const empty: ProfileData = { bio: "", skills: [], interests: [], github_url: "", linkedin_url: "" };

export default function ProfilePage() {
  const qc = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<ProfileData>(empty);
  const [newSkill, setNewSkill] = useState("");

  const { data } = useQuery<ProfileMeResponse>({
    queryKey: ["profile"],
    queryFn: () => api.get("/profile/me").then((r) => r.data),
  });

  const profile = data?.profile;

  const save = useMutation({
    mutationFn: (body: Partial<ProfileData>) => api.put("/profile", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
      setEditing(false);
    },
  });

  const startEdit = () => {
    setForm({
      bio: profile?.bio ?? "",
      skills: profile?.skills ?? [],
      interests: profile?.interests ?? [],
      github_url: profile?.github_url ?? "",
      linkedin_url: profile?.linkedin_url ?? "",
    });
    setEditing(true);
  };

  const addSkill = () => {
    if (!newSkill.trim()) return;
    setForm((f) => ({ ...f, skills: [...f.skills, newSkill.trim()] }));
    setNewSkill("");
  };

  const removeSkill = (s: string) =>
    setForm((f) => ({ ...f, skills: f.skills.filter((x) => x !== s) }));

  const displayName = data?.name ?? user?.name ?? "Student";
  const displayEmail = data?.email ?? user?.email ?? "";
  const displayCollege = data?.college ?? user?.college;

  return (
    <div style={{ maxWidth: 880, margin: "0 auto", padding: "36px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)" }}>
            STUDENT PROFILE
          </span>
          <span className="sticker-badge sticker-blue" style={{ transform: "rotate(1deg)" }}>
            VERIFIED DATA
          </span>
        </div>

        <div className="field-card" style={{ backgroundColor: "#FFFFFF", padding: "28px 32px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            <div className="num-circle" style={{ backgroundColor: "#FDE047", width: 56, height: 56, fontSize: "1.4rem", fontWeight: 900 }}>
              {displayName.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="font-serif-headline" style={{ fontSize: "2.2rem", fontWeight: 400, margin: 0, lineHeight: 1.1 }}>
                {displayName}
              </h1>
              <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.82rem", color: "var(--text-muted)", margin: "4px 0 0" }}>
                {displayEmail} {displayCollege ? `• ${displayCollege}` : ""}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => (editing ? save.mutate(form) : startEdit())}
            className="btn-hard-primary"
          >
            {editing ? (save.isPending ? "SAVING..." : "SAVE PROFILE ↗") : "EDIT PROFILE ↗"}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        {/* Bio */}
        <div className="field-card" style={{ backgroundColor: "#FFFFFF", padding: "24px 28px" }}>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.08em", marginBottom: "12px", textTransform: "uppercase" }}>
            ACADEMIC BIO & OBJECTIVES
          </div>
          {editing ? (
            <textarea
              value={form.bio ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
              placeholder="Describe your research interests, coursework, and technical background..."
              style={{
                width: "100%",
                minHeight: "90px",
                padding: "12px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                fontFamily: "'Inter', sans-serif",
                fontSize: "0.9rem",
                outline: "none",
              }}
            />
          ) : (
            <p style={{ fontSize: "0.95rem", lineHeight: 1.6, color: profile?.bio ? "#0F0F11" : "var(--text-muted)" }}>
              {profile?.bio || "No academic bio specified yet. Click 'Edit Profile' to add one."}
            </p>
          )}
        </div>

        {/* Skills */}
        <div className="field-card" style={{ backgroundColor: "#FFFFFF", padding: "24px 28px" }}>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.08em", marginBottom: "12px", textTransform: "uppercase" }}>
            VERIFIED SKILLS & COMPETENCIES
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: editing ? "16px" : "0" }}>
            {(editing ? form.skills : profile?.skills ?? []).map((s) => (
              <span
                key={s}
                className="sticker-badge sticker-teal"
                style={{ cursor: editing ? "pointer" : "default", fontSize: "0.72rem" }}
                onClick={() => editing && removeSkill(s)}
              >
                {s} {editing && "×"}
              </span>
            ))}
            {(editing ? form.skills : profile?.skills ?? []).length === 0 && (
              <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", fontFamily: "'JetBrains Mono', monospace" }}>
                NO SKILLS ADDED YET.
              </p>
            )}
          </div>

          {editing && (
            <div style={{ display: "flex", gap: "10px" }}>
              <input
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Add new skill (e.g. Python, PyTorch, Embedded Systems)..."
                className="field-input"
                style={{ flex: 1, padding: "8px 14px", fontSize: "0.85rem" }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkill();
                  }
                }}
              />
              <button type="button" onClick={addSkill} className="btn-hard-secondary" style={{ padding: "8px 16px", fontSize: "0.75rem" }}>
                ADD SKILL
              </button>
            </div>
          )}
        </div>

        {/* Social Links */}
        <div className="field-card" style={{ backgroundColor: "#FFFFFF", padding: "24px 28px" }}>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.08em", marginBottom: "12px", textTransform: "uppercase" }}>
            EXTERNAL PROFILES & PORTFOLIO
          </div>
          {editing ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <input
                value={form.github_url ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, github_url: e.target.value }))}
                placeholder="GitHub Profile URL (https://github.com/...)"
                className="field-input"
                style={{ padding: "8px 14px", fontSize: "0.85rem" }}
              />
              <input
                value={form.linkedin_url ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, linkedin_url: e.target.value }))}
                placeholder="LinkedIn Profile URL (https://linkedin.com/in/...)"
                className="field-input"
                style={{ padding: "8px 14px", fontSize: "0.85rem" }}
              />
            </div>
          ) : (
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              {profile?.github_url && (
                <a href={profile.github_url} target="_blank" rel="noreferrer" className="btn-hard-secondary" style={{ padding: "8px 16px", fontSize: "0.75rem", textDecoration: "none" }}>
                  GITHUB PROFILES ↗
                </a>
              )}
              {profile?.linkedin_url && (
                <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="btn-hard-secondary" style={{ padding: "8px 16px", fontSize: "0.75rem", textDecoration: "none" }}>
                  LINKEDIN NETWORK ↗
                </a>
              )}
              {!profile?.github_url && !profile?.linkedin_url && (
                <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", fontFamily: "'JetBrains Mono', monospace" }}>
                  NO EXTERNAL LINKS CONNECTED YET.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
