"""論文に関するビジネスロジックを担当する場所です。

router はHTTPリクエストとレスポンスを扱い、
service は「論文を検索する」「論文を保存する」などの処理を担当します。
"""

from uuid import UUID

import httpx

from app.clients.supabase import SupabaseConfigError, get_supabase_client
from app.schemas.paper import (
    PaperActionCreate,
    PaperActionResponse,
    PaperCreate,
    PaperResponse,
)


class PaperStorageError(RuntimeError):
    """論文データの保存・取得に失敗した場合のエラーです。"""


def _request_supabase(
    method: str,
    path: str,
    *,
    json: dict | None = None,
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
        raise PaperStorageError(
            f"Supabase request failed with status {status_code}"
        ) from error
    except httpx.HTTPError as error:
        raise PaperStorageError("Supabase request failed") from error


def _read_rows(response: httpx.Response) -> list[dict]:
    try:
        data = response.json()
    except ValueError as error:
        raise PaperStorageError("Supabase returned invalid JSON") from error

    if not isinstance(data, list):
        raise PaperStorageError("Supabase returned unexpected JSON shape")

    return data


def _read_single_row(response: httpx.Response) -> dict:
    rows = _read_rows(response)
    if not rows:
        raise PaperStorageError("Supabase did not return created row")
    first_row = rows[0]
    if not isinstance(first_row, dict):
        raise PaperStorageError("Supabase returned unexpected row shape")
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


def create_paper_action(
    paper_id: UUID,
    paper_action_create: PaperActionCreate,
    user_id: UUID,
) -> PaperActionResponse | None:
    if get_paper(paper_id) is None:
        return None

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


def clear_papers() -> None:
    raise PaperStorageError(
        "clear_papers is not available for Supabase-backed storage"
    )
