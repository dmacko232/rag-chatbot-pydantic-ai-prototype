import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Telekom RAG Chatbot",
  description: "Ask questions about Deutsche Telekom press releases",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
