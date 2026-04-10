import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "PosturePal - Wellness Monitor",
  description: "AI Wellness Companion",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className={`${inter.variable} font-sans text-[var(--text-primary)] flex`}>
        <Sidebar className="print:hidden"/>
        <main className="flex-1 ml-[var(--sidebar-expanded)] transition-all duration-300 min-h-screen">
          <div className="max-w-[1280px] mx-auto p-8 lg:p-12">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
