"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
    if (err) {
      setError(err);
      return;
    }
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
        msg = detail.map((d: { msg?: string }) => d.msg ?? "").filter(Boolean).join(". ") || msg;
      }
      setError(msg);
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
          maxWidth: "460px",
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
          <span className="sticker-badge sticker-teal" style={{ transform: "rotate(2deg)", fontSize: "0.65rem" }}>
            NEW MEMBER
          </span>
        </div>

        <h1 className="font-serif-headline" style={{ fontSize: "2.4rem", fontWeight: 400, marginBottom: "6px", lineHeight: 1.1 }}>
          Create your profile.
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "24px", fontSize: "0.88rem" }}>
          Join the academic index to unlock personalized opportunity feeds.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.7rem",
                fontWeight: 700,
                color: "#0F0F11",
                display: "block",
                marginBottom: "4px",
                textTransform: "uppercase",
              }}
            >
              FULL NAME
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Priya Sharma"
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                backgroundColor: "#FFFFFF",
                fontSize: "0.88rem",
                outline: "none",
              }}
              required
            />
          </div>

          <div>
            <label
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.7rem",
                fontWeight: 700,
                color: "#0F0F11",
                display: "block",
                marginBottom: "4px",
                textTransform: "uppercase",
              }}
            >
              EMAIL ADDRESS
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="priya@example.com"
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                backgroundColor: "#FFFFFF",
                fontSize: "0.88rem",
                outline: "none",
              }}
              required
            />
          </div>

          <div>
            <label
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.7rem",
                fontWeight: 700,
                color: "#0F0F11",
                display: "block",
                marginBottom: "4px",
                textTransform: "uppercase",
              }}
            >
              PASSWORD
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 chars, 1 uppercase, 1 number"
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                backgroundColor: "#FFFFFF",
                fontSize: "0.88rem",
                outline: "none",
              }}
              required
            />
          </div>

          <div>
            <label
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "0.7rem",
                fontWeight: 700,
                color: "#0F0F11",
                display: "block",
                marginBottom: "4px",
                textTransform: "uppercase",
              }}
            >
              COLLEGE / INSTITUTION (OPTIONAL)
            </label>
            <input
              type="text"
              value={college}
              onChange={(e) => setCollege(e.target.value)}
              placeholder="IIT Bombay, IISc, BITS Pilani..."
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "var(--border-hard)",
                borderRadius: "var(--radius-box)",
                backgroundColor: "#FFFFFF",
                fontSize: "0.88rem",
                outline: "none",
              }}
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
            {loading ? "CREATING PROFILE..." : "CREATE ACCOUNT ↗"}
          </button>
        </form>

        <div style={{ borderTop: "var(--border-hard)", marginTop: "24px", paddingTop: "18px", textAlign: "center" }}>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
            ALREADY REGISTERED?{" "}
            <Link href="/login" style={{ color: "#0F0F11", fontWeight: 800, textDecoration: "underline" }}>
              SIGN IN ↗
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
