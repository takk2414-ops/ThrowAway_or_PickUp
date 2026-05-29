import type { PaperAction } from "../../lib/papers";

export type PaperDecisionAction = Extract<PaperAction, "pickup" | "skip">;

export type PaperViewMode = "today" | "picked";

export type ActionState = {
  paperId: string;
  message: string;
  isError: boolean;
} | null;
