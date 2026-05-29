from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    health,
    paper_actions,
    paper_analyses,
    paper_exports,
    paper_imports,
    paper_signals,
    papers,
)


def create_app() -> FastAPI:
    # FastAPIアプリ本体を作成する関数です。
    # router登録など、アプリ起動時に必要な設定をここにまとめます。
    app = FastAPI(
        title="ThrowAway_or_PickUp API",
        description="Paper screening API for ThrowAway_or_PickUp",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /health や /papers のようなAPIルートをアプリに登録します。
    app.include_router(health.router)
    app.include_router(paper_imports.router)
    app.include_router(paper_exports.router)
    app.include_router(paper_actions.router)
    app.include_router(paper_signals.router)
    app.include_router(paper_analyses.router)
    # /papers/{paper_id} を含むため、固定パス系routerより後に登録します。
    app.include_router(papers.router)
    return app


# uvicorn app.main:app で読み込まれるFastAPIアプリです。
app = create_app()


@app.get("/")
def read_root() -> dict[str, str]:
    # APIの入口として、よく使う確認先を返します。
    return {
        "message": "ThrowAway_or_PickUp API",
        "docs": "/docs",
        "health": "/health",
        "papers": "/papers",
    }
