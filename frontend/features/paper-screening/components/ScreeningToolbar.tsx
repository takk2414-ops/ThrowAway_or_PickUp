import type { PaperViewMode } from "../types";

type ScreeningToolbarProps = {
  canExportPicked: boolean;
  isExportingPicked: boolean;
  isLoadingSignals: boolean;
  onCopyNotebookPrompt: () => void;
  onCopyPickedPdfUrls: () => void;
  onDownloadPickedMarkdown: () => void;
  onDownloadPickedPdfZip: () => void;
  onLoadPicked: () => void;
  viewMode: PaperViewMode;
};

export function ScreeningToolbar({
  canExportPicked,
  isExportingPicked,
  isLoadingSignals,
  onCopyNotebookPrompt,
  onCopyPickedPdfUrls,
  onDownloadPickedMarkdown,
  onDownloadPickedPdfZip,
  onLoadPicked,
  viewMode,
}: ScreeningToolbarProps) {
  const exportDisabled = !canExportPicked || isExportingPicked;

  return (
    <section className="screening-toolbar" aria-label="論文表示操作">
      <div className="toolbar-actions">
        <button
          className={viewMode === "picked" ? "secondary-button active" : "secondary-button"}
          disabled={isLoadingSignals}
          onClick={onLoadPicked}
          type="button"
        >
          ピックアップ済み
        </button>
        {viewMode === "picked" && (
          <>
            <button
              className="secondary-button"
              disabled={exportDisabled}
              onClick={onCopyPickedPdfUrls}
              type="button"
            >
              PDF URLをコピー
            </button>
            <button
              className="secondary-button"
              disabled={exportDisabled}
              onClick={onDownloadPickedMarkdown}
              type="button"
            >
              Markdownノート
            </button>
            <button
              className="secondary-button"
              disabled={exportDisabled}
              onClick={onDownloadPickedPdfZip}
              type="button"
            >
              PDF ZIP
            </button>
            <button
              className="secondary-button"
              disabled={exportDisabled}
              onClick={onCopyNotebookPrompt}
              type="button"
            >
              NotebookLM質問
            </button>
          </>
        )}
      </div>
    </section>
  );
}
