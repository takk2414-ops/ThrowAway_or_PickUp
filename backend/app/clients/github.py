"""GitHub Search API から実装シグナルを取得する client です。"""

from datetime import datetime
from functools import lru_cache

import httpx

from app.schemas.paper import RelatedSignalCreate


GITHUB_API_BASE_URL = "https://api.github.com/"


class GitHubClientError(RuntimeError):
    """GitHub API への問い合わせに失敗した場合のエラーです。"""


@lru_cache
def get_github_client() -> httpx.Client:
    return httpx.Client(
        base_url=GITHUB_API_BASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ThrowAway_or_PickUp/0.1",
        },
        timeout=10.0,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def search_repositories(
    query: str,
    max_results: int,
) -> list[RelatedSignalCreate]:
    try:
        response = get_github_client().get(
            "search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": str(max_results),
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise GitHubClientError("GitHub search request failed") from error

    data = response.json()
    if not isinstance(data, dict):
        raise GitHubClientError("GitHub returned unexpected JSON shape")

    items = data.get("items", [])
    if not isinstance(items, list):
        raise GitHubClientError("GitHub returned unexpected items shape")

    signals: list[RelatedSignalCreate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("full_name")
        source_url = item.get("html_url")
        if not isinstance(title, str) or not isinstance(source_url, str):
            continue

        signals.append(
            RelatedSignalCreate(
                source_type="github",
                title=title,
                source_url=source_url,
                summary=item.get("description"),
                published_at=_parse_datetime(item.get("created_at")),
                raw_metadata={
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "language": item.get("language"),
                    "updated_at": item.get("updated_at"),
                },
            )
        )

    return signals
