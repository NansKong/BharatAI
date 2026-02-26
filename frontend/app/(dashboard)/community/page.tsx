"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "framer-motion";
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
        <div style={{ display: "grid", gridTemplateColumns: "1fr 260px", gap: 24, alignItems: "start" }}>
            {/* Main feed */}
            <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                    <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Community</h1>
                    <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary" style={{ fontSize: "0.85rem" }}>
                        + Post
                    </button>
                </div>

                {showCreate && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="glass card" style={{ marginBottom: 16 }}>
                        <textarea value={newPost} onChange={(e) => setNewPost(e.target.value)} placeholder="Share something with the community…" className="input" style={{ minHeight: 80, marginBottom: 12 }} />
                        <button onClick={handlePost} className="btn btn-primary" disabled={!newPost.trim()}>Post</button>
                    </motion.div>
                )}

                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {posts.map((p) => (
                        <motion.div key={p.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass card" style={{ padding: "16px 20px" }}>
                            <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                                <div style={{ width: 34, height: 34, borderRadius: "50%", background: "linear-gradient(135deg, var(--saffron), var(--emerald))", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontWeight: 700, fontSize: "0.8rem", color: "#fff" }}>
                                    {(p.author_name ?? "?").charAt(0).toUpperCase()}
                                </div>
                                <div style={{ flex: 1 }}>
                                    <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 4 }}>{p.author_name ?? "Student"}</p>
                                    <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{p.content}</p>
                                    <div style={{ display: "flex", gap: 16, marginTop: 10, fontSize: "0.78rem", color: "var(--text-muted)" }}>
                                        <span>❤️ {p.like_count}</span>
                                        <span>💬 {p.comment_count}</span>
                                        <span>{new Date(p.created_at).toLocaleDateString("en-IN")}</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Groups sidebar */}
            <div>
                <h3 style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: 12, color: "var(--text-secondary)" }}>GROUPS</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {groups.map((g) => (
                        <Link key={g.id} href={`/community/groups/${g.id}`} style={{ textDecoration: "none" }}>
                            <motion.div whileHover={{ x: 3 }} className="glass" style={{ borderRadius: "var(--radius-md)", padding: "12px 14px" }}>
                                <p style={{ fontWeight: 600, fontSize: "0.85rem" }}>{g.name}</p>
                                {g.member_count && <p style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{g.member_count} members</p>}
                            </motion.div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
