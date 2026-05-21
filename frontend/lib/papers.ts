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

type ArxivImportResponse = {
  imported_count: number;
  papers: Paper[];
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

export async function importArxivPapers(): Promise<Paper[]> {
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
