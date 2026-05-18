"use client";

import { useEffect, useState } from "react";

type Paper = {
  id: string;
  title: string;
  abstract: string | null;
  source_url: string | null;
  arxiv_id: string | null;
  doi: string | null;
  authors: string[];
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

type PaperAction = "pickup" | "save" | "skip";

type ActionState = {
  paperId: string;
  message: string;
  isError: boolean;
} | null;

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const paperActions: Array<{ value: PaperAction; label: string }> = [
  { value: "pickup", label: "PickUp" },
  { value: "save", label: "Save" },
  { value: "skip", label: "Skip" },
];

export default function HomePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [actionState, setActionState] = useState<ActionState>(null);

  useEffect(() => {
    async function fetchPapers(): Promise<void> {
      try {
        const response = await fetch(`${API_BASE_URL}/papers`);
        if (!response.ok) {
          throw new Error(`GET /papers failed: ${response.status}`);
        }

        const data = (await response.json()) as Paper[];
        setPapers(data);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "論文一覧の取得に失敗しました";
        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    fetchPapers();
  }, []);

  async function createPaperAction(
    paperId: string,
    action: PaperAction,
  ): Promise<void> {
    setPendingAction(`${paperId}:${action}`);
    setActionState(null);

    try {
      const response = await fetch(`${API_BASE_URL}/papers/${paperId}/actions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action }),
      });

      if (!response.ok) {
        throw new Error(`POST /papers/${paperId}/actions failed: ${response.status}`);
      }

      setActionState({
        paperId,
        message: `${action} を保存しました`,
        isError: false,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "判定アクションの保存に失敗しました";
      setActionState({
        paperId,
        message,
        isError: true,
      });
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Paper Screening</p>
          <h1>ThrowAway_or_PickUp</h1>
        </div>
        <p className="api-url">{API_BASE_URL}</p>
      </section>

      {isLoading && <p className="notice">論文一覧を読み込み中です。</p>}

      {errorMessage && (
        <p className="notice error">Backend APIに接続できません: {errorMessage}</p>
      )}

      {!isLoading && !errorMessage && papers.length === 0 && (
        <p className="notice">
          論文はまだありません。backendのPOST /papersで確認用データを登録してください。
        </p>
      )}

      <section className="paper-list" aria-label="論文一覧">
        {papers.map((paper) => (
          <article className="paper-card" key={paper.id}>
            <div className="paper-content">
              <p className="paper-meta">
                {paper.arxiv_id ? `arXiv: ${paper.arxiv_id}` : "manual entry"}
              </p>
              <h2>{paper.title}</h2>
              {paper.authors.length > 0 && (
                <p className="authors">{paper.authors.join(", ")}</p>
              )}
              {paper.abstract && <p className="abstract">{paper.abstract}</p>}
              {paper.source_url && (
                <a href={paper.source_url} target="_blank" rel="noreferrer">
                  Source
                </a>
              )}
            </div>

            <div className="action-panel">
              {paperActions.map((paperAction) => {
                const pendingKey = `${paper.id}:${paperAction.value}`;
                return (
                  <button
                    className={`action-button ${paperAction.value}`}
                    disabled={pendingAction !== null}
                    key={paperAction.value}
                    onClick={() => createPaperAction(paper.id, paperAction.value)}
                    type="button"
                  >
                    {pendingAction === pendingKey ? "Saving..." : paperAction.label}
                  </button>
                );
              })}
            </div>

            {actionState?.paperId === paper.id && (
              <p className={actionState.isError ? "action-result error" : "action-result"}>
                {actionState.message}
              </p>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
