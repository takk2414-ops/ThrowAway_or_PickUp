"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { AuthPanel } from "../components/AuthPanel";
import type { AuthMode } from "../components/AuthPanel";
import { PaperList } from "../components/PaperList";
import type { ActionState } from "../components/PaperList";
import {
  clearStoredSession,
  isSupabaseAuthConfigured,
  loadStoredSession,
  saveStoredSession,
  signInWithPassword,
  signUpWithPassword,
} from "../lib/supabaseAuth";
import type { AuthSession } from "../lib/supabaseAuth";
import {
  API_BASE_URL,
  createPaperAction,
  fetchPapers,
  importArxivPapers,
} from "../lib/papers";
import type { Paper, PaperAction } from "../lib/papers";

export default function HomePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [actionState, setActionState] = useState<ActionState>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isAuthPending, setIsAuthPending] = useState(false);

  useEffect(() => {
    setAuthSession(loadStoredSession());

    async function loadPapers(): Promise<void> {
      try {
        setPapers(await fetchPapers());
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "論文一覧の取得に失敗しました";
        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    loadPapers();
  }, []);

  async function handleAuthSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setAuthMessage(null);
    setAuthError(null);

    if (!isSupabaseAuthConfigured()) {
      setAuthError("Supabase Authの環境変数が設定されていません");
      return;
    }

    setIsAuthPending(true);

    try {
      const session =
        authMode === "signin"
          ? await signInWithPassword(email, password)
          : await signUpWithPassword(email, password);

      if (session === null) {
        setAuthMessage("確認メールを送信しました。メール確認後にログインしてください。");
        return;
      }

      saveStoredSession(session);
      setAuthSession(session);
      setPassword("");
      setAuthMessage("ログインしました");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "ログイン処理に失敗しました";
      setAuthError(message);
    } finally {
      setIsAuthPending(false);
    }
  }

  function handleSignOut(): void {
    clearStoredSession();
    setAuthSession(null);
    setAuthMessage("ログアウトしました");
    setAuthError(null);
  }

  async function handleImportArxivPapers(): Promise<void> {
    setIsImporting(true);
    setImportMessage(null);
    setErrorMessage(null);

    try {
      const importedPapers = await importArxivPapers();
      setPapers(importedPapers);
      setImportMessage(`${importedPapers.length}件の論文を取り込みました`);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "arXivからの論文取得に失敗しました";
      setErrorMessage(message);
    } finally {
      setIsImporting(false);
    }
  }

  async function handleCreatePaperAction(
    paperId: string,
    action: PaperAction,
  ): Promise<void> {
    if (!authSession) {
      setActionState({
        paperId,
        message: "ログインすると判定を保存できます",
        isError: true,
      });
      return;
    }

    setPendingAction(`${paperId}:${action}`);
    setActionState(null);

    try {
      await createPaperAction(paperId, action, authSession.accessToken);
      setActionState({
        paperId,
        message: `${action} を保存しました`,
        isError: false,
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes("failed: 401")) {
        clearStoredSession();
        setAuthSession(null);
        setActionState({
          paperId,
          message: "ログインの有効期限が切れました。再ログインしてください。",
          isError: true,
        });
      } else {
        const message =
          error instanceof Error ? error.message : "判定アクションの保存に失敗しました";
        setActionState({
          paperId,
          message,
          isError: true,
        });
      }
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <div>
          <p className="eyebrow">Paper Screening</p>
          <h1>ThrowAway_or_PickUp</h1>
        </div>
        <div className="header-actions">
          <p className="api-url">{API_BASE_URL}</p>
          <button
            className="secondary-button"
            disabled={isImporting}
            onClick={handleImportArxivPapers}
            type="button"
          >
            {isImporting ? "Importing..." : "Import arXiv"}
          </button>
        </div>
      </section>

      <AuthPanel
        authError={authError}
        authMessage={authMessage}
        authMode={authMode}
        authSession={authSession}
        email={email}
        isAuthPending={isAuthPending}
        onAuthModeChange={setAuthMode}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSignOut={handleSignOut}
        onSubmit={handleAuthSubmit}
        password={password}
      />

      {isLoading && <p className="notice">論文一覧を読み込み中です。</p>}

      {errorMessage && (
        <p className="notice error">Backend APIに接続できません: {errorMessage}</p>
      )}

      {importMessage && <p className="notice success">{importMessage}</p>}

      {!isLoading && !errorMessage && papers.length === 0 && (
        <p className="notice">
          論文はまだありません。Import arXiv で確認用データを取り込んでください。
        </p>
      )}

      <PaperList
        actionState={actionState}
        isAuthenticated={authSession !== null}
        onCreateAction={handleCreatePaperAction}
        papers={papers}
        pendingAction={pendingAction}
      />
    </main>
  );
}
