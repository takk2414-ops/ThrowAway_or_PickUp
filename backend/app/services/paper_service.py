"""論文に関するビジネスロジックを担当する service です。"""

from uuid import UUID

from app.clients import arxiv
from app.repositories import paper_repository
from app.schemas.paper import (
    ArxivImportRequest,
    ArxivImportResponse,
    PaperActionCreate,
    PaperActionResponse,
    PaperCreate,
    PaperResponse,
)


PaperStorageError = paper_repository.PaperRepositoryError
PaperImportError = arxiv.ArxivClientError


def list_papers() -> list[PaperResponse]:
    return paper_repository.list_papers()


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


def list_paper_actions(paper_id: UUID) -> list[PaperActionResponse]:
    return paper_repository.list_paper_actions(paper_id)


def clear_papers() -> None:
    raise PaperStorageError(
        "clear_papers is not available for Supabase-backed storage"
    )
