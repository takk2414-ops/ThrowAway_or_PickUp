"""papers APIのテストです。

GET /papers、GET /papers/{paper_id}、POST /papers、
POST /papers/{paper_id}/actions の最小動作を確認します。
"""

import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from uuid import UUID, uuid4
from zipfile import ZipFile

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients import arxiv as arxiv_client
from app.clients import gemini as gemini_client
from app.clients import github as github_client
from app.clients import qiita as qiita_client
from app.main import app
from app.repositories import paper_repository
from app.schemas.paper import (
    PaperAIAnalysisCreate,
    PaperCreate,
    PaperResponse,
    RelatedSignalCreate,
    RelatedSignalDiscoveryResponse,
    RelatedSignalResponse,
    RelatedSignalSourceType,
)
from app.services import auth_service
from app.services import daily_feed_service
from app.services import paper_export_service
from app.services import rising_service
from app.services.paper_service import list_paper_actions


client = TestClient(app)
TEST_USER_ID = "9ce94211-1471-413f-9699-990da998064e"
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


@pytest.fixture(autouse=True)
def supabase_mock(monkeypatch: pytest.MonkeyPatch):
    storage: dict[str, dict | list] = {
        "papers": {},
        "actions": [],
        "daily_import_runs": [],
        "daily_paper_items": [],
        "paper_ai_analyses": [],
        "related_signals": [],
    }

    def now_iso() -> str:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def read_json(request: httpx.Request) -> dict:
        if not request.content:
            return {}
        return json.loads(request.content.decode("utf-8"))

    def build_paper_row(payload: dict) -> dict:
        now = now_iso()
        return {
            "id": str(uuid4()),
            "title": payload["title"],
            "abstract": payload.get("abstract"),
            "source_url": payload.get("source_url"),
            "arxiv_id": payload.get("arxiv_id"),
            "doi": payload.get("doi"),
            "authors": payload.get("authors", []),
            "published_at": payload.get("published_at"),
            "created_at": now,
            "updated_at": now,
        }

    def upsert_paper_row(payload: dict) -> dict:
        papers = storage["papers"]
        if not isinstance(papers, dict):
            raise AssertionError("papers storage must be a dict")

        arxiv_id = payload.get("arxiv_id")
        if arxiv_id:
            for paper_id, paper in papers.items():
                if paper["arxiv_id"] == arxiv_id:
                    paper.update(
                        {
                            "title": payload["title"],
                            "abstract": payload.get("abstract"),
                            "source_url": payload.get("source_url"),
                            "doi": payload.get("doi"),
                            "authors": payload.get("authors", []),
                            "published_at": payload.get("published_at"),
                            "updated_at": now_iso(),
                        }
                    )
                    papers[paper_id] = paper
                    return paper

        row = build_paper_row(payload)
        papers[row["id"]] = row
        return row

    def build_action_row(payload: dict) -> dict:
        return {
            "id": str(uuid4()),
            "paper_id": payload["paper_id"],
            "user_id": payload["user_id"],
            "action": payload["action"],
            "reason": payload.get("reason"),
            "created_at": now_iso(),
        }

    def build_related_signal_row(payload: dict) -> dict:
        now = now_iso()
        return {
            "id": str(uuid4()),
            "paper_id": payload["paper_id"],
            "source_type": payload["source_type"],
            "title": payload["title"],
            "source_url": payload["source_url"],
            "summary": payload.get("summary"),
            "published_at": payload.get("published_at"),
            "raw_metadata": payload.get("raw_metadata", {}),
            "created_at": now,
            "updated_at": now,
        }

    def build_daily_paper_item_row(payload: dict) -> dict:
        return {
            "id": str(uuid4()),
            "paper_id": payload["paper_id"],
            "target_date": payload["target_date"],
            "display_order": payload["display_order"],
            "selection_reason": payload.get("selection_reason"),
            "created_at": now_iso(),
        }

    def build_daily_import_run_row(payload: dict) -> dict:
        now = now_iso()
        return {
            "id": str(uuid4()),
            "import_date": payload["import_date"],
            "source": payload["source"],
            "status": payload["status"],
            "imported_count": payload.get("imported_count", 0),
            "error_message": payload.get("error_message"),
            "started_at": now,
            "finished_at": now,
            "updated_at": now,
        }

    def build_paper_ai_analysis_row(payload: dict) -> dict:
        now = now_iso()
        return {
            "id": str(uuid4()),
            "paper_id": payload["paper_id"],
            "provider": payload["provider"],
            "model": payload["model"],
            "summary_ja": payload["summary_ja"],
            "implementation_difficulty": payload["implementation_difficulty"],
            "implementation_reason": payload["implementation_reason"],
            "reading_difficulty": payload["reading_difficulty"],
            "reading_reason": payload["reading_reason"],
            "math_difficulty": payload["math_difficulty"],
            "math_reason": payload["math_reason"],
            "raw_response": payload.get("raw_response", {}),
            "created_at": now,
            "updated_at": now,
        }

    def handle_papers_request(request: httpx.Request) -> httpx.Response:
        papers = storage["papers"]
        if not isinstance(papers, dict):
            raise AssertionError("papers storage must be a dict")

        if request.method == "GET":
            paper_id_filter = request.url.params.get("id")
            rows = list(papers.values())
            if paper_id_filter and paper_id_filter.startswith("eq."):
                paper_id = paper_id_filter.removeprefix("eq.")
                rows = [paper for paper in rows if paper["id"] == paper_id]
            rows = sorted(
                rows,
                key=lambda paper: paper["created_at"],
                reverse=True,
            )
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            payload = read_json(request)
            if isinstance(payload, list):
                rows = [upsert_paper_row(item) for item in payload]
                return httpx.Response(201, json=rows)

            row = build_paper_row(payload)
            papers[row["id"]] = row
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_actions_request(request: httpx.Request) -> httpx.Response:
        actions = storage["actions"]
        if not isinstance(actions, list):
            raise AssertionError("actions storage must be a list")

        if request.method == "GET":
            paper_id_filter = request.url.params.get("paper_id")
            user_id_filter = request.url.params.get("user_id")
            order = request.url.params.get("order", "")
            rows = actions
            if paper_id_filter and paper_id_filter.startswith("eq."):
                paper_id = paper_id_filter.removeprefix("eq.")
                rows = [
                    action
                    for action in rows
                    if action["paper_id"] == paper_id
                ]
            if user_id_filter and user_id_filter.startswith("eq."):
                user_id = user_id_filter.removeprefix("eq.")
                rows = [
                    action
                    for action in rows
                    if action["user_id"] == user_id
                ]
            if order == "created_at.desc":
                rows = list(reversed(rows))
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            row = build_action_row(read_json(request))
            actions.append(row)
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_related_signals_request(request: httpx.Request) -> httpx.Response:
        related_signals = storage["related_signals"]
        if not isinstance(related_signals, list):
            raise AssertionError("related_signals storage must be a list")

        if request.method == "GET":
            paper_id_filter = request.url.params.get("paper_id")
            rows = related_signals
            if paper_id_filter and paper_id_filter.startswith("eq."):
                paper_id = paper_id_filter.removeprefix("eq.")
                rows = [
                    signal
                    for signal in rows
                    if signal["paper_id"] == paper_id
                ]
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            row = build_related_signal_row(read_json(request))
            related_signals.append(row)
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_daily_paper_items_request(request: httpx.Request) -> httpx.Response:
        daily_paper_items = storage["daily_paper_items"]
        if not isinstance(daily_paper_items, list):
            raise AssertionError("daily_paper_items storage must be a list")

        if request.method == "GET":
            target_date_filter = request.url.params.get("target_date")
            rows = daily_paper_items
            if target_date_filter and target_date_filter.startswith("eq."):
                target_date = target_date_filter.removeprefix("eq.")
                rows = [
                    item
                    for item in rows
                    if item["target_date"] == target_date
                ]
            rows = sorted(rows, key=lambda item: item["display_order"])
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            payload = read_json(request)
            if not isinstance(payload, list):
                payload = [payload]
            rows = [build_daily_paper_item_row(item) for item in payload]
            daily_paper_items.extend(rows)
            return httpx.Response(201, json=rows)

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_daily_import_runs_request(request: httpx.Request) -> httpx.Response:
        daily_import_runs = storage["daily_import_runs"]
        if not isinstance(daily_import_runs, list):
            raise AssertionError("daily_import_runs storage must be a list")

        if request.method == "GET":
            import_date_filter = request.url.params.get("import_date")
            source_filter = request.url.params.get("source")
            status_filter = request.url.params.get("status")
            rows = daily_import_runs
            if import_date_filter and import_date_filter.startswith("eq."):
                import_date = import_date_filter.removeprefix("eq.")
                rows = [
                    run
                    for run in rows
                    if run["import_date"] == import_date
                ]
            if source_filter and source_filter.startswith("eq."):
                source = source_filter.removeprefix("eq.")
                rows = [
                    run
                    for run in rows
                    if run["source"] == source
                ]
            if status_filter and status_filter.startswith("eq."):
                status = status_filter.removeprefix("eq.")
                rows = [
                    run
                    for run in rows
                    if run["status"] == status
                ]
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            row = build_daily_import_run_row(read_json(request))
            daily_import_runs.append(row)
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_paper_ai_analyses_request(request: httpx.Request) -> httpx.Response:
        analyses = storage["paper_ai_analyses"]
        if not isinstance(analyses, list):
            raise AssertionError("paper_ai_analyses storage must be a list")

        if request.method == "GET":
            paper_id_filter = request.url.params.get("paper_id")
            provider_filter = request.url.params.get("provider")
            model_filter = request.url.params.get("model")
            rows = analyses
            if paper_id_filter and paper_id_filter.startswith("eq."):
                paper_id = paper_id_filter.removeprefix("eq.")
                rows = [
                    analysis
                    for analysis in rows
                    if analysis["paper_id"] == paper_id
                ]
            if provider_filter and provider_filter.startswith("eq."):
                provider = provider_filter.removeprefix("eq.")
                rows = [
                    analysis
                    for analysis in rows
                    if analysis["provider"] == provider
                ]
            if model_filter and model_filter.startswith("eq."):
                model = model_filter.removeprefix("eq.")
                rows = [
                    analysis
                    for analysis in rows
                    if analysis["model"] == model
                ]
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            payload = read_json(request)
            for index, analysis in enumerate(analyses):
                if (
                    analysis["paper_id"] == payload["paper_id"]
                    and analysis["provider"] == payload["provider"]
                    and analysis["model"] == payload["model"]
                ):
                    analyses[index] = {
                        **analysis,
                        **payload,
                        "id": analysis["id"],
                        "created_at": analysis["created_at"],
                        "updated_at": now_iso(),
                    }
                    return httpx.Response(201, json=[analyses[index]])

            row = build_paper_ai_analysis_row(payload)
            analyses.append(row)
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_request(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/papers":
            return handle_papers_request(request)
        if request.url.path == "/rest/v1/daily_import_runs":
            return handle_daily_import_runs_request(request)
        if request.url.path == "/rest/v1/daily_paper_items":
            return handle_daily_paper_items_request(request)
        if request.url.path == "/rest/v1/user_paper_actions":
            return handle_actions_request(request)
        if request.url.path == "/rest/v1/related_signals":
            return handle_related_signals_request(request)
        if request.url.path == "/rest/v1/paper_ai_analyses":
            return handle_paper_ai_analyses_request(request)
        return httpx.Response(404, json={"message": "not found"})

    def handle_auth_request(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/auth/v1/user":
            return httpx.Response(404, json={"message": "not found"})

        authorization = request.headers.get("Authorization")
        if authorization != "Bearer valid-access-token":
            return httpx.Response(401, json={"message": "invalid token"})

        return httpx.Response(
            200,
            json={
                "id": TEST_USER_ID,
                "email": "test@example.com",
            },
        )

    def handle_arxiv_request(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/api/query":
            return httpx.Response(404, text="not found")

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:arxiv="http://arxiv.org/schemas/atom">
          <entry>
            <id>https://arxiv.org/abs/2501.01234v1</id>
            <title> Retrieval-Augmented Backend APIs </title>
            <summary>
              This paper studies retrieval-augmented backend API design.
            </summary>
            <published>2025-01-02T00:00:00Z</published>
            <author><name>Alice Example</name></author>
            <author><name>Bob Example</name></author>
            <arxiv:doi>10.0000/example</arxiv:doi>
          </entry>
        </feed>
        """
        return httpx.Response(200, text=xml)

    def handle_github_request(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/search/repositories":
            return httpx.Response(404, json={"message": "not found"})

        query = request.url.params.get("q", "")
        if query != "2501.01234":
            return httpx.Response(
                200,
                json={"total_count": 0, "incomplete_results": False, "items": []},
            )

        return httpx.Response(
            200,
            json={
                "total_count": 1,
                "incomplete_results": False,
                "items": [
                    {
                        "full_name": "example/paper-implementation",
                        "html_url": "https://github.com/example/paper-implementation",
                        "description": "Implementation for the paper.",
                        "created_at": "2025-01-03T00:00:00Z",
                        "updated_at": "2025-01-04T00:00:00Z",
                        "stargazers_count": 42,
                        "forks_count": 3,
                        "language": "Python",
                    }
                ],
            },
        )

    def handle_qiita_request(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/api/v2/items":
            return httpx.Response(404, json={"message": "not found"})

        query = request.url.params.get("query", "")
        if query != "2501.01234":
            return httpx.Response(200, json=[])

        return httpx.Response(
            200,
            json=[
                {
                    "title": "Paper implementation note",
                    "url": "https://qiita.com/example/items/paper",
                    "created_at": "2025-01-05T00:00:00Z",
                    "likes_count": 5,
                    "stocks_count": 2,
                    "user": {"id": "example"},
                    "tags": [{"name": "AI"}],
                }
            ],
        )

    def handle_gemini_request(request: httpx.Request) -> httpx.Response:
        if request.url.path != "/v1beta/models/gemini-2.5-flash:generateContent":
            return httpx.Response(404, json={"message": "not found"})

        request_body = json.loads(request.content)
        system_text = request_body["systemInstruction"]["parts"][0]["text"]
        user_text = request_body["contents"][0]["parts"][0]["text"]
        assert "undergraduate computer science students" in system_text
        assert "情報系の大学生" in user_text
        assert "難しい専門用語" in user_text

        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {
                                            "summary_ja": "RAG API設計に関する論文です。",
                                            "implementation_difficulty": 3,
                                            "implementation_reason": (
                                                "検索基盤が必要ですが実装範囲は明確です。"
                                            ),
                                            "reading_difficulty": 2,
                                            "reading_reason": (
                                                "Abstractの主張が読み取りやすいためです。"
                                            ),
                                            "math_difficulty": 2,
                                            "math_reason": (
                                                "高度な数式より設計説明が中心のためです。"
                                            ),
                                        }
                                    )
                                }
                            ]
                        }
                    }
                ],
            },
        )

    mock_client = httpx.Client(
        base_url="https://example.supabase.co/rest/v1/",
        transport=httpx.MockTransport(handle_request),
    )
    mock_auth_client = httpx.Client(
        base_url="https://example.supabase.co/auth/v1/",
        transport=httpx.MockTransport(handle_auth_request),
    )
    mock_arxiv_client = httpx.Client(
        base_url="https://export.arxiv.org/api/",
        transport=httpx.MockTransport(handle_arxiv_request),
    )
    mock_github_client = httpx.Client(
        base_url="https://api.github.com/",
        transport=httpx.MockTransport(handle_github_request),
    )
    mock_qiita_client = httpx.Client(
        base_url="https://qiita.com/api/v2/",
        transport=httpx.MockTransport(handle_qiita_request),
    )
    mock_gemini_client = httpx.Client(
        base_url="https://generativelanguage.googleapis.com/v1beta/",
        transport=httpx.MockTransport(handle_gemini_request),
    )
    monkeypatch.setattr(
        paper_repository,
        "get_supabase_client",
        lambda: mock_client,
    )
    monkeypatch.setattr(
        auth_service,
        "get_supabase_auth_client",
        lambda: mock_auth_client,
    )
    monkeypatch.setattr(
        arxiv_client,
        "get_arxiv_client",
        lambda: mock_arxiv_client,
    )
    monkeypatch.setattr(
        github_client,
        "get_github_client",
        lambda: mock_github_client,
    )
    monkeypatch.setattr(
        qiita_client,
        "get_qiita_client",
        lambda: mock_qiita_client,
    )
    monkeypatch.setattr(
        gemini_client,
        "get_gemini_client",
        lambda: mock_gemini_client,
    )

    yield storage

    mock_client.close()
    mock_auth_client.close()
    mock_arxiv_client.close()
    mock_github_client.close()
    mock_qiita_client.close()
    mock_gemini_client.close()


def test_list_papers_returns_empty_list() -> None:
    response = client.get("/papers")

    assert response.status_code == 200
    assert response.json() == []


def test_create_paper() -> None:
    response = client.post(
        "/papers",
        json={
            "title": "Attention Is All You Need",
            "abstract": "Transformer architecture paper.",
            "source_url": "https://arxiv.org/abs/1706.03762",
            "arxiv_id": "1706.03762",
            "authors": ["Ashish Vaswani"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"]
    assert data["title"] == "Attention Is All You Need"
    assert data["abstract"] == "Transformer architecture paper."
    assert data["source_url"] == "https://arxiv.org/abs/1706.03762"
    assert data["arxiv_id"] == "1706.03762"
    assert data["doi"] is None
    assert data["authors"] == ["Ashish Vaswani"]
    assert data["published_at"] is None
    assert data["created_at"]
    assert data["updated_at"]


def test_get_paper() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for detail API"},
    )
    paper_id = create_response.json()["id"]

    response = client.get(f"/papers/{paper_id}")

    assert response.status_code == 200
    assert response.json()["id"] == paper_id
    assert response.json()["title"] == "A paper for detail API"


def test_get_paper_returns_404_when_not_found() -> None:
    response = client.get(f"/papers/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found"}


def test_create_paper_rejects_blank_title() -> None:
    response = client.post("/papers", json={"title": "   "})

    assert response.status_code == 422


def test_import_arxiv_papers() -> None:
    response = client.post(
        "/papers/import/arxiv",
        json={
            "search_query": "cat:cs.SE",
            "max_results": 1,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["imported_count"] == 1
    assert len(data["papers"]) == 1
    paper = data["papers"][0]
    assert paper["title"] == "Retrieval-Augmented Backend APIs"
    assert paper["abstract"] == (
        "This paper studies retrieval-augmented backend API design."
    )
    assert paper["source_url"] == "https://arxiv.org/abs/2501.01234v1"
    assert paper["arxiv_id"] == "2501.01234"
    assert paper["doi"] == "10.0000/example"
    assert paper["authors"] == ["Alice Example", "Bob Example"]
    assert paper["published_at"] == "2025-01-02T00:00:00Z"


def test_import_arxiv_papers_rejects_too_large_max_results() -> None:
    response = client.post(
        "/papers/import/arxiv",
        json={
            "search_query": "cat:cs.SE",
            "max_results": 51,
        },
    )

    assert response.status_code == 422


def test_import_daily_papers_runs_once_per_day() -> None:
    first_response = client.post(
        "/papers/import/daily",
        json={
            "search_query": "cat:cs.SE",
            "max_results": 1,
        },
    )
    second_response = client.post(
        "/papers/import/daily",
        json={
            "search_query": "cat:cs.SE",
            "max_results": 1,
        },
    )

    assert first_response.status_code == 201
    first_data = first_response.json()
    assert first_data["skipped"] is False
    assert first_data["imported_count"] == 1
    assert len(first_data["papers"]) == 1
    assert first_data["ai_analysis_generated_count"] == 1
    assert first_data["ai_analysis_failed_count"] == 0

    assert second_response.status_code == 201
    second_data = second_response.json()
    assert second_data["skipped"] is True
    assert second_data["imported_count"] == 0
    assert len(second_data["papers"]) == 1
    assert second_data["papers"][0]["arxiv_id"] == "2501.01234"
    assert second_data["ai_analysis_generated_count"] == 0
    assert second_data["ai_analysis_failed_count"] == 0


def test_import_daily_papers_includes_latest_and_signal_papers(
    monkeypatch: pytest.MonkeyPatch,
    supabase_mock,
) -> None:
    def fetch_papers_for_test(search_query: str, max_results: int) -> list[PaperCreate]:
        return [PaperCreate(title="Latest paper", arxiv_id="latest-paper")]

    monkeypatch.setattr(
        arxiv_client,
        "fetch_papers",
        fetch_papers_for_test,
    )

    def fetch_papers_by_ids_for_test(arxiv_ids: list[str]) -> list[PaperCreate]:
        assert arxiv_ids == ["2501.01234"]
        return [
            PaperCreate(
                title="Signal paper",
                arxiv_id="2501.01234",
                published_at=datetime.now(UTC) - timedelta(hours=1),
            )
        ]

    monkeypatch.setattr(
        arxiv_client,
        "fetch_papers_by_ids",
        fetch_papers_by_ids_for_test,
    )

    def search_recent_arxiv_articles_for_test(
        created_after,
        max_results: int,
    ) -> list[qiita_client.QiitaArxivArticle]:
        return [
            qiita_client.QiitaArxivArticle(
                arxiv_id="2501.01234",
                signal=RelatedSignalCreate(
                    source_type="qiita",
                    title="Signal paper article",
                    source_url="https://qiita.com/example/items/signal-paper",
                ),
            )
        ]

    monkeypatch.setattr(
        qiita_client,
        "search_recent_arxiv_articles",
        search_recent_arxiv_articles_for_test,
    )

    def discover_for_test(
        paper: PaperResponse,
        max_results_per_source: int = 3,
    ) -> RelatedSignalDiscoveryResponse:
        return RelatedSignalDiscoveryResponse(
            discovered_count=0,
            signals=[],
            source_errors=[],
        )

    monkeypatch.setattr(
        daily_feed_service.signal_discovery_service,
        "discover_and_save_related_signals",
        discover_for_test,
    )

    response = client.post(
        "/papers/import/daily",
        json={
            "search_query": "cat:cs.SE",
            "max_results": 1,
            "signal_categories": ["cs.SE"],
            "signal_max_results_per_category": 1,
            "signal_max_papers": 1,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["imported_count"] == 2
    assert data["ai_analysis_generated_count"] == 2
    assert data["ai_analysis_failed_count"] == 0
    assert [paper["arxiv_id"] for paper in data["papers"]] == [
        "latest-paper",
        "2501.01234",
    ]
    daily_items = supabase_mock["daily_paper_items"]
    assert daily_items[0]["selection_reason"] == (
        daily_feed_service.LATEST_SELECTION_REASON
    )
    assert daily_items[1]["selection_reason"] == (
        daily_feed_service.EXTERNAL_SIGNAL_SELECTION_REASON
    )


def test_list_today_papers() -> None:
    import_response = client.post(
        "/papers/import/daily",
        json={
            "search_query": "cat:cs.SE",
            "max_results": 1,
        },
    )

    response = client.get("/papers/today")

    assert import_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["arxiv_id"] == "2501.01234"


def test_upsert_and_get_paper_ai_analysis_repository() -> None:
    create_response = client.post(
        "/papers",
        json={
            "title": "A paper for AI analysis repository",
            "abstract": "This paper studies backend API analysis.",
        },
    )
    paper_id = UUID(create_response.json()["id"])

    analysis = paper_repository.upsert_paper_ai_analysis(
        PaperAIAnalysisCreate(
            paper_id=paper_id,
            provider="gemini",
            model="gemini-2.5-flash",
            summary_ja="Backend API分析に関する論文です。",
            implementation_difficulty=3,
            implementation_reason="APIとDBの実装が必要なためです。",
            reading_difficulty=2,
            reading_reason="Abstractの構成が明確なためです。",
            math_difficulty=1,
            math_reason="数式より設計説明が中心のためです。",
            raw_response={"id": "resp_test"},
        )
    )

    fetched_analysis = paper_repository.get_paper_ai_analysis(
        paper_id,
        "gemini",
        "gemini-2.5-flash",
    )

    assert analysis.paper_id == paper_id
    assert fetched_analysis is not None
    assert fetched_analysis.id == analysis.id
    assert fetched_analysis.summary_ja == "Backend API分析に関する論文です。"


def test_generate_paper_ai_analysis() -> None:
    create_response = client.post(
        "/papers",
        json={
            "title": "Retrieval-Augmented Backend APIs",
            "abstract": "This paper studies retrieval-augmented backend API design.",
            "arxiv_id": "2501.01234",
        },
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/analysis/generate",
        json={"provider": "gemini", "model": "gemini-2.5-flash"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["paper_id"] == paper_id
    assert data["provider"] == "gemini"
    assert data["model"] == "gemini-2.5-flash"
    assert data["summary_ja"] == "RAG API設計に関する論文です。"
    assert data["implementation_difficulty"] == 3


def test_get_paper_ai_analysis() -> None:
    create_response = client.post(
        "/papers",
        json={
            "title": "A paper for AI analysis API",
            "abstract": "This paper studies AI-generated paper analysis.",
        },
    )
    paper_id = create_response.json()["id"]

    generate_response = client.post(
        f"/papers/{paper_id}/analysis/generate",
        json={"provider": "gemini", "model": "gemini-2.5-flash"},
    )
    response = client.get(f"/papers/{paper_id}/analysis")

    assert generate_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == paper_id
    assert data["summary_ja"] == "RAG API設計に関する論文です。"


def test_get_paper_ai_analysis_returns_404_when_not_found() -> None:
    response = client.get(f"/papers/{uuid4()}/analysis")

    assert response.status_code == 404
    assert response.json() == {"detail": "Paper AI analysis not found"}


def test_generate_paper_ai_analysis_returns_404_when_paper_not_found() -> None:
    response = client.post(
        f"/papers/{uuid4()}/analysis/generate",
        json={"provider": "gemini", "model": "gemini-2.5-flash"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found"}


def test_import_rising_papers() -> None:
    response = client.post(
        "/papers/import/rising",
        json={
            "categories": ["cs.SE"],
            "max_results_per_category": 1,
            "max_papers": 10,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["imported_count"] == 1
    assert len(data["papers"]) == 1
    assert data["papers"][0]["arxiv_id"] == "2501.01234"
    assert data["signal_counts"][data["papers"][0]["id"]] == 2
    assert data["source_errors"] == []


def test_build_rising_search_query_uses_14_to_60_day_range() -> None:
    query = rising_service.build_rising_search_query(
        category="cs.AI",
        min_days_old=14,
        max_days_old=60,
        now=datetime(2026, 5, 22, tzinfo=UTC),
    )

    assert query == (
        "cat:cs.AI "
        "AND submittedDate:[202603230000 TO 202605082359]"
    )


def test_import_rising_papers_requires_github_and_article(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arxiv_queries: list[str] = []

    def fetch_papers_for_test(search_query: str, max_results: int) -> list[PaperCreate]:
        arxiv_queries.append(search_query)
        return [
            PaperCreate(title="GitHub only", arxiv_id="github-only"),
            PaperCreate(title="Article only", arxiv_id="article-only"),
            PaperCreate(title="Both sources", arxiv_id="both-sources"),
        ]

    monkeypatch.setattr(
        arxiv_client,
        "fetch_papers",
        fetch_papers_for_test,
    )

    def discover_for_test(
        paper: PaperResponse,
        max_results_per_source: int = 3,
    ) -> RelatedSignalDiscoveryResponse:
        now = datetime.now(UTC)
        source_types_by_arxiv_id: dict[str, list[RelatedSignalSourceType]] = {
            "github-only": ["github"],
            "article-only": ["qiita"],
            "both-sources": ["github", "qiita"],
        }
        signals = [
            RelatedSignalResponse(
                id=uuid4(),
                paper_id=paper.id,
                source_type=source_type,
                title=f"{paper.title} {source_type}",
                source_url=f"https://example.com/{paper.arxiv_id}/{source_type}",
                created_at=now,
                updated_at=now,
            )
            for source_type in source_types_by_arxiv_id.get(paper.arxiv_id, [])
        ]
        return RelatedSignalDiscoveryResponse(
            discovered_count=len(signals),
            signals=signals,
            source_errors=[],
        )

    monkeypatch.setattr(
        rising_service.signal_discovery_service,
        "discover_and_save_related_signals",
        discover_for_test,
    )

    response = client.post(
        "/papers/import/rising",
        json={
            "categories": ["cs.SE"],
            "max_results_per_category": 3,
            "max_papers": 10,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert len(arxiv_queries) == 1
    assert arxiv_queries[0].startswith("cat:cs.SE AND submittedDate:[")
    assert data["imported_count"] == 1
    assert [paper["arxiv_id"] for paper in data["papers"]] == ["both-sources"]


def test_import_rising_papers_rejects_invalid_day_range() -> None:
    response = client.post(
        "/papers/import/rising",
        json={
            "categories": ["cs.SE"],
            "max_results_per_category": 5,
            "max_papers": 10,
            "min_days_old": 60,
            "max_days_old": 14,
        },
    )

    assert response.status_code == 422


def test_import_rising_papers_rejects_too_many_categories_results() -> None:
    response = client.post(
        "/papers/import/rising",
        json={
            "categories": ["cs.SE"],
            "max_results_per_category": 21,
            "max_papers": 10,
        },
    )

    assert response.status_code == 422


def test_create_paper_action() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for action API"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/actions",
        headers=AUTH_HEADERS,
        json={
            "action": "pickup",
            "reason": "Looks relevant to backend API design.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"]
    assert data["paper_id"] == paper_id
    assert data["user_id"] == TEST_USER_ID
    assert data["action"] == "pickup"
    assert data["reason"] == "Looks relevant to backend API design."
    assert data["created_at"]


def test_list_picked_papers_returns_latest_pickup_only() -> None:
    first_create_response = client.post(
        "/papers",
        json={"title": "Picked paper"},
    )
    second_create_response = client.post(
        "/papers",
        json={"title": "Skipped after pickup paper"},
    )
    first_paper_id = first_create_response.json()["id"]
    second_paper_id = second_create_response.json()["id"]

    first_action_response = client.post(
        f"/papers/{first_paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "pickup"},
    )
    second_pickup_response = client.post(
        f"/papers/{second_paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "pickup"},
    )
    second_skip_response = client.post(
        f"/papers/{second_paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "skip"},
    )

    response = client.get("/papers/picked", headers=AUTH_HEADERS)

    assert first_action_response.status_code == 201
    assert second_pickup_response.status_code == 201
    assert second_skip_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == first_paper_id
    assert data[0]["title"] == "Picked paper"


def test_export_picked_papers_for_notebooklm() -> None:
    create_response = client.post(
        "/papers",
        json={
            "title": "Picked arXiv paper",
            "abstract": "This paper studies agent memory.",
            "arxiv_id": "2605.12345",
            "source_url": "https://arxiv.org/abs/2605.12345",
        },
    )
    paper_id = create_response.json()["id"]
    action_response = client.post(
        f"/papers/{paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "pickup"},
    )

    response = client.get("/papers/picked/export", headers=AUTH_HEADERS)

    assert action_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert data["pdf_urls"] == ["https://arxiv.org/pdf/2605.12345"]
    assert "Picked arXiv paper" in data["markdown_note"]
    assert "This paper studies agent memory." in data["markdown_note"]
    assert "共通テーマ" in data["notebooklm_prompt"]


def test_export_picked_papers_pdf_zip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_response = client.post(
        "/papers",
        json={
            "title": "Picked PDF paper",
            "arxiv_id": "2605.54321",
            "source_url": "https://arxiv.org/abs/2605.54321",
        },
    )
    paper_id = create_response.json()["id"]
    client.post(
        f"/papers/{paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "pickup"},
    )

    monkeypatch.setattr(
        paper_export_service,
        "_download_pdf",
        lambda pdf_url: b"%PDF-1.4 test",
    )

    response = client.get("/papers/picked/export/pdf-zip", headers=AUTH_HEADERS)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(response.content)) as zip_file:
        names = zip_file.namelist()
        assert "picked-papers-note.md" in names
        assert "notebooklm-prompt.txt" in names
        assert any(name.endswith(".pdf") for name in names)


def test_create_paper_action_requires_authorization_header() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for auth required API"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/actions",
        json={"action": "pickup"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authorization header is required"}


def test_create_paper_action_rejects_invalid_token() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for invalid token API"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/actions",
        headers={"Authorization": "Bearer invalid-access-token"},
        json={"action": "pickup"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing access token"}


def test_create_paper_action_rejects_invalid_action() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for invalid action API"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "read_later"},
    )

    assert response.status_code == 422


def test_create_related_signal() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for related signal API"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/related-signals",
        json={
            "source_type": "github",
            "title": "Example implementation",
            "source_url": "https://github.com/example/paper-implementation",
            "summary": "Unofficial implementation repository.",
            "raw_metadata": {"stars": 42},
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"]
    assert data["paper_id"] == paper_id
    assert data["source_type"] == "github"
    assert data["title"] == "Example implementation"
    assert data["source_url"] == "https://github.com/example/paper-implementation"
    assert data["summary"] == "Unofficial implementation repository."
    assert data["raw_metadata"] == {"stars": 42}
    assert data["created_at"]
    assert data["updated_at"]


def test_list_related_signals() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper with related signals"},
    )
    paper_id = create_response.json()["id"]

    first_response = client.post(
        f"/papers/{paper_id}/related-signals",
        json={
            "source_type": "github",
            "title": "Implementation repository",
            "source_url": "https://github.com/example/paper",
        },
    )
    second_response = client.post(
        f"/papers/{paper_id}/related-signals",
        json={
            "source_type": "qiita",
            "title": "Implementation note",
            "source_url": "https://qiita.com/example/items/paper",
        },
    )

    response = client.get(f"/papers/{paper_id}/related-signals")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["source_type"] == "github"
    assert data[1]["source_type"] == "qiita"


def test_create_related_signal_returns_404_when_paper_not_found() -> None:
    response = client.post(
        f"/papers/{uuid4()}/related-signals",
        json={
            "source_type": "github",
            "title": "Missing paper implementation",
            "source_url": "https://github.com/example/missing-paper",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found"}


def test_create_related_signal_rejects_invalid_source_type() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for invalid related signal"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/related-signals",
        json={
            "source_type": "mastodon",
            "title": "Invalid source type",
            "source_url": "https://example.com/invalid",
        },
    )

    assert response.status_code == 422


def test_discover_related_signals() -> None:
    create_response = client.post(
        "/papers",
        json={
            "title": "Retrieval-Augmented Backend APIs",
            "arxiv_id": "2501.01234",
        },
    )
    paper_id = create_response.json()["id"]

    response = client.post(f"/papers/{paper_id}/related-signals/discover")

    assert response.status_code == 201
    data = response.json()
    assert data["discovered_count"] == 2
    assert data["source_errors"] == []
    source_types = [
        signal["source_type"]
        for signal in data["signals"]
    ]
    assert source_types == ["github", "qiita"]

    list_response = client.get(f"/papers/{paper_id}/related-signals")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2


def test_discover_related_signals_reports_source_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_github_error(query: str, max_results: int):
        raise github_client.GitHubClientError("GitHub search request failed")

    monkeypatch.setattr(
        github_client,
        "search_repositories",
        raise_github_error,
    )

    create_response = client.post(
        "/papers",
        json={
            "title": "Retrieval-Augmented Backend APIs",
            "arxiv_id": "2501.01234",
        },
    )
    paper_id = create_response.json()["id"]

    response = client.post(f"/papers/{paper_id}/related-signals/discover")

    assert response.status_code == 201
    data = response.json()
    assert data["source_errors"] == ["github"]
    assert data["discovered_count"] == 1
    source_types = [
        signal["source_type"]
        for signal in data["signals"]
    ]
    assert source_types == ["qiita"]


def test_discover_related_signals_returns_404_when_paper_not_found() -> None:
    response = client.post(f"/papers/{uuid4()}/related-signals/discover")

    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found"}


def test_create_paper_action_returns_404_when_paper_not_found() -> None:
    response = client.post(
        f"/papers/{uuid4()}/actions",
        headers=AUTH_HEADERS,
        json={"action": "skip"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found"}


def test_create_paper_action_keeps_history_for_same_paper() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper with action history"},
    )
    paper_id = create_response.json()["id"]

    first_response = client.post(
        f"/papers/{paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "save"},
    )
    second_response = client.post(
        f"/papers/{paper_id}/actions",
        headers=AUTH_HEADERS,
        json={"action": "skip", "reason": "Read later is enough for now."},
    )

    actions = list_paper_actions(UUID(paper_id))
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert len(actions) == 2
    assert actions[0].action == "save"
    assert actions[1].action == "skip"
    assert str(actions[0].user_id) == TEST_USER_ID
    assert str(actions[1].user_id) == TEST_USER_ID
