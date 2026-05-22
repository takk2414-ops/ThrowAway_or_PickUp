import type { Paper, RelatedSignal } from "../../lib/papers";
import type { SortKey } from "./types";

export type SignalCounts = {
  articleCount: number;
  articleScore: number;
  githubCount: number;
  githubScore: number;
  totalCount: number;
};

export const SORT_OPTIONS: Array<{ key: SortKey; label: string }> = [
  { key: "new", label: "New" },
  { key: "github", label: "GitHub" },
  { key: "articles", label: "Articles" },
  { key: "signals", label: "Signals" },
];

function readNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function getPaperTimestamp(paper: Paper): number {
  const timestamp = Date.parse(paper.published_at ?? paper.created_at);
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

export function countSignals(signals: RelatedSignal[]): SignalCounts {
  return signals.reduce<SignalCounts>(
    (counts, signal) => {
      if (signal.source_type === "github") {
        return {
          ...counts,
          githubCount: counts.githubCount + 1,
          githubScore: counts.githubScore + readNumber(signal.raw_metadata.stars),
          totalCount: counts.totalCount + 1,
        };
      }

      if (signal.source_type === "qiita") {
        return {
          ...counts,
          articleCount: counts.articleCount + 1,
          articleScore:
            counts.articleScore
            + readNumber(signal.raw_metadata.likes_count)
            + readNumber(signal.raw_metadata.stocks_count),
          totalCount: counts.totalCount + 1,
        };
      }

      return {
        ...counts,
        totalCount: counts.totalCount + 1,
      };
    },
    {
      articleCount: 0,
      articleScore: 0,
      githubCount: 0,
      githubScore: 0,
      totalCount: 0,
    },
  );
}

export function sortPapers(
  papers: Paper[],
  relatedSignals: Record<string, RelatedSignal[]>,
  sortKey: SortKey,
): Paper[] {
  return [...papers].sort((leftPaper, rightPaper) => {
    const leftCounts = countSignals(relatedSignals[leftPaper.id] ?? []);
    const rightCounts = countSignals(relatedSignals[rightPaper.id] ?? []);
    const leftTimestamp = getPaperTimestamp(leftPaper);
    const rightTimestamp = getPaperTimestamp(rightPaper);

    if (sortKey === "github") {
      return (
        rightCounts.githubCount - leftCounts.githubCount
        || rightCounts.githubScore - leftCounts.githubScore
        || rightTimestamp - leftTimestamp
      );
    }

    if (sortKey === "articles") {
      return (
        rightCounts.articleCount - leftCounts.articleCount
        || rightCounts.articleScore - leftCounts.articleScore
        || rightTimestamp - leftTimestamp
      );
    }

    if (sortKey === "signals") {
      return (
        rightCounts.totalCount - leftCounts.totalCount
        || rightCounts.githubCount - leftCounts.githubCount
        || rightCounts.articleCount - leftCounts.articleCount
        || rightTimestamp - leftTimestamp
      );
    }

    return rightTimestamp - leftTimestamp;
  });
}
