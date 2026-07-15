import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Video RAG Chatbot",
  description: "Chat with your videos using AI and RAG",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
