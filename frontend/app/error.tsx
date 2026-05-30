"use client";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return (
    <main className="page-shell">
      <section className="notice error operational-error" aria-label="エラー">
        <p className="error-title">画面の表示中にエラーが発生しました</p>
        <p>{error.message}</p>
        <button className="secondary-button" onClick={reset} type="button">
          再読み込み
        </button>
      </section>
    </main>
  );
}
