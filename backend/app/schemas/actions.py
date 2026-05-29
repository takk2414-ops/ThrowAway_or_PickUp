"""ユーザーの論文判定action schemaです。"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


PaperActionType = Literal["pickup", "save", "skip"]


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
