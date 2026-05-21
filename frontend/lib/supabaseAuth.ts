export type AuthSession = {
  accessToken: string;
  refreshToken: string | null;
  email: string | null;
  userId: string | null;
};

type SupabaseAuthResponse = {
  access_token?: string;
  refresh_token?: string;
  user?: {
    id?: string;
    email?: string;
  };
};

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";
const SESSION_STORAGE_KEY = "throwaway_or_pickup_auth_session";

function getAuthBaseUrl(): string {
  const baseUrl = SUPABASE_URL.trim().replace(/\/$/, "");
  if (!baseUrl || !SUPABASE_ANON_KEY) {
    throw new Error("Supabase Authの環境変数が設定されていません");
  }
  return `${baseUrl}/auth/v1`;
}

function buildHeaders(): HeadersInit {
  return {
    apikey: SUPABASE_ANON_KEY,
    "Content-Type": "application/json",
  };
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { msg?: string; message?: string };
    return data.msg ?? data.message ?? `Auth request failed: ${response.status}`;
  } catch {
    return `Auth request failed: ${response.status}`;
  }
}

function toAuthSession(data: SupabaseAuthResponse): AuthSession {
  if (!data.access_token) {
    throw new Error("ログインセッションを取得できませんでした");
  }

  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token ?? null,
    email: data.user?.email ?? null,
    userId: data.user?.id ?? null,
  };
}

export function isSupabaseAuthConfigured(): boolean {
  return Boolean(SUPABASE_URL.trim() && SUPABASE_ANON_KEY.trim());
}

export function loadStoredSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawSession = window.localStorage.getItem(SESSION_STORAGE_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    return JSON.parse(rawSession) as AuthSession;
  } catch {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

export function saveStoredSession(session: AuthSession): void {
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
}

export async function signInWithPassword(
  email: string,
  password: string,
): Promise<AuthSession> {
  const response = await fetch(`${getAuthBaseUrl()}/token?grant_type=password`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return toAuthSession((await response.json()) as SupabaseAuthResponse);
}

export async function signUpWithPassword(
  email: string,
  password: string,
): Promise<AuthSession | null> {
  const response = await fetch(`${getAuthBaseUrl()}/signup`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const data = (await response.json()) as SupabaseAuthResponse;
  if (!data.access_token) {
    return null;
  }

  return toAuthSession(data);
}
