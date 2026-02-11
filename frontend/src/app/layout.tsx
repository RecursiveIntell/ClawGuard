import type { Metadata } from "next";
import "./globals.css";
import Navigation from "@/components/navigation";

export const metadata: Metadata = {
  title: "ClawGuard",
  description: "Security scanner for AI agent skills",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-900 text-slate-100 antialiased">
        <div className="flex min-h-screen flex-col">
          <Navigation />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
            {children}
          </main>
          <footer className="border-t border-slate-800 px-4 py-4 text-center text-sm text-slate-500">
            ClawGuard v0.1.0 — Security scanner for AI agent skills
          </footer>
        </div>
      </body>
    </html>
  );
}
