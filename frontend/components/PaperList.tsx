"use client";

import type { Paper, PaperAction } from "../lib/papers";

export type ActionState = {
  paperId: string;
  message: string;
  isError: boolean;
} | null;

type PaperListProps = {
  actionState: ActionState;
  isAuthenticated: boolean;
  onCreateAction: (paperId: string, action: PaperAction) => void;
  papers: Paper[];
  pendingAction: string | null;
};

const paperActions: Array<{ value: PaperAction; label: string }> = [
  { value: "pickup", label: "PickUp" },
  { value: "save", label: "Save" },
  { value: "skip", label: "Skip" },
];

export function PaperList({
  actionState,
  isAuthenticated,
  onCreateAction,
  papers,
  pendingAction,
}: PaperListProps) {
  return (
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
                  disabled={pendingAction !== null || !isAuthenticated}
                  key={paperAction.value}
                  onClick={() => onCreateAction(paper.id, paperAction.value)}
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
  );
}
