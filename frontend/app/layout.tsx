import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "BharatAI — Opportunities for Every Indian Student",
  description:
    "AI-powered platform connecting Indian students with scholarships, internships, competitions, and fellowships. Personalized feed, InCoScore leaderboard, and community.",
  keywords: ["scholarships", "internships", "students", "India", "AI", "opportunities"],
  openGraph: {
    title: "BharatAI",
    description: "Opportunities for Every Indian Student",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
