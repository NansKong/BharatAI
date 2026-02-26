"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

export default function RegisterPage() {
    const router = useRouter();
    const login = useAuthStore((s) => s.login);

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [college, setCollege] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const validate = () => {
        if (name.trim().length < 2) return "Name must be at least 2 characters";
        if (!email.includes("@")) return "Enter a valid email address";
        if (password.length < 8) return "Password must be at least 8 characters";
        if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter";
        if (!/\d/.test(password)) return "Password must contain at least one number";
        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const err = validate();
        if (err) { setError(err); return; }
        setError("");
        setLoading(true);
        try {
            const body: Record<string, string> = { name, email, password };
            if (college.trim()) body.college = college.trim();
            const res = await api.post("/auth/register", body);
            const { access_token, refresh_token } = res.data;
            const meRes = await api.get("/users/me", {
                headers: { Authorization: `Bearer ${access_token}` },
            });
            login(meRes.data, access_token, refresh_token);
            router.push("/feed");
        } catch (err: unknown) {
            const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
            let msg = "Registration failed. Please try again.";
            if (typeof detail === "string") {
                msg = detail;
            } else if (Array.isArray(detail) && detail.length > 0) {
                // Pydantic 422 returns [{loc, msg, type}]
                msg = detail.map((d: { msg?: string }) => d.msg ?? "").filter(Boolean).join(". ") || msg;
            }
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-base)", padding: 24 }}>
            <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass"
                style={{ width: "100%", maxWidth: 440, borderRadius: "var(--radius-xl)", padding: "40px 36px" }}
            >
                <Link href="/" style={{ textDecoration: "none" }}>
                    <span className="gradient-text" style={{ fontSize: "1.4rem", fontWeight: 800 }}>BharatAI</span>
                </Link>
                <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "20px 0 6px" }}>Create account</h1>
                <p style={{ color: "var(--text-secondary)", marginBottom: 28, fontSize: "0.9rem" }}>Start finding opportunities today</p>

                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    {/* Name */}
                    <div>
                        <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>Full Name</label>
                        <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Priya Sharma" className="input" required />
                    </div>
                    {/* Email */}
                    <div>
                        <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>Email</label>
                        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="priya@example.com" className="input" required />
                    </div>
                    {/* Password */}
                    <div>
                        <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>Password</label>
                        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 chars, 1 uppercase, 1 number" className="input" required />
                    </div>
                    {/* College */}
                    <div>
                        <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>College (optional)</label>
                        <input type="text" value={college} onChange={(e) => setCollege(e.target.value)} placeholder="IIT Bombay" className="input" />
                    </div>

                    {/* Password hint */}
                    <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: -6 }}>
                        Must be 8+ characters with at least 1 uppercase letter and 1 number
                    </p>

                    {error && (
                        <div style={{ background: "rgba(255,80,80,0.1)", border: "1px solid rgba(255,80,80,0.3)", borderRadius: "var(--radius-md)", padding: "10px 14px", fontSize: "0.85rem", color: "#ff5050" }}>
                            {error}
                        </div>
                    )}

                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%", justifyContent: "center", marginTop: 4 }}>
                        {loading ? "Creating account…" : "Create account →"}
                    </button>
                </form>

                <hr className="divider" />
                <p style={{ textAlign: "center", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                    Have an account?{" "}
                    <Link href="/login" style={{ color: "var(--emerald)", textDecoration: "none", fontWeight: 600 }}>
                        Sign in
                    </Link>
                </p>
            </motion.div>
        </div>
    );
}
