"""論文に紐づく外部シグナル探索を担当する service です。"""

from app.clients import github, qiita
from app.repositories import paper_repository
from app.schemas.paper import (
    PaperResponse,
    RelatedSignalCreate,
    RelatedSignalDiscoveryResponse,
)


def build_signal_search_queries(paper: PaperResponse) -> list[str]:
    queries: list[str] = []
    if paper.arxiv_id:
        queries.append(paper.arxiv_id)
    queries.append(paper.title)
    return queries


def dedupe_signal_creates(
    signals: list[RelatedSignalCreate],
) -> list[RelatedSignalCreate]:
    seen_urls: set[str] = set()
    deduped_signals: list[RelatedSignalCreate] = []
    for signal in signals:
        if signal.source_url in seen_urls:
            continue
        seen_urls.add(signal.source_url)
        deduped_signals.append(signal)
    return deduped_signals


def first_non_empty_source_results(
    queries: list[str],
    search_func,
    max_results: int,
) -> list[RelatedSignalCreate]:
    for query in queries:
        signals = search_func(query, max_results)
        if signals:
            return signals
    return []


def discover_signal_creates(
    paper: PaperResponse,
    max_results_per_source: int = 3,
) -> tuple[list[RelatedSignalCreate], list[str]]:
    discovered_signals: list[RelatedSignalCreate] = []
    source_errors: list[str] = []
    queries = build_signal_search_queries(paper)

    sources = [
        ("github", github.search_repositories),
        ("qiita", qiita.search_items),
    ]
    for source_name, search_func in sources:
        try:
            discovered_signals.extend(
                first_non_empty_source_results(
                    queries,
                    search_func,
                    max_results_per_source,
                )
            )
        except (
            github.GitHubClientError,
            qiita.QiitaClientError,
        ):
            source_errors.append(source_name)

    return dedupe_signal_creates(discovered_signals), source_errors


def discover_and_save_related_signals(
    paper: PaperResponse,
    max_results_per_source: int = 3,
) -> RelatedSignalDiscoveryResponse:
    signal_creates, source_errors = discover_signal_creates(
        paper,
        max_results_per_source,
    )
    saved_signals = [
        paper_repository.create_related_signal(paper.id, signal)
        for signal in signal_creates
    ]

    return RelatedSignalDiscoveryResponse(
        discovered_count=len(saved_signals),
        signals=saved_signals,
        source_errors=source_errors,
    )
