import type { Metadata } from "next";

import "@fontsource-variable/inter";
import { AppShell } from "@/components/shell/AppShell";

import "./globals.css";

export const metadata: Metadata = {
  title: "TalentFlow AI — Hiring Pipeline",
  description:
    "Open-source AI-native hiring pipeline with explainable candidate matching. AI assists; recruiters decide.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
