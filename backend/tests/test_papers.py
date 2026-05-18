"""papers APIのテストです。

GET /papers、GET /papers/{paper_id}、POST /papers、
POST /papers/{paper_id}/actions の最小動作を確認します。
"""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.paper_service import clear_papers, list_paper_actions


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_papers() -> None:
    clear_papers()


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
        json={
            "action": "pickup",
            "reason": "Looks relevant to backend API design.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"]
    assert data["paper_id"] == paper_id
    assert data["user_id"] is None
    assert data["action"] == "pickup"
    assert data["reason"] == "Looks relevant to backend API design."
    assert data["created_at"]


def test_create_paper_action_rejects_invalid_action() -> None:
    create_response = client.post(
        "/papers",
        json={"title": "A paper for invalid action API"},
    )
    paper_id = create_response.json()["id"]

    response = client.post(
        f"/papers/{paper_id}/actions",
        json={"action": "read_later"},
    )

    assert response.status_code == 422


def test_create_paper_action_returns_404_when_paper_not_found() -> None:
    response = client.post(
        f"/papers/{uuid4()}/actions",
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
        json={"action": "save"},
    )
    second_response = client.post(
        f"/papers/{paper_id}/actions",
        json={"action": "skip", "reason": "Read later is enough for now."},
    )

    actions = list_paper_actions(UUID(paper_id))
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert len(actions) == 2
    assert actions[0].action == "save"
    assert actions[1].action == "skip"
