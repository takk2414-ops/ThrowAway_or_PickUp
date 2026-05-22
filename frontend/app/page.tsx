"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { AuthPanel } from "../components/AuthPanel";
import type { AuthMode } from "../components/AuthPanel";
import { PaperList } from "../features/paper-screening/components/PaperList";
import { ScreeningToolbar } from "../features/paper-screening/components/ScreeningToolbar";
import { sortPapers } from "../features/paper-screening/sortPapers";
import type {
  ActionState,
  PaperDecisionAction,
  SortKey,
} from "../features/paper-screening/types";
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
  discoverRelatedSignals,
  fetchPapers,
  fetchRelatedSignals,
  importNewPapers,
} from "../lib/papers";
import type { Paper, RelatedSignal } from "../lib/papers";

export default function HomePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [decidedActions, setDecidedActions] = useState<Record<string, PaperDecisionAction>>({});
  const [sortKey, setSortKey] = useState<SortKey>("new");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [isImportingNew, setIsImportingNew] = useState(false);
  const [relatedSignals, setRelatedSignals] = useState<Record<string, RelatedSignal[]>>({});
  const [sourceErrorsByPaper, setSourceErrorsByPaper] = useState<Record<string, string[]>>({});
  const [isLoadingSignals, setIsLoadingSignals] = useState(false);
  const [isDiscoveringSignals, setIsDiscoveringSignals] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [actionState, setActionState] = useState<ActionState>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isAuthPending, setIsAuthPending] = useState(false);
  const screeningPapers = useMemo(
    () => sortPapers(papers, relatedSignals, sortKey).slice(0, 10),
    [papers, relatedSignals, sortKey],
  );
  const currentPaper = screeningPapers[currentIndex] ?? null;

  useEffect(() => {
    setAuthSession(loadStoredSession());

    async function loadPapers(): Promise<void> {
      try {
        const fetchedPapers = await fetchPapers();
        setPapers(fetchedPapers);
        setCurrentIndex(0);
        setDecidedActions({});
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

  useEffect(() => {
    if (screeningPapers.length === 0) {
      setCurrentIndex(0);
      return;
    }

    setCurrentIndex((index) => Math.min(index, screeningPapers.length - 1));
  }, [screeningPapers.length]);

  useEffect(() => {
    if (currentPaper === null || relatedSignals[currentPaper.id]) {
      return;
    }

    async function loadRelatedSignals(): Promise<void> {
      if (currentPaper === null) {
        return;
      }

      try {
        const signals = await fetchRelatedSignals(currentPaper.id);
        setRelatedSignals((currentSignals) => ({
          ...currentSignals,
          [currentPaper.id]: signals,
        }));
      } catch {
        setRelatedSignals((currentSignals) => ({
          ...currentSignals,
          [currentPaper.id]: [],
        }));
      }
    }

    loadRelatedSignals();
  }, [currentPaper, relatedSignals]);

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

  async function handleSortChange(nextSortKey: SortKey): Promise<void> {
    setSortKey(nextSortKey);
    setCurrentIndex(0);
    setActionState(null);
    setImportMessage(null);

    if (nextSortKey === "new" || papers.length === 0) {
      return;
    }

    setIsLoadingSignals(true);
    try {
      await loadRelatedSignalsForPapers(papers);
    } finally {
      setIsLoadingSignals(false);
    }
  }

  async function loadRelatedSignalsForPapers(nextPapers: Paper[]): Promise<void> {
    const signalEntries = await Promise.all(
      nextPapers.map(async (paper) => {
        try {
          return [paper.id, await fetchRelatedSignals(paper.id)] as const;
        } catch {
          return [paper.id, []] as const;
        }
      }),
    );
    setRelatedSignals((currentSignals) => ({
      ...currentSignals,
      ...Object.fromEntries(signalEntries),
    }));
  }

  async function handleImportNewPapers(): Promise<void> {
    setIsImportingNew(true);
    setImportMessage(null);
    setErrorMessage(null);

    try {
      const importedPapers = await importNewPapers();
      setPapers(importedPapers);
      setSortKey("new");
      setCurrentIndex(0);
      setDecidedActions({});
      setRelatedSignals({});
      setSourceErrorsByPaper({});
      setImportMessage(`${importedPapers.length}件の新着論文を取り込みました`);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "arXivからの論文取得に失敗しました";
      setErrorMessage(message);
    } finally {
      setIsImportingNew(false);
    }
  }

  async function handleCreatePaperAction(
    paperId: string,
    action: PaperDecisionAction,
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
      setDecidedActions((currentDecisions) => ({
        ...currentDecisions,
        [paperId]: action,
      }));
      setCurrentIndex((index) => (
        Math.min(index + 1, Math.max(screeningPapers.length - 1, 0))
      ));
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

  async function handleDiscoverSignalsForPaper(paperId: string): Promise<void> {
    setIsDiscoveringSignals(true);
    setErrorMessage(null);

    try {
      const discovery = await discoverRelatedSignals(paperId);
      setRelatedSignals((currentSignals) => ({
        ...currentSignals,
        [paperId]: discovery.signals,
      }));
      setSourceErrorsByPaper((currentErrors) => ({
        ...currentErrors,
        [paperId]: discovery.source_errors,
      }));
      const errorMessage =
        discovery.source_errors.length > 0
          ? ` / API失敗: ${discovery.source_errors.join(", ")}`
          : "";
      setImportMessage(
        `${discovery.discovered_count}件の関連シグナルを見つけました${errorMessage}`,
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "関連シグナルの探索に失敗しました";
      setErrorMessage(message);
    } finally {
      setIsDiscoveringSignals(false);
    }
  }

  async function handleDiscoverSignalsForVisiblePapers(): Promise<void> {
    if (screeningPapers.length === 0) {
      setImportMessage("探索対象の論文がありません");
      return;
    }

    setIsDiscoveringSignals(true);
    setErrorMessage(null);

    let discoveredCount = 0;
    const sourceErrorCounts: Record<string, number> = {};
    try {
      for (const paper of screeningPapers) {
        const discovery = await discoverRelatedSignals(paper.id);
        discoveredCount += discovery.discovered_count;
        for (const sourceName of discovery.source_errors) {
          sourceErrorCounts[sourceName] = (sourceErrorCounts[sourceName] ?? 0) + 1;
        }
        setRelatedSignals((currentSignals) => ({
          ...currentSignals,
          [paper.id]: discovery.signals,
        }));
        setSourceErrorsByPaper((currentErrors) => ({
          ...currentErrors,
          [paper.id]: discovery.source_errors,
        }));
      }
      setCurrentIndex(0);
      const errorSummary = Object.entries(sourceErrorCounts)
        .map(([sourceName, count]) => `${sourceName}: ${count}件`)
        .join(", ");
      setImportMessage(
        errorSummary
          ? `表示中${screeningPapers.length}件から${discoveredCount}件の関連シグナルを見つけました / API失敗: ${errorSummary}`
          : `表示中${screeningPapers.length}件から${discoveredCount}件の関連シグナルを見つけました`,
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "関連シグナルの探索に失敗しました";
      setErrorMessage(message);
    } finally {
      setIsDiscoveringSignals(false);
    }
  }

  function handleMovePrevious(): void {
    setCurrentIndex((index) => Math.max(index - 1, 0));
  }

  function handleMoveNext(): void {
    setCurrentIndex((index) => (
      Math.min(index + 1, Math.max(screeningPapers.length - 1, 0))
    ));
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

      <ScreeningToolbar
        isDiscoveringSignals={isDiscoveringSignals}
        isImportingNew={isImportingNew}
        isLoadingSignals={isLoadingSignals}
        onDiscoverSignals={handleDiscoverSignalsForVisiblePapers}
        onImportNew={handleImportNewPapers}
        onSortChange={(nextSortKey) => void handleSortChange(nextSortKey)}
        sortKey={sortKey}
      />

      {isLoading && <p className="notice">論文一覧を読み込み中です。</p>}

      {errorMessage && (
        <p className="notice error">Backend APIに接続できません: {errorMessage}</p>
      )}

      {importMessage && <p className="notice success">{importMessage}</p>}

      {isLoadingSignals && (
        <p className="notice">関連シグナルを確認中です。</p>
      )}

      {!isLoading && !errorMessage && papers.length === 0 && (
        <p className="notice">
          論文はまだありません。Import New で確認用データを取り込んでください。
        </p>
      )}

      <PaperList
        actionState={actionState}
        currentIndex={currentIndex}
        decidedActions={decidedActions}
        isAuthenticated={authSession !== null}
        isDiscoveringSignals={isDiscoveringSignals}
        onCreateAction={handleCreatePaperAction}
        onDiscoverSignals={handleDiscoverSignalsForPaper}
        onMoveNext={handleMoveNext}
        onMovePrevious={handleMovePrevious}
        papers={screeningPapers}
        pendingAction={pendingAction}
        relatedSignals={currentPaper ? relatedSignals[currentPaper.id] ?? [] : []}
        sourceErrors={currentPaper ? sourceErrorsByPaper[currentPaper.id] ?? [] : []}
      />
    </main>
  );
}
