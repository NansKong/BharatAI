"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore, useNotifStore } from "@/lib/store";

const NAV = [
    { href: "/feed", icon: "⚡", label: "Feed" },
    { href: "/applications", icon: "📋", label: "Applications" },
    { href: "/community", icon: "💬", label: "Community" },
    { href: "/leaderboard", icon: "🏆", label: "Leaderboard" },
    { href: "/achievements", icon: "🎖️", label: "Achievements" },
    { href: "/notifications", icon: "🔔", label: "Notifications" },
    { href: "/profile", icon: "👤", label: "Profile" },
];

const ADMIN_NAV = { href: "/admin", icon: "🛡️", label: "Admin" };

export function TopNav() {
    const pathname = usePathname();
    const router = useRouter();
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const unread = useNotifStore((s) => s.unreadCount);

    const links = user?.role === "admin" ? [...NAV, ADMIN_NAV] : NAV;

    const handleLogout = () => {
        logout();
        router.push("/");
    };

    // Whether the current page has a natural "back" (everything except /feed)
    const showBack = pathname !== "/feed";

    return (
        <>
            {/* ── Top announcement bar (like Internshala) ── */}
            <div style={{
                background: "linear-gradient(90deg, #1a0a3d 0%, #2d0f6e 100%)",
                textAlign: "center", padding: "8px 24px",
                fontSize: "0.78rem", fontWeight: 500, color: "rgba(255,255,255,0.85)",
                borderBottom: "1px solid rgba(255,255,255,0.08)",
                display: "flex", alignItems: "center", justifyContent: "center", gap: 12,
            }}>
                <span style={{
                    background: "var(--emerald)", color: "#000",
                    fontSize: "0.62rem", fontWeight: 800, padding: "2px 8px",
                    borderRadius: "4px", letterSpacing: "0.05em",
                }}>NEW</span>
                Get AI-personalised opportunity ranking with{" "}
                <Link href="/profile" style={{ color: "var(--saffron)", fontWeight: 700, textDecoration: "none" }}>
                    InCoScore
                </Link>{" "}
                — Complete your profile now
            </div>

            {/* ── Main nav bar ── */}
            <header style={{
                height: 60,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0 32px",
                background: "rgba(6,14,30,0.95)",
                borderBottom: "1px solid var(--border)",
                backdropFilter: "blur(16px)",
                position: "sticky",
                top: 0,
                zIndex: 50,
            }}>
                {/* Left: Logo + back button */}
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                    <Link href="/feed" style={{ textDecoration: "none", flexShrink: 0 }}>
                        <span className="gradient-text" style={{
                            fontFamily: "Montserrat, sans-serif",
                            fontSize: "1.25rem", fontWeight: 900, letterSpacing: "-0.02em",
                        }}>
                            BharatAI
                        </span>
                    </Link>

                    {showBack && (
                        <button
                            onClick={() => router.back()}
                            style={{
                                display: "flex", alignItems: "center", gap: 5,
                                background: "rgba(255,255,255,0.05)",
                                border: "1px solid var(--border)",
                                borderRadius: "9999px",
                                padding: "5px 14px",
                                color: "var(--text-secondary)",
                                fontSize: "0.78rem", fontWeight: 500,
                                cursor: "pointer",
                                transition: "all 0.2s",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.background = "rgba(255,255,255,0.1)";
                                e.currentTarget.style.color = "var(--text-primary)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                                e.currentTarget.style.color = "var(--text-secondary)";
                            }}
                        >
                            ← Back
                        </button>
                    )}
                </div>

                {/* Center: Nav links */}
                <nav style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    {links.map(({ href, icon, label }) => {
                        const active = pathname === href || pathname.startsWith(href + "/");
                        return (
                            <Link key={href} href={href} style={{ textDecoration: "none" }}>
                                <div style={{
                                    display: "flex", alignItems: "center", gap: 6,
                                    padding: "8px 14px",
                                    borderRadius: "var(--radius-md)",
                                    color: active ? "var(--emerald)" : "var(--text-secondary)",
                                    fontWeight: active ? 700 : 500,
                                    fontSize: "0.85rem",
                                    background: active ? "rgba(0,191,165,0.1)" : "transparent",
                                    borderBottom: active ? "2px solid var(--emerald)" : "2px solid transparent",
                                    transition: "all 0.18s ease",
                                    position: "relative",
                                }}
                                    onMouseEnter={(e) => {
                                        if (!active) {
                                            e.currentTarget.style.color = "var(--text-primary)";
                                            e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!active) {
                                            e.currentTarget.style.color = "var(--text-secondary)";
                                            e.currentTarget.style.background = "transparent";
                                        }
                                    }}
                                >
                                    <span style={{ fontSize: "0.9rem" }}>{icon}</span>
                                    <span>{label}</span>
                                    {href === "/notifications" && unread > 0 && (
                                        <span style={{
                                            background: "var(--saffron)", color: "#fff",
                                            fontSize: "0.55rem", fontWeight: 800,
                                            minWidth: 16, height: 16, borderRadius: "9999px",
                                            display: "flex", alignItems: "center", justifyContent: "center",
                                            padding: "0 4px", lineHeight: 1,
                                        }}>
                                            {unread > 9 ? "9+" : unread}
                                        </span>
                                    )}
                                </div>
                            </Link>
                        );
                    })}
                </nav>

                {/* Right: user avatar + logout */}
                {user && (
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <Link href="/profile" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 8 }}>
                            <div style={{
                                width: 34, height: 34, borderRadius: "50%",
                                background: "linear-gradient(135deg, var(--saffron), var(--emerald))",
                                display: "flex", alignItems: "center", justifyContent: "center",
                                fontWeight: 800, fontSize: "0.82rem", color: "#fff", flexShrink: 0,
                                boxShadow: "0 0 0 2px rgba(0,191,165,0.3)",
                            }}>
                                {user.name.charAt(0).toUpperCase()}
                            </div>
                            <div style={{ display: "flex", flexDirection: "column" }}>
                                <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.2 }}>
                                    {user.name.split(" ")[0]}
                                </span>
                                <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "capitalize" }}>
                                    {user.role}
                                </span>
                            </div>
                        </Link>

                        <button
                            onClick={handleLogout}
                            style={{
                                background: "transparent",
                                border: "1px solid var(--border)",
                                borderRadius: "var(--radius-md)",
                                padding: "6px 14px",
                                color: "var(--text-secondary)",
                                fontSize: "0.78rem", fontWeight: 500,
                                cursor: "pointer",
                                transition: "all 0.2s",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = "rgba(255,80,80,0.4)";
                                e.currentTarget.style.color = "#ff5050";
                                e.currentTarget.style.background = "rgba(255,80,80,0.08)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = "var(--border)";
                                e.currentTarget.style.color = "var(--text-secondary)";
                                e.currentTarget.style.background = "transparent";
                            }}
                        >
                            Sign out
                        </button>
                    </div>
                )}
            </header>
        </>
    );
}

// Keep Sidebar export as an alias for backward compat
export { TopNav as Sidebar };
