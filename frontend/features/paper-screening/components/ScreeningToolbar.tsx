import { SORT_OPTIONS } from "../sortPapers";
import type { SortKey } from "../types";

type ScreeningToolbarProps = {
  isDiscoveringSignals: boolean;
  isImportingNew: boolean;
  isLoadingSignals: boolean;
  onDiscoverSignals: () => void;
  onImportNew: () => void;
  onSortChange: (sortKey: SortKey) => void;
  sortKey: SortKey;
};

export function ScreeningToolbar({
  isDiscoveringSignals,
  isImportingNew,
  isLoadingSignals,
  onDiscoverSignals,
  onImportNew,
  onSortChange,
  sortKey,
}: ScreeningToolbarProps) {
  const isBusy = isDiscoveringSignals || isImportingNew || isLoadingSignals;

  return (
    <section className="screening-toolbar" aria-label="論文表示操作">
      <div className="sort-controls" role="tablist" aria-label="並び替え">
        {SORT_OPTIONS.map((option) => (
          <button
            aria-selected={sortKey === option.key}
            className={sortKey === option.key ? "sort-button active" : "sort-button"}
            onClick={() => onSortChange(option.key)}
            role="tab"
            type="button"
            key={option.key}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="toolbar-actions">
        <button
          className="secondary-button"
          disabled={isBusy}
          onClick={onImportNew}
          type="button"
        >
          {isImportingNew ? "Importing..." : "Import New"}
        </button>
        <button
          className="secondary-button"
          disabled={isBusy}
          onClick={onDiscoverSignals}
          type="button"
        >
          {isDiscoveringSignals ? "Discovering..." : "Discover Signals"}
        </button>
      </div>
    </section>
  );
}
