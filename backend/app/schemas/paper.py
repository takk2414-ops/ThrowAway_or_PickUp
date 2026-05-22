from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

PaperActionType = Literal["pickup", "save", "skip"]
RelatedSignalSourceType = Literal[
    "github",
    "qiita",
    "hacker_news",
    "reddit",
    "x",
    "hugging_face",
    "blog",
    "other",
]


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


class RisingImportRequest(BaseModel):
    # 関連シグナルが出始めた論文を取り込むときの入力形式です。
    categories: list[str] = Field(default_factory=lambda: ["cs.AI", "cs.CL", "cs.LG"])
    max_results_per_category: int = Field(10, ge=1, le=20)
    max_papers: int = Field(10, ge=1, le=20)
    min_days_old: int = Field(14, ge=1, le=365)
    max_days_old: int = Field(60, ge=1, le=365)

    @model_validator(mode="after")
    def validate_day_range(self) -> "RisingImportRequest":
        if self.min_days_old > self.max_days_old:
            raise ValueError("min_days_old must be less than or equal to max_days_old")
        return self


class RisingImportResponse(BaseModel):
    # 関連シグナルがある論文の取り込み結果です。
    imported_count: int
    papers: list[PaperResponse]
    signal_counts: dict[str, int] = Field(default_factory=dict)
    source_errors: list[str] = Field(default_factory=list)


class RelatedSignalBase(BaseModel):
    # 論文に紐づく外部シグナルの共通項目です。
    source_type: RelatedSignalSourceType
    title: str = Field(..., min_length=1, max_length=500)
    source_url: str = Field(..., min_length=1, max_length=1000)
    summary: str | None = None
    published_at: datetime | None = None
    raw_metadata: dict = Field(default_factory=dict)

    @field_validator("title", "source_url")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("value must not be blank")
        return stripped_value


class RelatedSignalCreate(RelatedSignalBase):
    # 外部シグナルを新規登録するときの入力形式です。
    pass


class RelatedSignalResponse(RelatedSignalBase):
    # APIから外部シグナルを返すときの出力形式です。
    id: UUID
    paper_id: UUID
    created_at: datetime
    updated_at: datetime


class RelatedSignalDiscoveryResponse(BaseModel):
    # 外部シグナルの自動探索結果です。
    discovered_count: int
    signals: list[RelatedSignalResponse]
    source_errors: list[str] = Field(default_factory=list)


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
