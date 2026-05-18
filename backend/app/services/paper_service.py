"""論文に関するビジネスロジックを担当する場所です。

router はHTTPリクエストとレスポンスを扱い、
service は「論文を検索する」「論文を保存する」などの処理を担当します。
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas.paper import (
    PaperActionCreate,
    PaperActionResponse,
    PaperCreate,
    PaperResponse,
)


_papers: dict[UUID, PaperResponse] = {}
_paper_actions: list[PaperActionResponse] = []


def list_papers() -> list[PaperResponse]:
    # 新しく登録された論文を先に返します。
    return sorted(
        _papers.values(),
        key=lambda paper: paper.created_at,
        reverse=True,
    )


def get_paper(paper_id: UUID) -> PaperResponse | None:
    return _papers.get(paper_id)


def create_paper(paper_create: PaperCreate) -> PaperResponse:
    now = datetime.now(UTC)
    paper = PaperResponse(
        id=uuid4(),
        created_at=now,
        updated_at=now,
        **paper_create.model_dump(),
    )
    _papers[paper.id] = paper
    return paper


def create_paper_action(
    paper_id: UUID,
    paper_action_create: PaperActionCreate,
) -> PaperActionResponse | None:
    if paper_id not in _papers:
        return None

    action = PaperActionResponse(
        id=uuid4(),
        paper_id=paper_id,
        created_at=datetime.now(UTC),
        **paper_action_create.model_dump(),
    )
    _paper_actions.append(action)
    return action


def list_paper_actions(paper_id: UUID) -> list[PaperActionResponse]:
    return [
        action
        for action in _paper_actions
        if action.paper_id == paper_id
    ]


def clear_papers() -> None:
    # テストから状態を初期化するための関数です。
    _papers.clear()
    _paper_actions.clear()
