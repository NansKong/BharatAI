import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div style={{ minHeight: "100vh", background: "var(--bg-base)" }}>
            <Sidebar />
            <main style={{ padding: "32px 40px", maxWidth: 1240, margin: "0 auto" }}>
                {children}
            </main>
        </div>
    );
}
