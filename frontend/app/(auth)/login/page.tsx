"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
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
    if (err) {
      setError(err);
      return;
    }
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
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--bg-base)",
        padding: "24px",
      }}
    >
      <div
        className="field-card"
        style={{
          width: "100%",
          maxWidth: "440px",
          backgroundColor: "#FFFFFF",
          padding: "40px",
          boxShadow: "var(--shadow-hard-lg)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
          <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "8px" }}>
            <div
              style={{
                width: 32,
                height: 32,
                backgroundColor: "#0F0F11",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 900,
                fontSize: "0.9rem",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              BA
            </div>
            <span style={{ fontWeight: 900, fontSize: "1rem", color: "#0F0F11", textTransform: "uppercase" }}>
              BharatAI
            </span>
          </Link>
          <span className="sticker-badge sticker-yellow" style={{ transform: "rotate(-2deg)", fontSize: "0.65rem" }}>
            STUDENT AUTH
          </span>
        </div>

        <h1 className="font-serif-headline" style={{ fontSize: "2.4rem", fontWeight: 400, marginBottom: "6px", lineHeight: 1.1 }}>
          Welcome back to the index.
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "28px", fontSize: "0.9rem" }}>
          Enter your credentials to access your personalized feed and Applications.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "#0F0F11",
                display: "block",
                marginBottom: "6px",
                textTransform: "uppercase",
              }}
            >
              EMAIL ADDRESS
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="student@college.edu.in"
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                backgroundColor: "#FFFFFF",
                fontSize: "0.9rem",
                outline: "none",
              }}
              required
            />
          </div>

          <div>
            <label
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "#0F0F11",
                display: "block",
                marginBottom: "6px",
                textTransform: "uppercase",
              }}
            >
              PASSWORD
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                backgroundColor: "#FFFFFF",
                fontSize: "0.9rem",
                outline: "none",
              }}
              required
            />
          </div>

          {error && (
            <div
              style={{
                backgroundColor: "#FEF2F2",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                padding: "10px 14px",
                fontSize: "0.82rem",
                color: "#DC2626",
                fontWeight: 600,
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              {error}
            </div>
          )}

          <button type="submit" className="btn-hard-primary" disabled={loading} style={{ width: "100%", justifyContent: "center", marginTop: "8px" }}>
            {loading ? "AUTHENTICATING..." : "SIGN IN ↗"}
          </button>
        </form>

        <div style={{ borderTop: "var(--border-hard)", marginTop: "28px", paddingTop: "20px", textAlign: "center" }}>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
            NO ACCOUNT YET?{" "}
            <Link href="/register" style={{ color: "#0F0F11", fontWeight: 800, textDecoration: "underline" }}>
              CREATE ONE ↗
            </Link>
          </p>
        </div>
      </div>
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
