import type { Metadata } from "next";
import { Space_Grotesk, Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

const body = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Content Pipeline — six agents, one topic",
  description:
    "Give it a topic. Six local models research it, write it, edit it, optimize it, illustrate it, and repurpose it for social — end to end.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-screen flex flex-col bg-canvas text-ink font-body">
        <Navbar />
        <main className="flex-1 w-full">{children}</main>
        <footer className="text-center text-xs text-muted py-8 border-t border-edge mt-16">
          Runs on your own Ollama models · deploys to Azure Container Apps
        </footer>
      </body>
    </html>
  );
}
