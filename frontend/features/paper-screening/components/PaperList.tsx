"use client";

import { useEffect, useState } from "react";

import type { Paper, PaperAIAnalysis, RelatedSignal } from "../../../lib/papers";
import { countSignals } from "../sortPapers";
import type { ActionState, PaperDecisionAction, PaperViewMode } from "../types";

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
  paperAIAnalysesByPaperId: Record<string, PaperAIAnalysis | null>;
  pendingAction: string | null;
  relatedSignals: RelatedSignal[];
  sourceErrors: string[];
  viewMode: PaperViewMode;
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

function buildArxivPdfUrl(arxivId: string | null): string | null {
  if (!arxivId) {
    return null;
  }

  return `https://arxiv.org/pdf/${arxivId}`;
}

function formatPaperDateTime(value: string | null): string {
  if (!value) {
    return "未登録";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "未登録";
  }

  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatDifficultyStars(score: number): string {
  const normalizedScore = Math.min(Math.max(Math.round(score), 1), 5);
  return "★".repeat(normalizedScore) + "☆".repeat(5 - normalizedScore);
}

function formatSignalSource(sourceType: RelatedSignal["source_type"]): string {
  const labels: Record<RelatedSignal["source_type"], string> = {
    github: "GitHub",
    qiita: "Qiita",
    hacker_news: "HN",
    reddit: "Reddit",
    x: "X",
    hugging_face: "Hugging Face",
    blog: "Blog",
    other: "Other",
  };

  return labels[sourceType] ?? sourceType;
}

function buildStructuredAnalysisItems(
  analysis: PaperAIAnalysis,
): Array<{ label: string; value: string }> {
  return [
    { label: "何の研究か", value: analysis.what_is_it_ja ?? "" },
    { label: "何が新しいか", value: analysis.novelty_ja ?? "" },
    { label: "なぜ重要か", value: analysis.why_it_matters_ja ?? "" },
    { label: "読むべき人", value: analysis.recommended_for_ja ?? "" },
  ].filter((item) => item.value.trim().length > 0);
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
  paperAIAnalysesByPaperId,
  pendingAction,
  relatedSignals,
  sourceErrors,
  viewMode,
}: PaperListProps) {
  const [isAbstractVisible, setIsAbstractVisible] = useState(false);
  const [visibleReason, setVisibleReason] = useState<
    "implementation" | "reading" | "math" | null
  >(null);
  const currentPaper = papers[currentIndex] ?? null;
  const remainingCount = papers.length;
  const currentDecision = currentPaper ? decidedActions[currentPaper.id] : undefined;
  const pdfUrl = buildArxivPdfUrl(currentPaper?.arxiv_id ?? null);
  const signalCounts = countSignals(relatedSignals);
  const isLatestPaper = currentPaper?.daily_selection_reason === "latest_arxiv";
  const isExternalArticlePaper =
    currentPaper?.daily_selection_reason === "external_article";
  const institutions = currentPaper?.institutions ?? [];
  const isPickedView = viewMode === "picked";
  const paperCardClassName = [
    "paper-card",
    "active-paper",
    isAbstractVisible ? "abstract-open" : "",
    visibleReason ? "reason-open" : "",
    isLatestPaper ? "latest-paper-card" : "",
    isExternalArticlePaper ? "external-article-paper-card" : "",
  ].filter(Boolean).join(" ");
  const selectionLabel = isLatestPaper
    ? "最新論文"
    : isExternalArticlePaper
      ? "外部記事あり"
      : null;

  useEffect(() => {
    setIsAbstractVisible(false);
    setVisibleReason(null);
  }, [currentPaper?.id]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent): void {
      if (
        isPickedView ||
        isShortcutTarget(event.target) ||
        pendingAction !== null ||
        !currentPaper
      ) {
        return;
      }

      if (!isAuthenticated) {
        return;
      }

      if (event.code === "ArrowUp") {
        event.preventDefault();
        onCreateAction(currentPaper.id, "pickup");
      }

      if (event.code === "ArrowDown") {
        event.preventDefault();
        onCreateAction(currentPaper.id, "skip");
      }

      if (event.code === "ArrowLeft") {
        event.preventDefault();
        onMovePrevious();
      }

      if (event.code === "ArrowRight") {
        event.preventDefault();
        onMoveNext();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    currentPaper,
    isAuthenticated,
    isPickedView,
    onCreateAction,
    onMoveNext,
    onMovePrevious,
    pendingAction,
  ]);

  if (papers.length === 0 || currentPaper === null) {
    return null;
  }

  if (isPickedView) {
    return (
      <section className="picked-paper-screening" aria-label="ピックアップ済み論文">
        <div className="picked-list-header">
          <p className="deck-label">Picked Papers</p>
          <p className="deck-count">{papers.length}件</p>
        </div>
        <div className="picked-paper-list">
          {papers.map((paper) => {
            const pickedPdfUrl = buildArxivPdfUrl(paper.arxiv_id);
            const pickedInstitutions = paper.institutions ?? [];
            const pickedAnalysis = paperAIAnalysesByPaperId[paper.id];

            return (
              <article className="picked-paper-row" key={paper.id}>
                <div className="paper-heading">
                  <h2>{paper.title}</h2>
                  <p className="title-translation">
                    {pickedAnalysis?.title_ja
                      ? pickedAnalysis.title_ja
                      : "日本語タイトル補助: AI分析を生成すると表示されます"}
                  </p>
                </div>
                <div className="paper-links">
                  {paper.source_url && (
                    <a href={paper.source_url} target="_blank" rel="noreferrer">
                      原文を開く
                    </a>
                  )}
                  {pickedPdfUrl && (
                    <a
                      className="paper-link-button"
                      href={pickedPdfUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      PDFを開く
                    </a>
                  )}
                  <span className="paper-meta">
                    公開: {formatPaperDateTime(paper.published_at)}
                  </span>
                  <span className="paper-meta">
                    取込: {formatPaperDateTime(paper.created_at)}
                  </span>
                  <span className="paper-meta">
                    所属: {pickedInstitutions.length > 0 ? pickedInstitutions.join(", ") : "未取得"}
                  </span>
                  <span className="paper-meta">
                    場所: {paper.location ?? "未取得"}
                  </span>
                  <span className="paper-meta">
                    {paper.arxiv_id ? `arXiv: ${paper.arxiv_id}` : "手動登録"}
                  </span>
                </div>
                {paper.authors.length > 0 && (
                  <p className="authors">{paper.authors.join(", ")}</p>
                )}
                {paper.abstract && (
                  <p className="picked-abstract">{paper.abstract}</p>
                )}
              </article>
            );
          })}
        </div>
      </section>
    );
  }

  return (
    <section className="paper-screening" aria-label="論文スクリーニング">
      <div className="screening-status">
        <div>
          <p className="deck-label">Daily Deck</p>
          <p className="deck-count">
            {currentIndex + 1} / {papers.length}
          </p>
        </div>
        <div className="deck-progress" aria-label={`残り${remainingCount}件`}>
          {papers.map((paper, index) => {
            const isCurrent = index === currentIndex;
            const decision = decidedActions[paper.id];
            const className = [
              "deck-pip",
              isCurrent ? "current" : "",
              decision === "pickup" ? "picked" : "",
              decision === "skip" ? "skipped" : "",
            ].filter(Boolean).join(" ");

            return (
              <span
                aria-label={`${index + 1}枚目${decision ? ` ${decision}` : ""}`}
                className={className}
                key={paper.id}
              />
            );
          })}
        </div>
        <p className="deck-decided">残り {remainingCount}件</p>
      </div>

      <article className={paperCardClassName}>
        <div className="paper-content">
          <div className="paper-heading">
            {selectionLabel && (
              <p className={isLatestPaper ? "selection-badge latest" : "selection-badge external"}>
                {selectionLabel}
              </p>
            )}
            <h2>{currentPaper.title}</h2>
            <p className="title-translation">
              {paperAIAnalysis?.title_ja
                ? paperAIAnalysis.title_ja
                : "日本語タイトル補助: AI分析を生成すると表示されます"}
            </p>
          </div>
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
            <span className="paper-meta">
              公開: {formatPaperDateTime(currentPaper.published_at)}
            </span>
            <span className="paper-meta">
              取込: {formatPaperDateTime(currentPaper.created_at)}
            </span>
            <span className="paper-meta">
              所属: {institutions.length > 0 ? institutions.join(", ") : "未取得"}
            </span>
            <span className="paper-meta">
              場所: {currentPaper.location ?? "未取得"}
            </span>
            <span className="paper-meta">
              {currentPaper.arxiv_id ? `arXiv: ${currentPaper.arxiv_id}` : "手動登録"}
            </span>
          </div>
          {currentPaper.authors.length > 0 && (
            <p className="authors">{currentPaper.authors.join(", ")}</p>
          )}

          {paperAIAnalysis ? (
            <section className="paper-difficulty-panel" aria-label="難易度">
              <div className="difficulty-grid">
                <div className="difficulty-item">
                  <div className="difficulty-label-row">
                    <p className="difficulty-label">実装難易度</p>
                    <button
                      aria-expanded={visibleReason === "implementation"}
                      className="reason-toggle"
                      onClick={() => setVisibleReason((reason) => (
                        reason === "implementation" ? null : "implementation"
                      ))}
                      type="button"
                    >
                      理由
                    </button>
                  </div>
                  <p className="difficulty-score">
                    <span aria-label={`${paperAIAnalysis.implementation_difficulty} / 5`}>
                      {formatDifficultyStars(paperAIAnalysis.implementation_difficulty)}
                    </span>
                  </p>
                </div>
                <div className="difficulty-item">
                  <div className="difficulty-label-row">
                    <p className="difficulty-label">読解難易度</p>
                    <button
                      aria-expanded={visibleReason === "reading"}
                      className="reason-toggle"
                      onClick={() => setVisibleReason((reason) => (
                        reason === "reading" ? null : "reading"
                      ))}
                      type="button"
                    >
                      理由
                    </button>
                  </div>
                  <p className="difficulty-score">
                    <span aria-label={`${paperAIAnalysis.reading_difficulty} / 5`}>
                      {formatDifficultyStars(paperAIAnalysis.reading_difficulty)}
                    </span>
                  </p>
                </div>
                <div className="difficulty-item">
                  <div className="difficulty-label-row">
                    <p className="difficulty-label">数学難易度</p>
                    <button
                      aria-expanded={visibleReason === "math"}
                      className="reason-toggle"
                      onClick={() => setVisibleReason((reason) => (
                        reason === "math" ? null : "math"
                      ))}
                      type="button"
                    >
                      理由
                    </button>
                  </div>
                  <p className="difficulty-score">
                    <span aria-label={`${paperAIAnalysis.math_difficulty} / 5`}>
                      {formatDifficultyStars(paperAIAnalysis.math_difficulty)}
                    </span>
                  </p>
                </div>
              </div>
              {visibleReason && (
                <p className="difficulty-reason-popover">
                  {visibleReason === "implementation"
                    ? paperAIAnalysis.implementation_reason
                    : visibleReason === "reading"
                      ? paperAIAnalysis.reading_reason
                      : paperAIAnalysis.math_reason}
                </p>
              )}
            </section>
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

          <section className="ai-analysis-panel" aria-label="AI分析">
            {paperAIAnalysis ? (
              <div className="analysis-body">
                {buildStructuredAnalysisItems(paperAIAnalysis).length > 0 && (
                  <div className="structured-analysis">
                    {buildStructuredAnalysisItems(paperAIAnalysis).map((item) => (
                      <section className="structured-analysis-item" key={item.label}>
                        <p className="structured-analysis-label">{item.label}</p>
                        <p className="structured-analysis-text">{item.value}</p>
                      </section>
                    ))}
                  </div>
                )}
                <p className="ai-summary">{paperAIAnalysis.summary_ja}</p>
              </div>
            ) : (
              <p className="ai-summary">AI分析を生成すると、ここに要約が表示されます。</p>
            )}
          </section>

          <div className="paper-subtools">
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
                  <p className="abstract expanded">{currentPaper.abstract}</p>
                )}
              </div>
            )}
            <p className="related-summary">
              関連情報: GitHub {signalCounts.githubCount} / 記事 {signalCounts.articleCount}
            </p>
          </div>

          <section className="related-signal-panel" aria-label="関連情報">
            <div className="related-signal-header">
              <p>関連情報</p>
              <p>
                GitHub {signalCounts.githubCount} / 記事 {signalCounts.articleCount}
              </p>
            </div>
            {relatedSignals.length > 0 ? (
              <ul className="related-signal-list">
                {relatedSignals.map((signal) => (
                  <li key={signal.id}>
                    <span className={`signal-source ${signal.source_type}`}>
                      {formatSignalSource(signal.source_type)}
                    </span>
                    <a href={signal.source_url} target="_blank" rel="noreferrer">
                      {signal.title}
                    </a>
                    {signal.summary && (
                      <span className="signal-summary">{signal.summary}</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="pickup-hint">
                この論文に紐づく外部リンクはまだ見つかっていません。
              </p>
            )}
          </section>

          {sourceErrors.length > 0 && (
            <p className="source-error">
              API取得失敗: {sourceErrors.join(", ")}。0件ではなく、取得できなかった可能性があります。
            </p>
          )}
        </div>

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

      <aside className="visible-action-panel" aria-label="論文操作">
        <button
          className="action-button move"
          onClick={onMovePrevious}
          type="button"
        >
          ← 前へ
        </button>
        <button
          className="action-button pickup"
          disabled={pendingAction !== null}
          onClick={() => onCreateAction(currentPaper.id, "pickup")}
          type="button"
        >
          ↑ PickUp
        </button>
        <button
          className="action-button skip"
          disabled={pendingAction !== null}
          onClick={() => onCreateAction(currentPaper.id, "skip")}
          type="button"
        >
          ↓ Skip
        </button>
        <button
          className="action-button move"
          onClick={onMoveNext}
          type="button"
        >
          次へ →
        </button>
      </aside>

    </section>
  );
}
