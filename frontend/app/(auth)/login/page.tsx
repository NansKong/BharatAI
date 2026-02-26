"use client";
import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

function LoginForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const redirectTo = searchParams.get("redirect") ?? "/feed";
    const login = useAuthStore((s) => s.login);

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const validate = () => {
        if (!email.includes("@")) return "Enter a valid email address";
        if (!password) return "Password is required";
        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const err = validate();
        if (err) { setError(err); return; }
        setError("");
        setLoading(true);
        try {
            const res = await api.post("/auth/login", { email, password });
            const { access_token, refresh_token } = res.data;
            const meRes = await api.get("/users/me", {
                headers: { Authorization: `Bearer ${access_token}` },
            });
            login(meRes.data, access_token, refresh_token);
            router.push(redirectTo);
        } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(msg ?? "Login failed. Check your email and password.");
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
                style={{ width: "100%", maxWidth: 420, borderRadius: "var(--radius-xl)", padding: "40px 36px" }}
            >
                <Link href="/" style={{ textDecoration: "none" }}>
                    <span className="gradient-text" style={{ fontSize: "1.4rem", fontWeight: 800 }}>BharatAI</span>
                </Link>
                <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "20px 0 6px" }}>Welcome back</h1>
                <p style={{ color: "var(--text-secondary)", marginBottom: 28, fontSize: "0.9rem" }}>Sign in to your account</p>

                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div>
                        <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            className="input"
                            required
                        />
                    </div>
                    <div>
                        <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            className="input"
                            required
                        />
                    </div>

                    {error && (
                        <div style={{ background: "rgba(255,80,80,0.1)", border: "1px solid rgba(255,80,80,0.3)", borderRadius: "var(--radius-md)", padding: "10px 14px", fontSize: "0.85rem", color: "#ff5050" }}>
                            {error}
                        </div>
                    )}

                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%", justifyContent: "center", marginTop: 4 }}>
                        {loading ? "Signing in…" : "Sign in →"}
                    </button>
                </form>

                <hr className="divider" />
                <p style={{ textAlign: "center", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                    No account?{" "}
                    <Link href="/register" style={{ color: "var(--emerald)", textDecoration: "none", fontWeight: 600 }}>
                        Create one
                    </Link>
                </p>
            </motion.div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={null}>
            <LoginForm />
        </Suspense>
    );
}
