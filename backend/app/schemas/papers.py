"""論文本体のschemaです。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PaperBase(BaseModel):
    # 論文データで共通して使う基本項目です。
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str | None = None
    source_url: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    authors: list[str] = Field(default_factory=list)
    institutions: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=200)
    published_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        # 空白だけのタイトルは論文データとして扱えないため拒否します。
        stripped_title = title.strip()
        if not stripped_title:
            raise ValueError("title must not be blank")
        return stripped_title

    @field_validator("location")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped_value = value.strip()
        return stripped_value or None


class PaperCreate(PaperBase):
    # 論文を新規登録するときの入力形式です。
    pass


class PaperResponse(PaperBase):
    # APIから論文情報を返すときの出力形式です。
    id: UUID
    created_at: datetime
    updated_at: datetime
    daily_selection_reason: str | None = None
