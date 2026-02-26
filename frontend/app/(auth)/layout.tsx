// Auth pages don't use the dashboard layout (no sidebar/header)
export default function AuthLayout({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
}
