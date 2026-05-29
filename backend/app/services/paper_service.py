"""論文に関するビジネスロジックを担当する service です。"""

from datetime import date
from uuid import UUID

from app.clients import arxiv
from app.repositories import paper_repository
from app.schemas.actions import PaperActionCreate, PaperActionResponse
from app.schemas.imports import (
    ArxivImportRequest,
    ArxivImportResponse,
    DailyImportRequest,
    DailyImportResponse,
)
from app.schemas.papers import PaperCreate, PaperResponse
from app.schemas.signals import (
    RelatedSignalCreate,
    RelatedSignalDiscoveryResponse,
    RelatedSignalResponse,
)
from app.services import daily_feed_service, signal_discovery_service
from app.utils.time import today_jst


PaperStorageError = paper_repository.PaperRepositoryError
PaperImportError = arxiv.ArxivClientError


def list_papers() -> list[PaperResponse]:
    return paper_repository.list_papers()


def list_today_papers(target_date: date | None = None) -> list[PaperResponse]:
    import_date = target_date or today_jst()
    return paper_repository.list_today_papers(import_date)


def get_paper(paper_id: UUID) -> PaperResponse | None:
    return paper_repository.get_paper(paper_id)


def create_paper(paper_create: PaperCreate) -> PaperResponse:
    return paper_repository.create_paper(paper_create)


def import_arxiv_papers(
    import_request: ArxivImportRequest,
) -> ArxivImportResponse:
    paper_creates = arxiv.fetch_papers(
        search_query=import_request.search_query,
        max_results=import_request.max_results,
    )
    papers = paper_repository.upsert_papers_by_arxiv_id(paper_creates)
    return ArxivImportResponse(
        imported_count=len(papers),
        papers=papers,
    )


def import_daily_papers(
    import_request: DailyImportRequest,
) -> DailyImportResponse:
    return daily_feed_service.import_daily_feed(import_request)


def create_paper_action(
    paper_id: UUID,
    paper_action_create: PaperActionCreate,
    user_id: UUID,
) -> PaperActionResponse | None:
    if paper_repository.get_paper(paper_id) is None:
        return None

    return paper_repository.create_paper_action(
        paper_id,
        paper_action_create,
        user_id,
    )


def list_related_signals(paper_id: UUID) -> list[RelatedSignalResponse] | None:
    if paper_repository.get_paper(paper_id) is None:
        return None

    return paper_repository.list_related_signals(paper_id)


def create_related_signal(
    paper_id: UUID,
    related_signal_create: RelatedSignalCreate,
) -> RelatedSignalResponse | None:
    if paper_repository.get_paper(paper_id) is None:
        return None

    return paper_repository.create_related_signal(
        paper_id,
        related_signal_create,
    )


def discover_related_signals(
    paper_id: UUID,
    max_results_per_source: int = 3,
) -> RelatedSignalDiscoveryResponse | None:
    paper = paper_repository.get_paper(paper_id)
    if paper is None:
        return None

    return signal_discovery_service.discover_and_save_related_signals(
        paper,
        max_results_per_source,
    )


def list_paper_actions(paper_id: UUID) -> list[PaperActionResponse]:
    return paper_repository.list_paper_actions(paper_id)


def list_picked_papers(user_id: UUID) -> list[PaperResponse]:
    latest_actions_by_paper: dict[UUID, PaperActionResponse] = {}
    for action in paper_repository.list_user_paper_actions(user_id):
        if action.paper_id not in latest_actions_by_paper:
            latest_actions_by_paper[action.paper_id] = action

    picked_papers: list[PaperResponse] = []
    for paper_id, action in latest_actions_by_paper.items():
        if action.action != "pickup":
            continue
        paper = paper_repository.get_paper(paper_id)
        if paper is not None:
            picked_papers.append(paper)
    return picked_papers


def clear_papers() -> None:
    raise PaperStorageError(
        "clear_papers is not available for Supabase-backed storage"
    )
