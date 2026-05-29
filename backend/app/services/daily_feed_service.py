"""毎日の表示リスト生成を担当する service です。"""

from datetime import UTC, date, datetime, timedelta

from app.clients import arxiv, qiita
from app.repositories import paper_repository
from app.schemas.analyses import PaperAIAnalysisGenerateRequest
from app.schemas.imports import DailyImportRequest, DailyImportResponse
from app.schemas.papers import PaperCreate, PaperResponse
from app.schemas.signals import RelatedSignalResponse
from app.services import paper_analysis_service, signal_discovery_service
from app.utils.time import today_jst


DAILY_FEED_IMPORT_SOURCE = "daily-feed"
LATEST_SELECTION_REASON = "latest_arxiv"
EXTERNAL_SIGNAL_SELECTION_REASON = "external_article"
EXTERNAL_ARTICLE_SOURCE_TYPES = {"qiita"}


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


def _exclude_existing_papers(
    papers: list[PaperResponse],
    existing_papers: list[PaperResponse],
) -> list[PaperResponse]:
    existing_ids = {paper.id for paper in existing_papers}
    existing_arxiv_ids = {
        paper.arxiv_id
        for paper in existing_papers
        if paper.arxiv_id is not None
    }

    return [
        paper
        for paper in papers
        if paper.id not in existing_ids
        and (
            paper.arxiv_id is None
            or paper.arxiv_id not in existing_arxiv_ids
        )
    ]


def _has_external_article(signals: list[RelatedSignalResponse]) -> bool:
    return any(
        signal.source_type in EXTERNAL_ARTICLE_SOURCE_TYPES
        for signal in signals
    )


def _sort_by_signal_count(
    papers_with_signal_count: list[tuple[PaperResponse, int]],
) -> list[PaperResponse]:
    return [
        paper
        for paper, _signal_count in sorted(
            papers_with_signal_count,
            key=lambda item: (
                item[1],
                item[0].published_at or item[0].created_at,
            ),
            reverse=True,
        )
    ]


def _is_paper_in_signal_date_range(
    paper: PaperResponse,
    import_request: DailyImportRequest,
    now: datetime,
) -> bool:
    if paper.published_at is None:
        return False

    min_published_at = now - timedelta(days=import_request.signal_max_days_old)
    max_published_at = now - timedelta(days=import_request.signal_min_days_old)
    return min_published_at <= paper.published_at <= max_published_at


def _fetch_external_article_papers(
    import_request: DailyImportRequest,
) -> list[PaperResponse]:
    now = datetime.now(UTC)
    created_after = now.date() - timedelta(days=import_request.signal_max_days_old)
    try:
        article_results = qiita.search_recent_arxiv_articles(
            created_after=created_after,
            max_results=100,
        )
    except qiita.QiitaClientError:
        return []
    articles_by_arxiv_id: dict[str, list[qiita.QiitaArxivArticle]] = {}
    for article_result in article_results:
        articles_by_arxiv_id.setdefault(article_result.arxiv_id, []).append(
            article_result
        )

    arxiv_ids = list(articles_by_arxiv_id.keys())[
        : import_request.signal_max_results_per_category
    ]
    paper_creates = arxiv.fetch_papers_by_ids(arxiv_ids)
    imported_papers = paper_repository.upsert_papers_by_arxiv_id(
        _dedupe_paper_creates(paper_creates)
    )

    candidates: list[tuple[PaperResponse, int]] = []
    for paper in imported_papers:
        if not _is_paper_in_signal_date_range(paper, import_request, now):
            continue
        article_signals = articles_by_arxiv_id.get(paper.arxiv_id or "", [])
        saved_signals = [
            paper_repository.create_related_signal(paper.id, article.signal)
            for article in article_signals
        ]
        discovery = signal_discovery_service.discover_and_save_related_signals(
            paper,
            max_results_per_source=1,
        )
        signals = [*saved_signals, *discovery.signals]
        if _has_external_article(signals):
            candidates.append((paper, len(signals)))

    return _sort_by_signal_count(candidates)[: import_request.signal_max_papers]


def _create_import_run(
    import_date: date,
    status: str,
    imported_count: int,
    error_message: str | None = None,
) -> None:
    try:
        paper_repository.create_daily_import_run(
            import_date=import_date,
            source=DAILY_FEED_IMPORT_SOURCE,
            status=status,
            imported_count=imported_count,
            error_message=error_message,
        )
    except paper_repository.PaperRepositoryError:
        # 実行履歴テーブルが未反映でも、daily_paper_items が本体なので処理は止めません。
        pass


def _pre_generate_ai_analyses(papers: list[PaperResponse]) -> tuple[int, int]:
    generated_count = 0
    failed_count = 0

    for paper in papers:
        try:
            analysis = paper_analysis_service.generate_paper_ai_analysis(
                paper.id,
                PaperAIAnalysisGenerateRequest(),
            )
        except (
            paper_analysis_service.PaperAnalysisConfigError,
            paper_analysis_service.PaperAnalysisGenerateError,
            paper_analysis_service.PaperAnalysisStorageError,
        ):
            failed_count += 1
            continue

        if analysis is not None:
            generated_count += 1

    return generated_count, failed_count


def import_daily_feed(
    import_request: DailyImportRequest,
    target_date: date | None = None,
) -> DailyImportResponse:
    import_date = target_date or today_jst()
    desired_paper_count = import_request.max_results + import_request.signal_max_papers
    existing_papers = paper_repository.list_today_papers(import_date)
    if existing_papers:
        return DailyImportResponse(
            import_date=import_date,
            imported_count=0,
            papers=existing_papers,
            skipped=True,
        )

    try:
        if existing_papers:
            latest_papers = existing_papers
        else:
            latest_creates = arxiv.fetch_papers(
                search_query=import_request.search_query,
                max_results=import_request.max_results,
            )
            latest_papers = paper_repository.upsert_papers_by_arxiv_id(
                _dedupe_paper_creates(latest_creates)
            )[: import_request.max_results]
            paper_repository.create_daily_paper_items(
                import_date,
                latest_papers,
                selection_reason=LATEST_SELECTION_REASON,
                start_order=1,
            )

        external_article_papers = _fetch_external_article_papers(import_request)
        remaining_signal_slots = max(desired_paper_count - len(latest_papers), 0)
        signal_papers = _exclude_existing_papers(
            external_article_papers,
            latest_papers,
        )[:remaining_signal_slots]

        paper_repository.create_daily_paper_items(
            import_date,
            signal_papers,
            selection_reason=EXTERNAL_SIGNAL_SELECTION_REASON,
            start_order=len(latest_papers) + 1,
        )

        papers = [*latest_papers, *signal_papers]
        ai_analysis_generated_count, ai_analysis_failed_count = (
            _pre_generate_ai_analyses(papers)
        )
        _create_import_run(
            import_date=import_date,
            status="success",
            imported_count=len(papers),
        )
        return DailyImportResponse(
            import_date=import_date,
            imported_count=len(papers),
            papers=papers,
            skipped=False,
            ai_analysis_generated_count=ai_analysis_generated_count,
            ai_analysis_failed_count=ai_analysis_failed_count,
        )
    except arxiv.ArxivClientError as error:
        _create_import_run(
            import_date=import_date,
            status="failed",
            imported_count=0,
            error_message=str(error),
        )
        raise
