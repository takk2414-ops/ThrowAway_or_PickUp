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
  daily_selection_reason: "latest_arxiv" | "external_article" | string | null;
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

export type PaperAIAnalysis = {
  id: string;
  paper_id: string;
  provider: "openai" | "gemini" | string;
  model: string;
  summary_ja: string;
  implementation_difficulty: number;
  implementation_reason: string;
  reading_difficulty: number;
  reading_reason: string;
  math_difficulty: number;
  math_reason: string;
  raw_response: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type PickedPapersExport = {
  pdf_urls: string[];
  markdown_note: string;
  notebooklm_prompt: string;
  warnings: string[];
};

type DailyImportResponse = {
  import_date: string;
  imported_count: number;
  papers: Paper[];
  skipped: boolean;
  ai_analysis_generated_count: number;
  ai_analysis_failed_count: number;
};

type RelatedSignalDiscoveryResponse = {
  discovered_count: number;
  signals: RelatedSignal[];
  source_errors: string[];
};

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  endpoint: string;
  status: number;
  detail: string | null;

  constructor(endpoint: string, status: number, detail: string | null) {
    super(`${endpoint} failed: ${status}`);
    this.name = "ApiError";
    this.endpoint = endpoint;
    this.status = status;
    this.detail = detail;
  }
}

async function readApiErrorDetail(response: Response): Promise<string | null> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") {
      return data.detail;
    }
  } catch {
    return null;
  }

  return null;
}

async function throwApiError(response: Response, endpoint: string): Promise<never> {
  throw new ApiError(endpoint, response.status, await readApiErrorDetail(response));
}

export async function fetchPapers(): Promise<Paper[]> {
  const endpoint = "GET /papers";
  const response = await fetch(`${API_BASE_URL}/papers`);
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as Paper[];
}

export async function fetchTodayPapers(): Promise<Paper[]> {
  const endpoint = "GET /papers/today";
  const response = await fetch(`${API_BASE_URL}/papers/today`);
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as Paper[];
}

export async function fetchPickedPapers(accessToken: string): Promise<Paper[]> {
  const endpoint = "GET /papers/picked";
  const response = await fetch(`${API_BASE_URL}/papers/picked`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as Paper[];
}

export async function fetchPickedPapersExport(
  accessToken: string,
): Promise<PickedPapersExport> {
  const endpoint = "GET /papers/picked/export";
  const response = await fetch(`${API_BASE_URL}/papers/picked/export`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as PickedPapersExport;
}

export async function fetchPickedPapersPdfZip(accessToken: string): Promise<Blob> {
  const endpoint = "GET /papers/picked/export/pdf-zip";
  const response = await fetch(`${API_BASE_URL}/papers/picked/export/pdf-zip`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return await response.blob();
}

export async function createPaperAction(
  paperId: string,
  action: PaperAction,
  accessToken: string,
): Promise<void> {
  const endpoint = `POST /papers/${paperId}/actions`;
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}/actions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action }),
  });

  if (!response.ok) {
    await throwApiError(response, endpoint);
  }
}

export async function ensureTodayPapers(): Promise<Paper[]> {
  const endpoint = "POST /papers/import/daily";
  const response = await fetch(`${API_BASE_URL}/papers/import/daily`, {
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
    await throwApiError(response, endpoint);
  }

  const data = (await response.json()) as DailyImportResponse;
  return data.papers;
}

export async function fetchRelatedSignals(paperId: string): Promise<RelatedSignal[]> {
  const endpoint = `GET /papers/${paperId}/related-signals`;
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}/related-signals`);
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as RelatedSignal[];
}

export async function fetchPaperAIAnalysis(
  paperId: string,
): Promise<PaperAIAnalysis | null> {
  const endpoint = `GET /papers/${paperId}/analysis`;
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}/analysis`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as PaperAIAnalysis;
}

export async function generatePaperAIAnalysis(
  paperId: string,
): Promise<PaperAIAnalysis> {
  const endpoint = `POST /papers/${paperId}/analysis/generate`;
  const response = await fetch(`${API_BASE_URL}/papers/${paperId}/analysis/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      provider: "gemini",
    }),
  });

  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as PaperAIAnalysis;
}

export async function discoverRelatedSignals(
  paperId: string,
): Promise<RelatedSignalDiscoveryResponse> {
  const endpoint = `POST /papers/${paperId}/related-signals/discover`;
  const response = await fetch(
    `${API_BASE_URL}/papers/${paperId}/related-signals/discover`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    await throwApiError(response, endpoint);
  }

  return (await response.json()) as RelatedSignalDiscoveryResponse;
}
