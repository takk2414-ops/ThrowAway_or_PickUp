"""Qiita API から日本語記事シグナルを取得する client です。"""

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from functools import lru_cache
import re

import httpx

from app.config import get_settings
from app.schemas.signals import RelatedSignalCreate


QIITA_API_BASE_URL = "https://qiita.com/api/v2/"


class QiitaClientError(RuntimeError):
    """Qiita API への問い合わせに失敗した場合のエラーです。"""


@dataclass(frozen=True)
class QiitaArxivArticle:
    arxiv_id: str
    signal: RelatedSignalCreate


@lru_cache
def get_qiita_client() -> httpx.Client:
    settings = get_settings()
    headers = {"User-Agent": "ThrowAway_or_PickUp/0.1"}
    if settings.qiita_access_token:
        headers["Authorization"] = f"Bearer {settings.qiita_access_token}"

    return httpx.Client(
        base_url=QIITA_API_BASE_URL,
        headers=headers,
        timeout=10.0,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_arxiv_ids(*values: object) -> list[str]:
    arxiv_ids: list[str] = []
    seen_ids: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        for matched_id in re.findall(r"\b\d{4}\.\d{4,5}(?:v\d+)?\b", value):
            arxiv_id = re.sub(r"v\d+$", "", matched_id)
            if arxiv_id in seen_ids:
                continue
            seen_ids.add(arxiv_id)
            arxiv_ids.append(arxiv_id)
    return arxiv_ids


def _build_signal_from_item(item: dict) -> RelatedSignalCreate | None:
    title = item.get("title")
    source_url = item.get("url")
    if not isinstance(title, str) or not isinstance(source_url, str):
        return None

    user = item.get("user") if isinstance(item.get("user"), dict) else {}
    return RelatedSignalCreate(
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
        signal = _build_signal_from_item(item)
        if signal is None:
            continue
        signals.append(signal)

    return signals


def search_recent_arxiv_articles(
    created_after: date,
    max_results: int,
) -> list[QiitaArxivArticle]:
    try:
        response = get_qiita_client().get(
            "items",
            params={
                "query": "arxiv",
                "per_page": str(min(max_results, 100)),
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise QiitaClientError("Qiita arXiv article search request failed") from error

    data = response.json()
    if not isinstance(data, list):
        raise QiitaClientError("Qiita returned unexpected JSON shape")

    articles: list[QiitaArxivArticle] = []
    seen_pairs: set[tuple[str, str]] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        signal = _build_signal_from_item(item)
        if signal is None:
            continue
        if signal.published_at is None or signal.published_at.date() < created_after:
            continue
        arxiv_ids = _extract_arxiv_ids(
            item.get("title"),
            item.get("url"),
            item.get("body"),
            item.get("rendered_body"),
        )
        for arxiv_id in arxiv_ids:
            key = (arxiv_id, signal.source_url)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            articles.append(QiitaArxivArticle(arxiv_id=arxiv_id, signal=signal))

    return articles
