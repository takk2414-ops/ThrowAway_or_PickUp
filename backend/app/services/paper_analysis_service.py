"""論文AI分析の取得・生成を担当する service です。"""

from uuid import UUID

from app.clients import gemini
from app.config import get_settings
from app.repositories import paper_repository
from app.schemas.analyses import (
    PaperAIAnalysisGenerateRequest,
    PaperAIAnalysisResponse,
)


PaperAnalysisStorageError = paper_repository.PaperRepositoryError
PaperAnalysisConfigError = gemini.GeminiConfigError
PaperAnalysisGenerateError = gemini.GeminiClientError


def _resolve_model(requested_model: str | None) -> str:
    return requested_model or get_settings().gemini_analysis_model


def get_paper_ai_analysis(
    paper_id: UUID,
    provider: str = "gemini",
    model: str | None = None,
) -> PaperAIAnalysisResponse | None:
    resolved_model = _resolve_model(model)
    return paper_repository.get_paper_ai_analysis(
        paper_id=paper_id,
        provider=provider,
        model=resolved_model,
    )


def generate_paper_ai_analysis(
    paper_id: UUID,
    generate_request: PaperAIAnalysisGenerateRequest,
) -> PaperAIAnalysisResponse | None:
    paper = paper_repository.get_paper(paper_id)
    if paper is None:
        return None

    resolved_model = _resolve_model(generate_request.model)
    if not generate_request.force_refresh:
        existing_analysis = paper_repository.get_paper_ai_analysis(
            paper_id=paper_id,
            provider=generate_request.provider,
            model=resolved_model,
        )
        if (
            existing_analysis is not None
            and existing_analysis.title_ja is not None
            and existing_analysis.what_is_it_ja is not None
            and existing_analysis.novelty_ja is not None
            and existing_analysis.why_it_matters_ja is not None
            and existing_analysis.recommended_for_ja is not None
        ):
            return existing_analysis

    if generate_request.provider != "gemini":
        raise PaperAnalysisConfigError("Only Gemini analysis is implemented")

    analysis_create = gemini.analyze_paper_abstract(paper, resolved_model)
    return paper_repository.upsert_paper_ai_analysis(analysis_create)
