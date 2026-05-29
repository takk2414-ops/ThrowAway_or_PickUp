"""arXiv API から論文情報を取得する client です。"""

from datetime import datetime
from functools import lru_cache
import re
from xml.etree import ElementTree

import httpx

from app.schemas.papers import PaperCreate


ARXIV_API_BASE_URL = "https://export.arxiv.org/api/"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivClientError(RuntimeError):
    """arXiv API への問い合わせやレスポンス解析に失敗した場合のエラーです。"""


@lru_cache
def get_arxiv_client() -> httpx.Client:
    return httpx.Client(
        base_url=ARXIV_API_BASE_URL,
        headers={"User-Agent": "ThrowAway_or_PickUp/0.1"},
        follow_redirects=True,
        timeout=15.0,
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


def _fetch_papers_with_params(params: dict[str, str]) -> list[PaperCreate]:
    last_error: httpx.HTTPError | None = None
    for _ in range(2):
        try:
            response = get_arxiv_client().get("query", params=params)
            response.raise_for_status()
            break
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
