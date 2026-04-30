import type { Metadata } from "next";

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
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
