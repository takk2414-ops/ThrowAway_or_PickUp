"use client";

import { useEffect } from "react";

import type { Paper, RelatedSignal } from "../../../lib/papers";
import { countSignals } from "../sortPapers";
import type { ActionState, PaperDecisionAction } from "../types";

type PaperListProps = {
  actionState: ActionState;
  currentIndex: number;
  decidedActions: Record<string, PaperDecisionAction>;
  isAuthenticated: boolean;
  isDiscoveringSignals: boolean;
  onCreateAction: (paperId: string, action: PaperDecisionAction) => void;
  onDiscoverSignals: (paperId: string) => void;
  onMoveNext: () => void;
  onMovePrevious: () => void;
  papers: Paper[];
  pendingAction: string | null;
  relatedSignals: RelatedSignal[];
  sourceErrors: string[];
};

function isShortcutTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  const tagName = target.tagName.toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select" ||
    target.isContentEditable
  );
}

export function PaperList({
  actionState,
  currentIndex,
  decidedActions,
  isAuthenticated,
  isDiscoveringSignals,
  onCreateAction,
  onDiscoverSignals,
  onMoveNext,
  onMovePrevious,
  papers,
  pendingAction,
  relatedSignals,
  sourceErrors,
}: PaperListProps) {
  const currentPaper = papers[currentIndex] ?? null;
  const decidedCount = papers.filter((paper) => decidedActions[paper.id]).length;
  const isCompleted = papers.length > 0 && decidedCount >= papers.length;
  const currentDecision = currentPaper ? decidedActions[currentPaper.id] : undefined;
  const signalCounts = countSignals(relatedSignals);
  const pickupHint =
    signalCounts.githubCount > 0 && signalCounts.articleCount > 0
      ? "GitHub実装と日本語記事が見つかっています。実装確認やキャッチアップ目的ならPickUp候補です。"
      : relatedSignals.length > 0
        ? "周辺情報が見つかっています。リンク先の実装や解説を確認してから判断できます。"
        : "周辺情報はまだありません。Find signalsでGitHub/Qiitaを探索できます。";

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (isShortcutTarget(event.target) || pendingAction !== null || !currentPaper) {
        return;
      }

      if (event.code === "ArrowUp") {
        event.preventDefault();
        onMovePrevious();
      }

      if (event.code === "ArrowDown") {
        event.preventDefault();
        onMoveNext();
      }

      if (!isAuthenticated) {
        return;
      }

      if (event.code === "ArrowLeft") {
        event.preventDefault();
        onCreateAction(currentPaper.id, "pickup");
      }

      if (event.code === "ArrowRight") {
        event.preventDefault();
        onCreateAction(currentPaper.id, "skip");
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    currentPaper,
    isAuthenticated,
    onCreateAction,
    onMoveNext,
    onMovePrevious,
    pendingAction,
  ]);

  if (papers.length === 0 || currentPaper === null) {
    return null;
  }

  return (
    <section className="paper-screening" aria-label="論文スクリーニング">
      <div className="screening-status">
        <p>
          {currentIndex + 1} / {papers.length}
        </p>
        <p>{decidedCount}件 判定済み</p>
      </div>

      <article className="paper-card active-paper">
        <div className="paper-content">
          <p className="paper-meta">
            {currentPaper.arxiv_id ? `arXiv: ${currentPaper.arxiv_id}` : "manual entry"}
          </p>
          <h2>{currentPaper.title}</h2>
          {currentPaper.authors.length > 0 && (
            <p className="authors">{currentPaper.authors.join(", ")}</p>
          )}
          {currentPaper.abstract && <p className="abstract">{currentPaper.abstract}</p>}
          {currentPaper.source_url && (
            <a href={currentPaper.source_url} target="_blank" rel="noreferrer">
              Source
            </a>
          )}
        </div>

        <div className="action-panel screening-controls">
          <button
            className="action-button pickup"
            disabled={pendingAction !== null || !isAuthenticated}
            onClick={() => onCreateAction(currentPaper.id, "pickup")}
            type="button"
          >
            ← PickUp
          </button>
          <button
            className="action-button"
            disabled={pendingAction !== null || currentIndex === 0}
            onClick={onMovePrevious}
            type="button"
          >
            ↑ Previous
          </button>
          <button
            className="action-button"
            disabled={pendingAction !== null || currentIndex >= papers.length - 1}
            onClick={onMoveNext}
            type="button"
          >
            ↓ Next
          </button>
          <button
            className="action-button skip"
            disabled={pendingAction !== null || !isAuthenticated}
            onClick={() => onCreateAction(currentPaper.id, "skip")}
            type="button"
          >
            → Skip
          </button>
          <button
            className="action-button"
            disabled={pendingAction !== null || isDiscoveringSignals}
            onClick={() => onDiscoverSignals(currentPaper.id)}
            type="button"
          >
            {isDiscoveringSignals ? "Finding..." : "Find signals"}
          </button>
        </div>

        <section className="related-signal-panel" aria-label="関連シグナル">
          <div className="related-signal-header">
            <p>Related Signals</p>
            <p>
              GitHub {signalCounts.githubCount} / Articles {signalCounts.articleCount}
            </p>
          </div>
          <p className="pickup-hint">{pickupHint}</p>
          {sourceErrors.length > 0 && (
            <p className="source-error">
              API取得失敗: {sourceErrors.join(", ")}。0件ではなく、取得できなかった可能性があります。
            </p>
          )}
          {relatedSignals.length > 0 && (
            <ul className="related-signal-list">
              {relatedSignals.map((signal) => (
                <li key={signal.id}>
                  <span className={`signal-source ${signal.source_type}`}>
                    {signal.source_type}
                  </span>
                  <a href={signal.source_url} target="_blank" rel="noreferrer">
                    {signal.title}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>

        {currentDecision && (
          <p className="decision-badge">
            {currentDecision === "pickup" ? "PickUp済み" : "Skip済み"}
          </p>
        )}

        {actionState?.paperId === currentPaper.id && (
          <p className={actionState.isError ? "action-result error" : "action-result"}>
            {actionState.message}
          </p>
        )}
      </article>

      {isCompleted && (
        <p className="notice success">
          {papers.length}件すべてを PickUp / Skip で判定しました。
        </p>
      )}
    </section>
  );
}
