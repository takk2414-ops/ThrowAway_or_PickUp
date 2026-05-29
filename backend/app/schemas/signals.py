"""論文に紐づく外部シグナルのschemaです。"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
