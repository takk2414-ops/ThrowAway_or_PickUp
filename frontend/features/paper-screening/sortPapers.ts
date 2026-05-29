import type { RelatedSignal } from "../../lib/papers";

export type SignalCounts = {
  articleCount: number;
  articleScore: number;
  githubCount: number;
  githubScore: number;
  totalCount: number;
};

function readNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
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
