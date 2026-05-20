"""papers APIのテストです。

GET /papers、GET /papers/{paper_id}、POST /papers、
POST /papers/{paper_id}/actions の最小動作を確認します。
"""

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import auth_service, paper_service
from app.services.paper_service import list_paper_actions


client = TestClient(app)
TEST_USER_ID = "9ce94211-1471-413f-9699-990da998064e"
AUTH_HEADERS = {"Authorization": "Bearer valid-access-token"}


@pytest.fixture(autouse=True)
def supabase_mock(monkeypatch: pytest.MonkeyPatch):
    storage: dict[str, dict | list] = {
        "papers": {},
        "actions": [],
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

    def build_action_row(payload: dict) -> dict:
        return {
            "id": str(uuid4()),
            "paper_id": payload["paper_id"],
            "user_id": payload["user_id"],
            "action": payload["action"],
            "reason": payload.get("reason"),
            "created_at": now_iso(),
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
            row = build_paper_row(read_json(request))
            papers[row["id"]] = row
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_actions_request(request: httpx.Request) -> httpx.Response:
        actions = storage["actions"]
        if not isinstance(actions, list):
            raise AssertionError("actions storage must be a list")

        if request.method == "GET":
            paper_id_filter = request.url.params.get("paper_id")
            rows = actions
            if paper_id_filter and paper_id_filter.startswith("eq."):
                paper_id = paper_id_filter.removeprefix("eq.")
                rows = [
                    action
                    for action in rows
                    if action["paper_id"] == paper_id
                ]
            return httpx.Response(200, json=rows)

        if request.method == "POST":
            row = build_action_row(read_json(request))
            actions.append(row)
            return httpx.Response(201, json=[row])

        return httpx.Response(405, json={"message": "method not allowed"})

    def handle_request(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/papers":
            return handle_papers_request(request)
        if request.url.path == "/rest/v1/user_paper_actions":
            return handle_actions_request(request)
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

    mock_client = httpx.Client(
        base_url="https://example.supabase.co/rest/v1/",
        transport=httpx.MockTransport(handle_request),
    )
    mock_auth_client = httpx.Client(
        base_url="https://example.supabase.co/auth/v1/",
        transport=httpx.MockTransport(handle_auth_request),
    )
    monkeypatch.setattr(
        paper_service,
        "get_supabase_client",
        lambda: mock_client,
    )
    monkeypatch.setattr(
        auth_service,
        "get_supabase_auth_client",
        lambda: mock_auth_client,
    )

    yield storage

    mock_client.close()
    mock_auth_client.close()


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
