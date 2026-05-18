"""health APIのテストを書く場所です。

GET / と GET /health が期待どおり動くか確認します。
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_read_root() -> None:
    # APIの入口が、よく使うURL情報を返すことを確認します。
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "ThrowAway_or_PickUp API",
        "docs": "/docs",
        "health": "/health",
        "papers": "/papers",
    }


def test_health_check() -> None:
    # サーバーの生存確認APIが正常応答することを確認します。
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
