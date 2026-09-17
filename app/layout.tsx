import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Matinê",
  description: "Seu espaço pessoal para descobrir, organizar e escolher o que assistir.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
