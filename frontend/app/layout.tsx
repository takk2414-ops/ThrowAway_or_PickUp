import type { Metadata } from "next";
import "./globals.css";

// Next.jsがページの <title> や説明文に使うメタデータです。
export const metadata: Metadata = {
  title: "ThrowAway_or_PickUp",
  description: "Japanese-first paper screening app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // すべてのページに共通するHTMLの土台です。
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
