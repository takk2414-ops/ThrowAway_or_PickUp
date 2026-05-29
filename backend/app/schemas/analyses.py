"""AI分析のschemaです。"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


AIAnalysisProvider = Literal["openai", "gemini"]


class PaperAIAnalysisBase(BaseModel):
    # AIで生成した論文分析結果の共通項目です。
    provider: AIAnalysisProvider
    model: str = Field(..., min_length=1, max_length=100)
    summary_ja: str = Field(..., min_length=1, max_length=3000)
    implementation_difficulty: int = Field(..., ge=1, le=5)
    implementation_reason: str = Field(..., min_length=1, max_length=1500)
    reading_difficulty: int = Field(..., ge=1, le=5)
    reading_reason: str = Field(..., min_length=1, max_length=1500)
    math_difficulty: int = Field(..., ge=1, le=5)
    math_reason: str = Field(..., min_length=1, max_length=1500)
    raw_response: dict = Field(default_factory=dict)

    @field_validator(
        "model",
        "summary_ja",
        "implementation_reason",
        "reading_reason",
        "math_reason",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("value must not be blank")
        return stripped_value


class PaperAIAnalysisCreate(PaperAIAnalysisBase):
    # AI分析結果をDBへ保存するときの入力形式です。
    paper_id: UUID


class PaperAIAnalysisResponse(PaperAIAnalysisBase):
    # APIからAI分析結果を返すときの出力形式です。
    id: UUID
    paper_id: UUID
    created_at: datetime
    updated_at: datetime


class PaperAIAnalysisGenerateRequest(BaseModel):
    # AI分析を生成するときの入力形式です。
    provider: AIAnalysisProvider = "gemini"
    model: str | None = Field(default=None, min_length=1, max_length=100)
    force_refresh: bool = False
