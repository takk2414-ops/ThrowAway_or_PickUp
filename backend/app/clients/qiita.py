"""Qiita API から日本語記事シグナルを取得する client です。"""

from datetime import datetime
from functools import lru_cache

import httpx

from app.schemas.paper import RelatedSignalCreate


QIITA_API_BASE_URL = "https://qiita.com/api/v2/"


class QiitaClientError(RuntimeError):
    """Qiita API への問い合わせに失敗した場合のエラーです。"""


@lru_cache
def get_qiita_client() -> httpx.Client:
    return httpx.Client(
        base_url=QIITA_API_BASE_URL,
        headers={"User-Agent": "ThrowAway_or_PickUp/0.1"},
        timeout=10.0,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def search_items(
    query: str,
    max_results: int,
) -> list[RelatedSignalCreate]:
    try:
        response = get_qiita_client().get(
            "items",
            params={
                "query": query,
                "per_page": str(max_results),
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise QiitaClientError("Qiita search request failed") from error

    data = response.json()
    if not isinstance(data, list):
        raise QiitaClientError("Qiita returned unexpected JSON shape")

    signals: list[RelatedSignalCreate] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        source_url = item.get("url")
        if not isinstance(title, str) or not isinstance(source_url, str):
            continue

        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        signals.append(
            RelatedSignalCreate(
                source_type="qiita",
                title=title,
                source_url=source_url,
                summary=None,
                published_at=_parse_datetime(item.get("created_at")),
                raw_metadata={
                    "likes_count": item.get("likes_count"),
                    "stocks_count": item.get("stocks_count"),
                    "user_id": user.get("id"),
                    "tags": [
                        tag.get("name")
                        for tag in item.get("tags", [])
                        if isinstance(tag, dict) and tag.get("name")
                    ],
                },
            )
        )

    return signals
