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
        onSuccess: () => { qc.invalidateQueries({ queryKey: ["profile"] }); setEditing(false); },
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

    const displayName = data?.name ?? user?.name ?? "";
    const displayEmail = data?.email ?? user?.email ?? "";
    const displayCollege = data?.college ?? user?.college;

    return (
        <div style={{ maxWidth: 640 }}>
            {/* Avatar + name */}
            <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 28 }}>
                <div style={{ width: 64, height: 64, borderRadius: "50%", background: "linear-gradient(135deg, var(--saffron), var(--emerald))", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.8rem", fontWeight: 800, color: "#fff", flexShrink: 0 }}>
                    {displayName.charAt(0).toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                    <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>{displayName}</h1>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>{displayEmail}</p>
                    {displayCollege && <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{displayCollege}</p>}
                </div>
                <button
                    onClick={() => editing ? save.mutate(form) : startEdit()}
                    className={`btn ${editing ? "btn-primary" : "btn-secondary"}`}
                    style={{ fontSize: "0.85rem" }}
                >
                    {editing ? (save.isPending ? "Saving…" : "Save") : "Edit Profile"}
                </button>
            </div>

            {/* Bio */}
            <div className="glass card" style={{ marginBottom: 16 }}>
                <h3 style={{ fontWeight: 700, fontSize: "0.85rem", marginBottom: 10, color: "var(--text-secondary)" }}>BIO</h3>
                {editing ? (
                    <textarea value={form.bio ?? ""} onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))} className="input" style={{ minHeight: 80, resize: "vertical" }} placeholder="Tell the community about yourself…" />
                ) : (
                    <p style={{ fontSize: "0.9rem", color: profile?.bio ? "var(--text-primary)" : "var(--text-muted)" }}>{profile?.bio || "No bio yet."}</p>
                )}
            </div>

            {/* Skills */}
            <div className="glass card" style={{ marginBottom: 16 }}>
                <h3 style={{ fontWeight: 700, fontSize: "0.85rem", marginBottom: 10, color: "var(--text-secondary)" }}>SKILLS</h3>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: editing ? 12 : 0 }}>
                    {(editing ? form.skills : profile?.skills ?? []).map((s) => (
                        <span
                            key={s}
                            className="badge badge-emerald"
                            style={{ cursor: editing ? "pointer" : "default" }}
                            onClick={() => editing && removeSkill(s)}
                        >
                            {s} {editing && "×"}
                        </span>
                    ))}
                    {(editing ? form.skills : profile?.skills ?? []).length === 0 && (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No skills added yet.</p>
                    )}
                </div>
                {editing && (
                    <div style={{ display: "flex", gap: 8 }}>
                        <input
                            value={newSkill}
                            onChange={(e) => setNewSkill(e.target.value)}
                            placeholder="Add skill…"
                            className="input"
                            style={{ flex: 1 }}
                            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }}
                        />
                        <button onClick={addSkill} className="btn btn-secondary">Add</button>
                    </div>
                )}
            </div>

            {/* Social links */}
            <div className="glass card">
                <h3 style={{ fontWeight: 700, fontSize: "0.85rem", marginBottom: 10, color: "var(--text-secondary)" }}>LINKS</h3>
                {editing ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        <input value={form.github_url ?? ""} onChange={(e) => setForm((f) => ({ ...f, github_url: e.target.value }))} placeholder="GitHub URL" className="input" />
                        <input value={form.linkedin_url ?? ""} onChange={(e) => setForm((f) => ({ ...f, linkedin_url: e.target.value }))} placeholder="LinkedIn URL" className="input" />
                    </div>
                ) : (
                    <div style={{ display: "flex", gap: 12 }}>
                        {profile?.github_url && <a href={profile.github_url} target="_blank" rel="noreferrer" className="btn btn-ghost" style={{ fontSize: "0.82rem" }}>🐙 GitHub</a>}
                        {profile?.linkedin_url && <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="btn btn-ghost" style={{ fontSize: "0.82rem" }}>💼 LinkedIn</a>}
                        {!profile?.github_url && !profile?.linkedin_url && <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No links added yet.</p>}
                    </div>
                )}
            </div>
        </div>
    );
}
