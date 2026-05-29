"""論文取り込みAPI routerです。"""

from fastapi import APIRouter, status

from app.clients.supabase import SupabaseConfigError
from app.routers.dependencies import raise_import_http_error, raise_storage_http_error
from app.schemas.imports import (
    ArxivImportRequest,
    ArxivImportResponse,
    DailyImportRequest,
    DailyImportResponse,
    RisingImportRequest,
    RisingImportResponse,
)
from app.services import paper_service, rising_service


router = APIRouter(prefix="/papers/import", tags=["paper-imports"])


@router.post(
    "/daily",
    response_model=DailyImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_daily_papers(
    import_request: DailyImportRequest,
) -> DailyImportResponse:
    try:
        return paper_service.import_daily_papers(import_request)
    except paper_service.PaperImportError as error:
        raise_import_http_error(error)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)


@router.post(
    "/arxiv",
    response_model=ArxivImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_arxiv_papers(
    import_request: ArxivImportRequest,
) -> ArxivImportResponse:
    try:
        return paper_service.import_arxiv_papers(import_request)
    except paper_service.PaperImportError as error:
        raise_import_http_error(error)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)


@router.post(
    "/rising",
    response_model=RisingImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_rising_papers(
    import_request: RisingImportRequest,
) -> RisingImportResponse:
    try:
        return rising_service.import_rising_papers(import_request)
    except rising_service.RisingImportError as error:
        raise_import_http_error(error)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)
