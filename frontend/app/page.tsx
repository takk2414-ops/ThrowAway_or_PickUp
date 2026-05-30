"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { AuthPanel } from "../components/AuthPanel";
import type { AuthMode } from "../components/AuthPanel";
import { PaperList } from "../features/paper-screening/components/PaperList";
import { ScreeningToolbar } from "../features/paper-screening/components/ScreeningToolbar";
import {
  copyTextToClipboard,
  downloadBlobFile,
  downloadTextFile,
} from "../features/paper-screening/browserFiles";
import {
  buildErrorNotice,
  type ErrorNotice,
} from "../features/paper-screening/errorNotices";
import type {
  ActionState,
  PaperViewMode,
  PaperDecisionAction,
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
  createPaperAction,
  fetchPickedPapers,
  fetchPickedPapersExport,
  fetchPickedPapersPdfZip,
  fetchPaperAIAnalysis,
  fetchRelatedSignals,
  fetchTodayPapers,
  generatePaperAIAnalysis,
} from "../lib/papers";
import type {
  Paper,
  PaperAIAnalysis,
  PickedPapersExport,
  RelatedSignal,
} from "../lib/papers";

export default function HomePage() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [decidedActions, setDecidedActions] = useState<Record<string, PaperDecisionAction>>({});
  const [viewMode, setViewMode] = useState<PaperViewMode>("today");
  const [isLoading, setIsLoading] = useState(true);
  const [errorNotice, setErrorNotice] = useState<ErrorNotice | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [relatedSignals, setRelatedSignals] = useState<Record<string, RelatedSignal[]>>({});
  const [paperAIAnalyses, setPaperAIAnalyses] = useState<
    Record<string, PaperAIAnalysis | null>
  >({});
  const [isLoadingSignals, setIsLoadingSignals] = useState(false);
  const [isExportingPicked, setIsExportingPicked] = useState(false);
  const [pickedExport, setPickedExport] = useState<PickedPapersExport | null>(null);
  const [isGeneratingAnalysis, setIsGeneratingAnalysis] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [actionState, setActionState] = useState<ActionState>(null);
  const [authMode, setAuthMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authSession, setAuthSession] = useState<AuthSession | null>(null);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isAuthPending, setIsAuthPending] = useState(false);
  const screeningPapers = papers;
  const currentPaper = screeningPapers[currentIndex] ?? null;
  const decidedActionCount = Object.keys(decidedActions).length;

  useEffect(() => {
    setAuthSession(loadStoredSession());

    async function loadPapers(): Promise<void> {
      try {
        const fetchedPapers = await fetchTodayPapers();
        setPapers(fetchedPapers);
        setCurrentIndex(0);
        setDecidedActions({});
      } catch (error) {
        setErrorNotice(
          buildErrorNotice(error, "論文一覧の取得に失敗しました", "today"),
        );
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

  useEffect(() => {
    if (currentPaper === null || currentPaper.id in paperAIAnalyses) {
      return;
    }

    async function loadPaperAIAnalysis(): Promise<void> {
      if (currentPaper === null) {
        return;
      }

      try {
        const analysis = await fetchPaperAIAnalysis(currentPaper.id);
        setPaperAIAnalyses((currentAnalyses) => ({
          ...currentAnalyses,
          [currentPaper.id]: analysis,
        }));
      } catch {
        setPaperAIAnalyses((currentAnalyses) => ({
          ...currentAnalyses,
          [currentPaper.id]: null,
        }));
      }
    }

    loadPaperAIAnalysis();
  }, [currentPaper, paperAIAnalyses]);

  useEffect(() => {
    if (viewMode !== "picked" || papers.length === 0) {
      return;
    }

    const missingPapers = papers.filter((paper) => !(paper.id in paperAIAnalyses));
    if (missingPapers.length === 0) {
      return;
    }

    async function loadPickedPaperAIAnalyses(): Promise<void> {
      const analysisEntries = await Promise.all(
        missingPapers.map(async (paper): Promise<[string, PaperAIAnalysis | null]> => {
          try {
            return [paper.id, await fetchPaperAIAnalysis(paper.id)];
          } catch {
            return [paper.id, null];
          }
        }),
      );

      setPaperAIAnalyses((currentAnalyses) => ({
        ...currentAnalyses,
        ...Object.fromEntries(analysisEntries),
      }));
    }

    loadPickedPaperAIAnalyses();
  }, [papers, paperAIAnalyses, viewMode]);

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

  async function handleLoadPickedPapers(): Promise<void> {
    if (!authSession) {
      setImportMessage(null);
      setErrorNotice(null);
      setAuthError("ピックアップ済み論文を見るにはログインしてください");
      return;
    }

    setIsLoadingSignals(true);
    setImportMessage(null);
    setErrorNotice(null);
    setAuthError(null);

    try {
      const pickedPapers = await fetchPickedPapers(authSession.accessToken);
      setPapers(pickedPapers);
      setViewMode("picked");
      setCurrentIndex(0);
      setRelatedSignals({});
      setPaperAIAnalyses({});
      setPickedExport(null);
      setImportMessage(`${pickedPapers.length}件のピックアップ済み論文を読み込みました`);
    } catch (error) {
      if (error instanceof Error && error.message.includes("failed: 401")) {
        clearStoredSession();
        setAuthSession(null);
        setAuthError("ログインの有効期限が切れました。再ログインしてください。");
      } else {
        setErrorNotice(
          buildErrorNotice(error, "ピックアップ済み論文の取得に失敗しました", "picked"),
        );
      }
    } finally {
      setIsLoadingSignals(false);
    }
  }

  async function handleLoadTodayPapers(): Promise<void> {
    setIsLoadingSignals(true);
    setImportMessage(null);
    setErrorNotice(null);
    setAuthError(null);

    try {
      const todayPapers = await fetchTodayPapers();
      setPapers(todayPapers);
      setViewMode("today");
      setCurrentIndex(0);
      setDecidedActions({});
      setRelatedSignals({});
      setPaperAIAnalyses({});
      setPickedExport(null);
      setImportMessage(`${todayPapers.length}件の最新論文を読み込みました`);
    } catch (error) {
      setErrorNotice(
        buildErrorNotice(error, "論文一覧の取得に失敗しました", "today"),
      );
    } finally {
      setIsLoadingSignals(false);
    }
  }

  async function loadPickedExport(): Promise<PickedPapersExport | null> {
    if (!authSession) {
      setAuthError("ピックアップ済み論文をexportするにはログインしてください");
      return null;
    }

    if (pickedExport !== null) {
      return pickedExport;
    }

    setIsExportingPicked(true);
    setErrorNotice(null);
    setImportMessage(null);

    try {
      const exportData = await fetchPickedPapersExport(authSession.accessToken);
      setPickedExport(exportData);
      return exportData;
    } catch (error) {
      setErrorNotice(
        buildErrorNotice(error, "ピックアップ済み論文のexportに失敗しました", "picked"),
      );
      return null;
    } finally {
      setIsExportingPicked(false);
    }
  }

  async function handleCopyPickedPdfUrls(): Promise<void> {
    const exportData = await loadPickedExport();
    if (exportData === null) {
      return;
    }

    try {
      await copyTextToClipboard(exportData.pdf_urls.join("\n"));
      setImportMessage(`${exportData.pdf_urls.length}件のPDF URLをコピーしました`);
    } catch (error) {
      setErrorNotice(buildErrorNotice(error, "PDF URLのコピーに失敗しました", "picked"));
    }
  }

  async function handleDownloadPickedMarkdown(): Promise<void> {
    const exportData = await loadPickedExport();
    if (exportData === null) {
      return;
    }

    downloadTextFile("picked-papers-notebooklm.md", exportData.markdown_note);
    setImportMessage("NotebookLM用Markdownノートをダウンロードしました");
  }

  async function handleDownloadPickedPdfZip(): Promise<void> {
    if (!authSession) {
      setAuthError("PDF ZIPをダウンロードするにはログインしてください");
      return;
    }

    setIsExportingPicked(true);
    setErrorNotice(null);
    setImportMessage(null);

    try {
      const zipBlob = await fetchPickedPapersPdfZip(authSession.accessToken);
      downloadBlobFile("picked-papers-notebooklm.zip", zipBlob);
      setImportMessage("PDF ZIPをダウンロードしました");
    } catch (error) {
      setErrorNotice(
        buildErrorNotice(error, "PDF ZIPのダウンロードに失敗しました", "picked"),
      );
    } finally {
      setIsExportingPicked(false);
    }
  }

  async function handleCopyNotebookPrompt(): Promise<void> {
    const exportData = await loadPickedExport();
    if (exportData === null) {
      return;
    }

    try {
      await copyTextToClipboard(exportData.notebooklm_prompt);
      setImportMessage("NotebookLM用質問テンプレートをコピーしました");
    } catch (error) {
      setErrorNotice(
        buildErrorNotice(error, "NotebookLM用質問テンプレートのコピーに失敗しました", "picked"),
      );
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
      const remainingPaperCount = Math.max(screeningPapers.length - 1, 0);
      setPapers((currentPapers) => (
        currentPapers.filter((paper) => paper.id !== paperId)
      ));
      setCurrentIndex((index) => (
        remainingPaperCount === 0 ? 0 : Math.min(index, remainingPaperCount - 1)
      ));
      setActionState({
        paperId,
        message: `${action === "pickup" ? "ピックアップ" : "スキップ"}を保存しました`,
        isError: false,
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes("failed: 401")) {
        clearStoredSession();
        setAuthSession(null);
        setAuthError("ログインの有効期限が切れました。再ログインしてください。");
        setActionState({
          paperId,
          message: "ログインの有効期限が切れました。再ログインしてください。",
          isError: true,
        });
      } else {
        const notice = buildErrorNotice(
          error,
          "判定アクションの保存に失敗しました",
          "action",
        );
        setErrorNotice(notice);
        setActionState({
          paperId,
          message: notice.title,
          isError: true,
        });
      }
    } finally {
      setPendingAction(null);
    }
  }

  function handleMovePrevious(): void {
    setCurrentIndex((index) => (
      screeningPapers.length === 0
        ? 0
        : (index - 1 + screeningPapers.length) % screeningPapers.length
    ));
  }

  function handleMoveNext(): void {
    setCurrentIndex((index) => (
      screeningPapers.length === 0 ? 0 : (index + 1) % screeningPapers.length
    ));
  }

  async function handleGeneratePaperAIAnalysis(paperId: string): Promise<void> {
    setIsGeneratingAnalysis(true);
    setErrorNotice(null);

    try {
      const analysis = await generatePaperAIAnalysis(paperId);
      setPaperAIAnalyses((currentAnalyses) => ({
        ...currentAnalyses,
        [paperId]: analysis,
      }));
    } catch (error) {
      setErrorNotice(
        buildErrorNotice(error, "AI分析の生成に失敗しました", "analysis"),
      );
    } finally {
      setIsGeneratingAnalysis(false);
    }
  }

  return (
    <main className="page-shell">
      {isLoading && <p className="notice">論文一覧を読み込み中です。</p>}

      {errorNotice && (
        <section className="notice error operational-error" aria-label="エラー詳細">
          <p className="error-title">{errorNotice.title}</p>
          <p>{errorNotice.message}</p>
          <ul>
            {errorNotice.checks.map((check) => (
              <li key={check}>{check}</li>
            ))}
          </ul>
        </section>
      )}

      {importMessage && <p className="notice success">{importMessage}</p>}

      {isLoadingSignals && (
        <p className="notice">関連シグナルを確認中です。</p>
      )}

      {!isLoading && !errorNotice && viewMode === "today" && papers.length === 0 && decidedActionCount === 0 && (
        <section className="notice empty-state" aria-label="今日の論文リスト未生成">
          <p className="error-title">今日表示できる論文がありません</p>
          <p>自動取り込みは実行されましたが、保存対象の論文が見つからなかった可能性があります。</p>
          <ul>
            <li>arXiv / Qiita / GitHub など外部APIの応答をbackendログで確認してください。</li>
            <li>daily_paper_items に今日の日付の行があるか確認してください。</li>
            <li>運用環境ではcronが `backend/scripts/import_daily_feed.py` を4:00 JSTに実行しているか確認してください。</li>
          </ul>
        </section>
      )}

      {!isLoading && !errorNotice && viewMode === "today" && papers.length === 0 && decidedActionCount > 0 && (
        <p className="notice success">
          表示中の論文はすべてピックアップ/スキップで判定しました。
        </p>
      )}

      {!isLoading && !errorNotice && viewMode === "picked" && papers.length === 0 && (
        <p className="notice">ピックアップ済み論文はまだありません。</p>
      )}

      <PaperList
        actionState={actionState}
        currentIndex={currentIndex}
        decidedActions={decidedActions}
        isAuthenticated={authSession !== null}
        onCreateAction={handleCreatePaperAction}
        onGenerateAnalysis={handleGeneratePaperAIAnalysis}
        onMoveNext={handleMoveNext}
        onMovePrevious={handleMovePrevious}
        papers={screeningPapers}
        paperAIAnalysis={currentPaper ? paperAIAnalyses[currentPaper.id] : null}
        paperAIAnalysesByPaperId={paperAIAnalyses}
        isGeneratingAnalysis={isGeneratingAnalysis}
        pendingAction={pendingAction}
        relatedSignals={currentPaper ? relatedSignals[currentPaper.id] ?? [] : []}
        sourceErrors={[]}
        viewMode={viewMode}
      />

      <section className="bottom-dock" aria-label="固定操作">
        <ScreeningToolbar
          canExportPicked={viewMode === "picked" && papers.length > 0}
          isExportingPicked={isExportingPicked}
          isLoadingSignals={isLoadingSignals}
          onCopyNotebookPrompt={handleCopyNotebookPrompt}
          onCopyPickedPdfUrls={handleCopyPickedPdfUrls}
          onDownloadPickedMarkdown={handleDownloadPickedMarkdown}
          onDownloadPickedPdfZip={handleDownloadPickedPdfZip}
          onLoadPicked={handleLoadPickedPapers}
          onLoadToday={handleLoadTodayPapers}
          viewMode={viewMode}
        />

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
      </section>
    </main>
  );
}
