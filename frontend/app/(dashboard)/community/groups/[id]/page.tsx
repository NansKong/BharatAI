"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { use, useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import api from "@/lib/api";

interface Message {
    id: string;
    content: string;
    author_name?: string;
    created_at: string;
}

export default function GroupChatPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [msg, setMsg] = useState("");
    const bottomRef = useRef<HTMLDivElement>(null);

    const { data: messages = [], refetch } = useQuery<Message[]>({
        queryKey: ["group-messages", id],
        queryFn: () => api.get(`/community/groups/${id}/messages`).then((r) => r.data.items ?? r.data),
        refetchInterval: 3000, // Poll every 3s (WebSocket upgrade in production)
    });

    const send = useMutation({
        mutationFn: (content: string) => api.post(`/community/groups/${id}/messages`, { content }),
        onSuccess: () => { setMsg(""); refetch(); },
    });

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 140px)" }}>
            <h1 style={{ fontSize: "1.3rem", fontWeight: 700, marginBottom: 16 }}>Group Chat</h1>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, paddingRight: 8 }}>
                {messages.map((m, i) => (
                    <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.02 }}
                        style={{ display: "flex", gap: 12, alignItems: "flex-start" }}
                    >
                        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg, var(--saffron), var(--emerald))", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontWeight: 700, fontSize: "0.75rem", color: "#fff" }}>
                            {(m.author_name ?? "?").charAt(0).toUpperCase()}
                        </div>
                        <div className="glass" style={{ borderRadius: "var(--radius-md)", padding: "10px 14px", maxWidth: "75%" }}>
                            <p style={{ fontWeight: 600, fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: 3 }}>{m.author_name ?? "Student"}</p>
                            <p style={{ fontSize: "0.9rem" }}>{m.content}</p>
                            <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: 4 }}>{new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</p>
                        </div>
                    </motion.div>
                ))}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{ display: "flex", gap: 10, marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
                <input value={msg} onChange={(e) => setMsg(e.target.value)} placeholder="Type a message…" className="input" style={{ flex: 1 }}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (msg.trim()) send.mutate(msg.trim()); } }} />
                <button onClick={() => msg.trim() && send.mutate(msg.trim())} className="btn btn-primary" disabled={!msg.trim() || send.isPending}>
                    Send →
                </button>
            </div>
        </div>
    );
}
