"""arXiv API から論文情報を取得する client です。"""

from datetime import datetime
from functools import lru_cache
import re
import threading
import time
from xml.etree import ElementTree

import httpx

from app.schemas.papers import PaperCreate


ARXIV_API_BASE_URL = "https://export.arxiv.org/api/"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
ARXIV_REQUEST_INTERVAL_SECONDS = 3.1
ARXIV_MAX_ATTEMPTS = 3
ARXIV_DEFAULT_RETRY_AFTER_SECONDS = 10.0
_request_lock = threading.Lock()
_last_request_monotonic = 0.0


class ArxivClientError(RuntimeError):
    """arXiv API への問い合わせやレスポンス解析に失敗した場合のエラーです。"""


class ArxivRateLimitError(ArxivClientError):
    """arXiv API のrate limitに達した場合のエラーです。"""


@lru_cache
def get_arxiv_client() -> httpx.Client:
    return httpx.Client(
        base_url=ARXIV_API_BASE_URL,
        headers={"User-Agent": "ThrowAway_or_PickUp/0.1"},
        follow_redirects=True,
        timeout=httpx.Timeout(60.0, connect=10.0),
    )


def _get_text(element: ElementTree.Element, tag: str) -> str | None:
    child = element.find(tag)
    if child is None or child.text is None:
        return None
    return _normalize_text(child.text)


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ArxivClientError("arXiv returned invalid published date") from error


def _parse_arxiv_id(source_url: str | None) -> str | None:
    if source_url is None:
        return None
    arxiv_id = source_url.rstrip("/").split("/")[-1]
    return re.sub(r"v\d+$", "", arxiv_id)


def _parse_entry(entry: ElementTree.Element) -> PaperCreate:
    source_url = _get_text(entry, f"{ATOM_NS}id")
    title = _get_text(entry, f"{ATOM_NS}title")
    if title is None:
        raise ArxivClientError("arXiv entry does not have title")

    authors = [
        name
        for author in entry.findall(f"{ATOM_NS}author")
        if (name := _get_text(author, f"{ATOM_NS}name")) is not None
    ]

    return PaperCreate(
        title=title,
        abstract=_get_text(entry, f"{ATOM_NS}summary"),
        source_url=source_url,
        arxiv_id=_parse_arxiv_id(source_url),
        doi=_get_text(entry, f"{ARXIV_NS}doi"),
        authors=authors,
        published_at=_parse_datetime(_get_text(entry, f"{ATOM_NS}published")),
    )


def _wait_until_request_allowed() -> None:
    global _last_request_monotonic

    if ARXIV_REQUEST_INTERVAL_SECONDS <= 0:
        return

    now = time.monotonic()
    elapsed = now - _last_request_monotonic
    wait_seconds = ARXIV_REQUEST_INTERVAL_SECONDS - elapsed
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    _last_request_monotonic = time.monotonic()


def _parse_retry_after_seconds(response: httpx.Response) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after is None:
        return ARXIV_DEFAULT_RETRY_AFTER_SECONDS

    try:
        return max(float(retry_after), ARXIV_REQUEST_INTERVAL_SECONDS)
    except ValueError:
        return ARXIV_DEFAULT_RETRY_AFTER_SECONDS


def _request_arxiv(params: dict[str, str]) -> httpx.Response:
    with _request_lock:
        _wait_until_request_allowed()
        return get_arxiv_client().get("query", params=params)


def _fetch_papers_with_params(params: dict[str, str]) -> list[PaperCreate]:
    last_error: httpx.HTTPError | None = None
    for attempt in range(ARXIV_MAX_ATTEMPTS):
        try:
            response = _request_arxiv(params)
            response.raise_for_status()
            break
        except httpx.HTTPStatusError as error:
            last_error = error
            if error.response.status_code != 429:
                continue
            if attempt >= ARXIV_MAX_ATTEMPTS - 1:
                raise ArxivRateLimitError(
                    "arXiv rate limit exceeded"
                ) from error
            time.sleep(_parse_retry_after_seconds(error.response))
        except httpx.HTTPError as error:
            last_error = error
    else:
        raise ArxivClientError("arXiv request failed") from last_error

    try:
        root = ElementTree.fromstring(response.text)
    except ElementTree.ParseError as error:
        raise ArxivClientError("arXiv returned invalid XML") from error

    return [
        _parse_entry(entry)
        for entry in root.findall(f"{ATOM_NS}entry")
    ]


def fetch_papers(
    search_query: str,
    max_results: int,
) -> list[PaperCreate]:
    return _fetch_papers_with_params(
        {
            "search_query": search_query,
            "start": "0",
            "max_results": str(max_results),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )


def fetch_papers_by_ids(arxiv_ids: list[str]) -> list[PaperCreate]:
    if not arxiv_ids:
        return []

    return _fetch_papers_with_params(
        {
            "id_list": ",".join(arxiv_ids),
            "max_results": str(len(arxiv_ids)),
        }
    )
