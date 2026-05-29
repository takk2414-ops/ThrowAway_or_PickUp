"""Supabase上の論文データへアクセスする repository です。"""

from datetime import date
from uuid import UUID

import httpx

from app.clients.supabase import SupabaseConfigError, get_supabase_client
from app.schemas.actions import PaperActionCreate, PaperActionResponse
from app.schemas.analyses import PaperAIAnalysisCreate, PaperAIAnalysisResponse
from app.schemas.papers import PaperCreate, PaperResponse
from app.schemas.signals import RelatedSignalCreate, RelatedSignalResponse


class PaperRepositoryError(RuntimeError):
    """論文データの保存・取得に失敗した場合のエラーです。"""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        supabase_code: str | None = None,
        supabase_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.supabase_code = supabase_code
        self.supabase_message = supabase_message


def _read_supabase_error(response: httpx.Response) -> tuple[str | None, str | None]:
    try:
        data = response.json()
    except ValueError:
        return None, None

    if not isinstance(data, dict):
        return None, None

    code = data.get("code")
    message = data.get("message")
    return (
        code if isinstance(code, str) else None,
        message if isinstance(message, str) else None,
    )


def _request_supabase(
    method: str,
    path: str,
    *,
    json: dict | list[dict] | None = None,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    try:
        response = get_supabase_client().request(
            method,
            path,
            json=json,
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        return response
    except SupabaseConfigError:
        raise
    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        supabase_code, supabase_message = _read_supabase_error(error.response)
        raise PaperRepositoryError(
            f"Supabase request failed with status {status_code}",
            status_code=status_code,
            supabase_code=supabase_code,
            supabase_message=supabase_message,
        ) from error
    except httpx.HTTPError as error:
        raise PaperRepositoryError("Supabase request failed") from error


def _read_rows(response: httpx.Response) -> list[dict]:
    try:
        data = response.json()
    except ValueError as error:
        raise PaperRepositoryError("Supabase returned invalid JSON") from error

    if not isinstance(data, list):
        raise PaperRepositoryError("Supabase returned unexpected JSON shape")

    return data


def _read_single_row(response: httpx.Response) -> dict:
    rows = _read_rows(response)
    if not rows:
        raise PaperRepositoryError("Supabase did not return created row")
    first_row = rows[0]
    if not isinstance(first_row, dict):
        raise PaperRepositoryError("Supabase returned unexpected row shape")
    return first_row


def list_papers() -> list[PaperResponse]:
    response = _request_supabase(
        "GET",
        "papers",
        params={
            "select": "*",
            "order": "created_at.desc",
        },
    )
    return [PaperResponse.model_validate(row) for row in _read_rows(response)]


def list_today_papers(target_date: date) -> list[PaperResponse]:
    response = _request_supabase(
        "GET",
        "daily_paper_items",
        params={
            "select": "paper_id,selection_reason",
            "target_date": f"eq.{target_date.isoformat()}",
            "order": "display_order.asc",
        },
    )
    daily_items = _read_rows(response)

    papers: list[PaperResponse] = []
    for row in daily_items:
        if not isinstance(row.get("paper_id"), str):
            continue
        paper_id = UUID(row["paper_id"])
        paper = get_paper(paper_id)
        if paper is not None:
            paper_data = paper.model_dump()
            paper_data["daily_selection_reason"] = row.get("selection_reason")
            papers.append(PaperResponse.model_validate(paper_data))
    return papers


def get_paper(paper_id: UUID) -> PaperResponse | None:
    response = _request_supabase(
        "GET",
        "papers",
        params={
            "select": "*",
            "id": f"eq.{paper_id}",
            "limit": "1",
        },
    )
    rows = _read_rows(response)
    if not rows:
        return None
    return PaperResponse.model_validate(rows[0])


def create_paper(paper_create: PaperCreate) -> PaperResponse:
    response = _request_supabase(
        "POST",
        "papers",
        json=paper_create.model_dump(mode="json"),
        headers={"Prefer": "return=representation"},
    )
    return PaperResponse.model_validate(_read_single_row(response))


def upsert_papers_by_arxiv_id(
    paper_creates: list[PaperCreate],
) -> list[PaperResponse]:
    if not paper_creates:
        return []

    response = _request_supabase(
        "POST",
        "papers",
        json=[
            paper_create.model_dump(mode="json")
            for paper_create in paper_creates
        ],
        params={"on_conflict": "arxiv_id"},
        headers={"Prefer": "return=representation,resolution=merge-duplicates"},
    )
    return [
        PaperResponse.model_validate(row)
        for row in _read_rows(response)
    ]


def create_daily_paper_items(
    target_date: date,
    papers: list[PaperResponse],
    *,
    selection_reason: str = "daily_arxiv_import",
    start_order: int = 1,
) -> None:
    if not papers:
        return

    payload = [
        {
            "paper_id": str(paper.id),
            "target_date": target_date.isoformat(),
            "display_order": index,
            "selection_reason": selection_reason,
        }
        for index, paper in enumerate(papers, start=start_order)
    ]
    _request_supabase(
        "POST",
        "daily_paper_items",
        json=payload,
        params={"on_conflict": "target_date,paper_id"},
        headers={"Prefer": "resolution=merge-duplicates"},
    )


def has_successful_daily_import(
    import_date: date,
    source: str,
) -> bool:
    response = _request_supabase(
        "GET",
        "daily_import_runs",
        params={
            "select": "id",
            "import_date": f"eq.{import_date.isoformat()}",
            "source": f"eq.{source}",
            "status": "eq.success",
            "limit": "1",
        },
    )
    return len(_read_rows(response)) > 0


def create_daily_import_run(
    import_date: date,
    source: str,
    status: str,
    imported_count: int,
    error_message: str | None = None,
) -> None:
    _request_supabase(
        "POST",
        "daily_import_runs",
        json={
            "import_date": import_date.isoformat(),
            "source": source,
            "status": status,
            "imported_count": imported_count,
            "error_message": error_message,
        },
        params={"on_conflict": "import_date,source"},
        headers={"Prefer": "resolution=merge-duplicates"},
    )


def create_paper_action(
    paper_id: UUID,
    paper_action_create: PaperActionCreate,
    user_id: UUID,
) -> PaperActionResponse:
    payload = {
        "paper_id": str(paper_id),
        "user_id": str(user_id),
        **paper_action_create.model_dump(mode="json"),
    }
    response = _request_supabase(
        "POST",
        "user_paper_actions",
        json=payload,
        headers={"Prefer": "return=representation"},
    )
    return PaperActionResponse.model_validate(_read_single_row(response))


def list_related_signals(paper_id: UUID) -> list[RelatedSignalResponse]:
    response = _request_supabase(
        "GET",
        "related_signals",
        params={
            "select": "*",
            "paper_id": f"eq.{paper_id}",
            "source_type": "neq.zenn",
            "order": "published_at.desc.nullslast,created_at.desc",
        },
    )
    return [
        RelatedSignalResponse.model_validate(row)
        for row in _read_rows(response)
    ]


def create_related_signal(
    paper_id: UUID,
    related_signal_create: RelatedSignalCreate,
) -> RelatedSignalResponse:
    payload = {
        "paper_id": str(paper_id),
        **related_signal_create.model_dump(mode="json"),
    }
    response = _request_supabase(
        "POST",
        "related_signals",
        json=payload,
        params={"on_conflict": "paper_id,source_url"},
        headers={"Prefer": "return=representation,resolution=merge-duplicates"},
    )
    return RelatedSignalResponse.model_validate(_read_single_row(response))


def get_paper_ai_analysis(
    paper_id: UUID,
    provider: str,
    model: str,
) -> PaperAIAnalysisResponse | None:
    response = _request_supabase(
        "GET",
        "paper_ai_analyses",
        params={
            "select": "*",
            "paper_id": f"eq.{paper_id}",
            "provider": f"eq.{provider}",
            "model": f"eq.{model}",
            "limit": "1",
        },
    )
    rows = _read_rows(response)
    if not rows:
        return None
    return PaperAIAnalysisResponse.model_validate(rows[0])


def upsert_paper_ai_analysis(
    analysis_create: PaperAIAnalysisCreate,
) -> PaperAIAnalysisResponse:
    response = _request_supabase(
        "POST",
        "paper_ai_analyses",
        json=analysis_create.model_dump(mode="json"),
        params={"on_conflict": "paper_id,provider,model"},
        headers={"Prefer": "return=representation,resolution=merge-duplicates"},
    )
    return PaperAIAnalysisResponse.model_validate(_read_single_row(response))


def list_paper_actions(paper_id: UUID) -> list[PaperActionResponse]:
    response = _request_supabase(
        "GET",
        "user_paper_actions",
        params={
            "select": "*",
            "paper_id": f"eq.{paper_id}",
            "order": "created_at.asc",
        },
    )
    return [
        PaperActionResponse.model_validate(row)
        for row in _read_rows(response)
    ]


def list_user_paper_actions(user_id: UUID) -> list[PaperActionResponse]:
    response = _request_supabase(
        "GET",
        "user_paper_actions",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
        },
    )
    return [
        PaperActionResponse.model_validate(row)
        for row in _read_rows(response)
    ]
