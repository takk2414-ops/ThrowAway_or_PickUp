"use client";

type GlobalErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function GlobalErrorPage({
  error,
  reset,
}: GlobalErrorPageProps) {
  return (
    <html lang="ja">
      <body>
        <main className="page-shell">
          <section className="notice error operational-error" aria-label="エラー">
            <p className="error-title">アプリ全体の表示中にエラーが発生しました</p>
            <p>{error.message}</p>
            <button className="secondary-button" onClick={reset} type="button">
              再読み込み
            </button>
          </section>
        </main>
      </body>
    </html>
  );
}
