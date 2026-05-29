"""論文AI分析API routerです。"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.clients.supabase import SupabaseConfigError
from app.routers.dependencies import raise_analysis_http_error, raise_storage_http_error
from app.schemas.analyses import (
    PaperAIAnalysisGenerateRequest,
    PaperAIAnalysisResponse,
)
from app.services import paper_analysis_service


router = APIRouter(prefix="/papers", tags=["paper-analyses"])


@router.get(
    "/{paper_id}/analysis",
    response_model=PaperAIAnalysisResponse,
)
def get_paper_ai_analysis(paper_id: UUID) -> PaperAIAnalysisResponse:
    try:
        analysis = paper_analysis_service.get_paper_ai_analysis(paper_id)
    except (
        SupabaseConfigError,
        paper_analysis_service.PaperAnalysisStorageError,
    ) as error:
        raise_storage_http_error(error)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper AI analysis not found",
        )
    return analysis


@router.post(
    "/{paper_id}/analysis/generate",
    response_model=PaperAIAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_paper_ai_analysis(
    paper_id: UUID,
    generate_request: PaperAIAnalysisGenerateRequest,
) -> PaperAIAnalysisResponse:
    try:
        analysis = paper_analysis_service.generate_paper_ai_analysis(
            paper_id,
            generate_request,
        )
    except (
        SupabaseConfigError,
        paper_analysis_service.PaperAnalysisStorageError,
    ) as error:
        raise_storage_http_error(error)
    except (
        paper_analysis_service.PaperAnalysisConfigError,
        paper_analysis_service.PaperAnalysisGenerateError,
    ) as error:
        raise_analysis_http_error(error)

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return analysis
