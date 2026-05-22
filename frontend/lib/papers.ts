export type Paper = {
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

export type PaperAction = "pickup" | "save" | "skip";

export type RelatedSignalSourceType =
  | "github"
  | "qiita"
  | "hacker_news"
  | "reddit"
  | "x"
  | "hugging_face"
  | "blog"
  | "other";

export type RelatedSignal = {
  id: string;
  paper_id: string;
  source_type: RelatedSignalSourceType;
  title: string;
  source_url: string;
  summary: string | null;
  published_at: string | null;
  raw_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type ArxivImportResponse = {
  imported_count: number;
  papers: Paper[];
};

type RelatedSignalDiscoveryResponse = {
  discovered_count: number;
  signals: RelatedSignal[];
  source_errors: string[];
};

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchPapers(): Promise<Paper[]> {
  const response = await fetch(`${API_BASE_URL}/papers`);
  if (!response.ok) {
    throw new Error(`GET /papers failed: ${response.status}`);
  }

  return (await response.json()) as Paper[];
}

export async function createPaperAction(
  paperId: string,
  action: PaperAction,
  accessToken: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}/actions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action }),
  });

  if (!response.ok) {
    throw new Error(`POST /papers/${paperId}/actions failed: ${response.status}`);
  }
}

export async function importNewPapers(): Promise<Paper[]> {
  const response = await fetch(`${API_BASE_URL}/papers/import/arxiv`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      search_query: "cat:cs.AI",
      max_results: 10,
    }),
  });

  if (!response.ok) {
    throw new Error(`POST /papers/import/arxiv failed: ${response.status}`);
  }

  const data = (await response.json()) as ArxivImportResponse;
  return data.papers;
}

export async function fetchRelatedSignals(paperId: string): Promise<RelatedSignal[]> {
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}/related-signals`);
  if (!response.ok) {
    throw new Error(`GET /papers/${paperId}/related-signals failed: ${response.status}`);
  }

  return (await response.json()) as RelatedSignal[];
}

export async function discoverRelatedSignals(
  paperId: string,
): Promise<RelatedSignalDiscoveryResponse> {
  const response = await fetch(
    `${API_BASE_URL}/papers/${paperId}/related-signals/discover`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(
      `POST /papers/${paperId}/related-signals/discover failed: ${response.status}`,
    );
  }

  return (await response.json()) as RelatedSignalDiscoveryResponse;
}
