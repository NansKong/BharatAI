"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore, useNotifStore } from "@/lib/store";

const BASE_NAV = [
  { href: "/", label: "INDEX" },
  { href: "/opportunities", label: "OPPORTUNITIES" },
  { href: "/internships", label: "INTERNSHIPS" },
  { href: "/leaderboard", label: "INCOSCORE" },
  { href: "/community", label: "COMMUNITY" },
];

const AUTH_NAV = [
  { href: "/feed", label: "MY FEED" },
  { href: "/applications", label: "APPLICATIONS" },
  { href: "/notifications", label: "NOTIFS" },
];

const ADMIN_NAV = { href: "/admin", label: "ADMIN" };

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const unread = useNotifStore((s) => s.unreadCount);

  const links = user
    ? [...BASE_NAV, ...AUTH_NAV, ...(user.role === "admin" ? [ADMIN_NAV] : [])]
    : BASE_NAV;

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <header
      style={{
        height: 64,
        borderBottom: "var(--border-hard)",
        padding: "0 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        backgroundColor: "var(--bg-base)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Left: Logo Badge */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: 36,
              height: 36,
              backgroundColor: "#0F0F11",
              color: "#FFFFFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "1.05rem",
              borderRadius: "4px",
              fontFamily: "'JetBrains Mono', monospace",
              boxShadow: "var(--shadow-hard-sm)",
            }}
          >
            BA
          </div>
          <div>
            <span style={{ fontWeight: 900, fontSize: "1rem", letterSpacing: "-0.02em", color: "#0F0F11", textTransform: "uppercase" }}>
              BharatAI
            </span>
            <div style={{ fontSize: "0.58rem", fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)", letterSpacing: "0.08em" }}>
              ACADEMIC OPPORTUNITY INDEX
            </div>
          </div>
        </Link>
      </div>

      {/* Center: Nav links */}
      <nav style={{ display: "flex", alignItems: "center", gap: "4px" }}>
        {links.map(({ href, label }) => {
          const active = href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href} style={{ textDecoration: "none" }}>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: active ? "#0F0F11" : "transparent",
                  color: active ? "#FFFFFF" : "#0F0F11",
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  letterSpacing: "0.04em",
                  border: active ? "1px solid #0F0F11" : "1px solid transparent",
                  transition: "all 0.15s ease",
                }}
              >
                {label}
                {href === "/notifications" && unread > 0 && (
                  <span
                    style={{
                      backgroundColor: "var(--yellow-accent)",
                      color: "#0F0F11",
                      fontSize: "0.6rem",
                      fontWeight: 800,
                      padding: "1px 5px",
                      borderRadius: "50%",
                      border: "1px solid #0F0F11",
                    }}
                  >
                    {unread > 9 ? "9+" : unread}
                  </span>
                )}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Right: User / Auth actions */}
      {user ? (
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link href="/profile" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "8px" }}>
            <div className="num-circle" style={{ backgroundColor: "var(--yellow-accent)", width: 32, height: 32, fontSize: "0.82rem" }}>
              {user.name.charAt(0).toUpperCase()}
            </div>
            <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0F0F11", fontFamily: "'JetBrains Mono', monospace" }}>
              {user.name.split(" ")[0]}
            </span>
          </Link>

          <button type="button" onClick={handleLogout} className="btn-hard-secondary" style={{ padding: "6px 12px", fontSize: "0.68rem" }}>
            LOGOUT ↗
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", gap: "8px" }}>
          <Link href="/login" className="btn-hard-secondary" style={{ padding: "6px 14px", fontSize: "0.7rem" }}>
            LOGIN
          </Link>
          <Link href="/register" className="btn-hard-primary" style={{ padding: "6px 14px", fontSize: "0.7rem" }}>
            JOIN INDEX ↗
          </Link>
        </div>
      )}
    </header>
  );
}

export { TopNav as Sidebar };
