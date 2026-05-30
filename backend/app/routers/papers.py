"""論文本体API routerです。"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.clients.supabase import SupabaseConfigError
from app.routers.dependencies import raise_import_http_error, raise_storage_http_error
from app.schemas.papers import PaperCreate, PaperResponse
from app.services import paper_service


router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[PaperResponse])
def list_papers() -> list[PaperResponse]:
    try:
        return paper_service.list_papers()
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)


@router.get("/today", response_model=list[PaperResponse])
def list_today_papers() -> list[PaperResponse]:
    try:
        return paper_service.list_or_import_today_papers()
    except paper_service.PaperImportError as error:
        raise_import_http_error(error)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: UUID) -> PaperResponse:
    try:
        paper = paper_service.get_paper(paper_id)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return paper


@router.post("", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
def create_paper(paper_create: PaperCreate) -> PaperResponse:
    try:
        return paper_service.create_paper(paper_create)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)
