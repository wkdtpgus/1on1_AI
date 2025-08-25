import type { Metadata } from "next";
import Header from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "1on1 AI Meeting Assistant",
  description: "AI를 활용한 효율적인 1on1 미팅 준비 및 관리",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="bg-gray-50 text-gray-800">
        <Header />
        <main className="container mx-auto p-6">
          {children}
        </main>
      </body>
    </html>
  );
}
