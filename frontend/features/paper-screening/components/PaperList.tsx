"use client";

import { useEffect, useState } from "react";

import type { Paper, PaperAIAnalysis, RelatedSignal } from "../../../lib/papers";
import { countSignals } from "../sortPapers";
import type { ActionState, PaperDecisionAction } from "../types";

type PaperListProps = {
  actionState: ActionState;
  currentIndex: number;
  decidedActions: Record<string, PaperDecisionAction>;
  isAuthenticated: boolean;
  isGeneratingAnalysis: boolean;
  onCreateAction: (paperId: string, action: PaperDecisionAction) => void;
  onGenerateAnalysis: (paperId: string) => void;
  onMoveNext: () => void;
  onMovePrevious: () => void;
  papers: Paper[];
  paperAIAnalysis: PaperAIAnalysis | null | undefined;
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

function formatSignalSource(sourceType: RelatedSignal["source_type"]): string {
  const sourceLabels: Record<RelatedSignal["source_type"], string> = {
    github: "GitHub",
    qiita: "Qiita",
    hacker_news: "Hacker News",
    reddit: "Reddit",
    x: "X",
    hugging_face: "Hugging Face",
    blog: "ブログ",
    other: "その他",
  };

  return sourceLabels[sourceType];
}

function buildArxivPdfUrl(arxivId: string | null): string | null {
  if (!arxivId) {
    return null;
  }

  return `https://arxiv.org/pdf/${arxivId}`;
}

function formatDifficultyStars(score: number): string {
  const normalizedScore = Math.min(Math.max(Math.round(score), 1), 5);
  return "★".repeat(normalizedScore) + "☆".repeat(5 - normalizedScore);
}

export function PaperList({
  actionState,
  currentIndex,
  decidedActions,
  isAuthenticated,
  isGeneratingAnalysis,
  onCreateAction,
  onGenerateAnalysis,
  onMoveNext,
  onMovePrevious,
  papers,
  paperAIAnalysis,
  pendingAction,
  relatedSignals,
  sourceErrors,
}: PaperListProps) {
  const [isAbstractVisible, setIsAbstractVisible] = useState(false);
  const currentPaper = papers[currentIndex] ?? null;
  const decidedCount = papers.filter((paper) => decidedActions[paper.id]).length;
  const isCompleted = papers.length > 0 && decidedCount >= papers.length;
  const currentDecision = currentPaper ? decidedActions[currentPaper.id] : undefined;
  const pdfUrl = buildArxivPdfUrl(currentPaper?.arxiv_id ?? null);
  const signalCounts = countSignals(relatedSignals);
  const isLatestPaper = currentPaper?.daily_selection_reason === "latest_arxiv";
  const isExternalArticlePaper =
    currentPaper?.daily_selection_reason === "external_article";
  const paperCardClassName = [
    "paper-card",
    "active-paper",
    isLatestPaper ? "latest-paper-card" : "",
    isExternalArticlePaper ? "external-article-paper-card" : "",
  ].filter(Boolean).join(" ");
  const selectionLabel = isLatestPaper
    ? "最新論文"
    : isExternalArticlePaper
      ? "外部記事あり"
      : null;
  const pickupHint =
    signalCounts.githubCount > 0 && signalCounts.articleCount > 0
      ? "GitHub実装と日本語記事が見つかっています。実装確認やキャッチアップ目的ならPickUp候補です。"
      : relatedSignals.length > 0
        ? "周辺情報が見つかっています。リンク先の実装や解説を確認してから判断できます。"
        : "周辺情報はまだありません。最新枠として表示されています。";

  useEffect(() => {
    setIsAbstractVisible(false);
  }, [currentPaper?.id]);

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

      <article className={paperCardClassName}>
        <div className="paper-content">
          {selectionLabel && (
            <p className={isLatestPaper ? "selection-badge latest" : "selection-badge external"}>
              {selectionLabel}
            </p>
          )}
          <p className="paper-meta">
            {currentPaper.arxiv_id ? `arXiv: ${currentPaper.arxiv_id}` : "手動登録"}
          </p>
          <h2>{currentPaper.title}</h2>
          {currentPaper.authors.length > 0 && (
            <p className="authors">{currentPaper.authors.join(", ")}</p>
          )}
          {(currentPaper.source_url || pdfUrl) && (
            <div className="paper-links">
              {currentPaper.source_url && (
                <a href={currentPaper.source_url} target="_blank" rel="noreferrer">
                  原文を開く
                </a>
              )}
              {pdfUrl && (
                <a
                  className="paper-link-button"
                  href={pdfUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  PDFを開く
                </a>
              )}
            </div>
          )}
          {currentPaper.abstract && (
            <div className="abstract-panel">
              <button
                className="secondary-button abstract-toggle"
                onClick={() => setIsAbstractVisible((visible) => !visible)}
                type="button"
              >
                {isAbstractVisible ? "Abstractを隠す" : "Abstractを表示"}
              </button>
              {isAbstractVisible && (
                <p className="abstract">{currentPaper.abstract}</p>
              )}
            </div>
          )}
        </div>

        <div className="action-panel screening-controls">
          <button
            className="action-button pickup"
            disabled={pendingAction !== null || !isAuthenticated}
            onClick={() => onCreateAction(currentPaper.id, "pickup")}
            type="button"
          >
            ← ピックアップ
          </button>
          <button
            className="action-button"
            disabled={pendingAction !== null || currentIndex === 0}
            onClick={onMovePrevious}
            type="button"
          >
            ↑ 前の論文
          </button>
          <button
            className="action-button"
            disabled={pendingAction !== null || currentIndex >= papers.length - 1}
            onClick={onMoveNext}
            type="button"
          >
            ↓ 次の論文
          </button>
          <button
            className="action-button skip"
            disabled={pendingAction !== null || !isAuthenticated}
            onClick={() => onCreateAction(currentPaper.id, "skip")}
            type="button"
          >
            → スキップ
          </button>
        </div>

        <section className="ai-analysis-panel" aria-label="AI分析">
          <div className="ai-analysis-header">
            <p>AI分析</p>
            {paperAIAnalysis && (
              <p>{paperAIAnalysis.provider} / {paperAIAnalysis.model}</p>
            )}
          </div>

          {paperAIAnalysis ? (
            <>
              <p className="ai-summary">{paperAIAnalysis.summary_ja}</p>
              <div className="difficulty-grid">
                <div className="difficulty-item">
                  <p className="difficulty-label">実装難易度</p>
                  <p className="difficulty-score">
                    <span aria-label={`${paperAIAnalysis.implementation_difficulty} / 5`}>
                      {formatDifficultyStars(paperAIAnalysis.implementation_difficulty)}
                    </span>
                  </p>
                  <p className="difficulty-reason">
                    {paperAIAnalysis.implementation_reason}
                  </p>
                </div>
                <div className="difficulty-item">
                  <p className="difficulty-label">読解難易度</p>
                  <p className="difficulty-score">
                    <span aria-label={`${paperAIAnalysis.reading_difficulty} / 5`}>
                      {formatDifficultyStars(paperAIAnalysis.reading_difficulty)}
                    </span>
                  </p>
                  <p className="difficulty-reason">
                    {paperAIAnalysis.reading_reason}
                  </p>
                </div>
                <div className="difficulty-item">
                  <p className="difficulty-label">数学難易度</p>
                  <p className="difficulty-score">
                    <span aria-label={`${paperAIAnalysis.math_difficulty} / 5`}>
                      {formatDifficultyStars(paperAIAnalysis.math_difficulty)}
                    </span>
                  </p>
                  <p className="difficulty-reason">
                    {paperAIAnalysis.math_reason}
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="ai-analysis-empty">
              <p>AI分析はまだ生成されていません。</p>
              <button
                className="secondary-button"
                disabled={isGeneratingAnalysis}
                onClick={() => onGenerateAnalysis(currentPaper.id)}
                type="button"
              >
                {isGeneratingAnalysis ? "生成中..." : "AI分析を生成"}
              </button>
            </div>
          )}
        </section>

        <section className="related-signal-panel" aria-label="関連シグナル">
          <div className="related-signal-header">
            <p>関連情報</p>
            <p>
              GitHub {signalCounts.githubCount} / 記事 {signalCounts.articleCount}
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
                    {formatSignalSource(signal.source_type)}
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
            {currentDecision === "pickup" ? "ピックアップ済み" : "スキップ済み"}
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
          {papers.length}件すべてをピックアップ/スキップで判定しました。
        </p>
      )}
    </section>
  );
}
