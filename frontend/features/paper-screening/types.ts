import type { PaperAction } from "../../lib/papers";

export type PaperDecisionAction = Extract<PaperAction, "pickup" | "skip">;

export type SortKey = "new" | "github" | "articles" | "signals";

export type ActionState = {
  paperId: string;
  message: string;
  isError: boolean;
} | null;
