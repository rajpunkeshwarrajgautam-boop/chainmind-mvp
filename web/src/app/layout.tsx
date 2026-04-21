import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChainMind",
  description: "Supply chain intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
