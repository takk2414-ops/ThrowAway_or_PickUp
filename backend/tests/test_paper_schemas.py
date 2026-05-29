"""論文関連Pydantic schemaのテストです。"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.paper import PaperAIAnalysisCreate


def build_analysis_payload() -> dict:
    return {
        "paper_id": uuid4(),
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "summary_ja": "RAGの検索精度を改善する手法を提案している論文です。",
        "implementation_difficulty": 3,
        "implementation_reason": "既存の検索基盤があれば実装しやすいためです。",
        "reading_difficulty": 2,
        "reading_reason": "Abstractの主張が比較的明確なためです。",
        "math_difficulty": 2,
        "math_reason": "高度な数式よりもシステム設計の説明が中心のためです。",
        "raw_response": {"provider": "openai"},
    }


def test_paper_ai_analysis_create_accepts_valid_payload() -> None:
    analysis = PaperAIAnalysisCreate.model_validate(build_analysis_payload())

    assert analysis.provider == "openai"
    assert analysis.implementation_difficulty == 3


def test_paper_ai_analysis_create_rejects_invalid_difficulty() -> None:
    payload = build_analysis_payload()
    payload["math_difficulty"] = 6

    with pytest.raises(ValidationError):
        PaperAIAnalysisCreate.model_validate(payload)


def test_paper_ai_analysis_create_rejects_blank_required_text() -> None:
    payload = build_analysis_payload()
    payload["summary_ja"] = "   "

    with pytest.raises(ValidationError):
        PaperAIAnalysisCreate.model_validate(payload)
