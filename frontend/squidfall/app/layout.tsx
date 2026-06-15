import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/v2/styles.css";
import { Clock } from "./components/Clock";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Squidfall · Liquid Weather",
  description: "Squidfall — a liquid-glass agentic weather assistant.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <body>
        <div className="aurora" aria-hidden="true">
          <div className="blob b1" />
          <div className="blob b2" />
          <div className="blob b3" />
          <div className="blob b4" />
        </div>
        <div className="noise" aria-hidden="true" />

        <header className="topbar glass">
          <div className="brand">
            <span className="orb" />
            <span className="brand-name">SQUIDFALL</span>
            <span className="brand-sub">liquid weather</span>
          </div>
          <div className="top-right">
            <span className="pill ok">online</span>
            <Clock />
          </div>
        </header>

        <CopilotKit runtimeUrl="/api/copilotkit" agent="sample_agent">
          <main className="shell">{children}</main>
        </CopilotKit>
      </body>
    </html>
  );
}
