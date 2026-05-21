from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

PaperActionType = Literal["pickup", "save", "skip"]


class PaperBase(BaseModel):
    # 論文データで共通して使う基本項目です。
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str | None = None
    source_url: str | None = None
    arxiv_id: str | None = None
    doi: str | None = None
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        # 空白だけのタイトルは論文データとして扱えないため拒否します。
        stripped_title = title.strip()
        if not stripped_title:
            raise ValueError("title must not be blank")
        return stripped_title


class PaperCreate(PaperBase):
    # 論文を新規登録するときの入力形式です。
    pass


class PaperResponse(PaperBase):
    # APIから論文情報を返すときの出力形式です。
    id: UUID
    created_at: datetime
    updated_at: datetime


class ArxivImportRequest(BaseModel):
    # arXiv APIから論文を取り込むときの入力形式です。
    search_query: str = Field("cat:cs.AI", min_length=1, max_length=200)
    max_results: int = Field(10, ge=1, le=50)


class ArxivImportResponse(BaseModel):
    # arXiv APIから取り込んだ論文の結果です。
    imported_count: int
    papers: list[PaperResponse]


class PaperActionCreate(BaseModel):
    # ユーザーが論文に対して行う判定です。
    action: PaperActionType
    reason: str | None = None


class PaperActionResponse(PaperActionCreate):
    # APIから判定履歴を返すときの出力形式です。
    id: UUID
    paper_id: UUID
    user_id: UUID | None = None
    created_at: datetime
