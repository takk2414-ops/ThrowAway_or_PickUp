"""Rising Papers の取り込みを担当する service です。"""

from datetime import UTC, datetime, timedelta

from app.clients import arxiv
from app.repositories import paper_repository
from app.schemas.imports import (
    RisingImportRequest,
    RisingImportResponse,
)
from app.schemas.papers import PaperCreate, PaperResponse
from app.schemas.signals import RelatedSignalResponse
from app.services import signal_discovery_service


RisingImportError = arxiv.ArxivClientError
JAPANESE_ARTICLE_SOURCE_TYPES = {"qiita"}


def _format_arxiv_submitted_date(target_datetime: datetime, suffix: str) -> str:
    return f"{target_datetime.strftime('%Y%m%d')}{suffix}"


def build_rising_search_query(
    category: str,
    min_days_old: int,
    max_days_old: int,
    now: datetime | None = None,
) -> str:
    current_time = now or datetime.now(UTC)
    oldest_date = current_time - timedelta(days=max_days_old)
    newest_date = current_time - timedelta(days=min_days_old)
    oldest_submitted_date = _format_arxiv_submitted_date(oldest_date, "0000")
    newest_submitted_date = _format_arxiv_submitted_date(newest_date, "2359")
    return (
        f"cat:{category} "
        f"AND submittedDate:[{oldest_submitted_date} TO {newest_submitted_date}]"
    )


def _dedupe_paper_creates(
    paper_creates: list[PaperCreate],
) -> list[PaperCreate]:
    seen_keys: set[str] = set()
    deduped_papers: list[PaperCreate] = []
    for paper_create in paper_creates:
        key = paper_create.arxiv_id or paper_create.source_url or paper_create.title
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped_papers.append(paper_create)
    return deduped_papers


def _sort_papers_by_signal_count(
    papers: list[PaperResponse],
    signal_counts: dict[str, int],
) -> list[PaperResponse]:
    return sorted(
        papers,
        key=lambda paper: (
            signal_counts.get(str(paper.id), 0),
            paper.published_at or paper.created_at,
        ),
        reverse=True,
    )


def _count_signals_by_source(
    signals: list[RelatedSignalResponse],
) -> dict[str, int]:
    source_counts: dict[str, int] = {}
    for signal in signals:
        source_type = signal.source_type
        source_counts[source_type] = source_counts.get(source_type, 0) + 1
    return source_counts


def _is_rising_candidate(source_counts: dict[str, int]) -> bool:
    has_github = source_counts.get("github", 0) > 0
    has_japanese_article = any(
        source_counts.get(source_type, 0) > 0
        for source_type in JAPANESE_ARTICLE_SOURCE_TYPES
    )
    return has_github and has_japanese_article


def import_rising_papers(
    import_request: RisingImportRequest,
) -> RisingImportResponse:
    paper_creates: list[PaperCreate] = []
    for category in import_request.categories:
        paper_creates.extend(
            arxiv.fetch_papers(
                search_query=build_rising_search_query(
                    category,
                    import_request.min_days_old,
                    import_request.max_days_old,
                ),
                max_results=import_request.max_results_per_category,
            )
        )

    imported_papers = paper_repository.upsert_papers_by_arxiv_id(
        _dedupe_paper_creates(paper_creates)
    )

    signal_counts: dict[str, int] = {}
    source_errors: list[str] = []
    rising_papers: list[PaperResponse] = []

    for paper in imported_papers:
        discovery = signal_discovery_service.discover_and_save_related_signals(
            paper,
            max_results_per_source=2,
        )
        signal_counts[str(paper.id)] = discovery.discovered_count
        source_errors.extend(discovery.source_errors)
        source_counts = _count_signals_by_source(discovery.signals)
        if _is_rising_candidate(source_counts):
            rising_papers.append(paper)

    sorted_rising_papers = _sort_papers_by_signal_count(rising_papers, signal_counts)

    return RisingImportResponse(
        imported_count=len(sorted_rising_papers[:import_request.max_papers]),
        papers=sorted_rising_papers[:import_request.max_papers],
        signal_counts=signal_counts,
        source_errors=sorted(set(source_errors)),
    )
