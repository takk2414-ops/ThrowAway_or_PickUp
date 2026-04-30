from fastapi import FastAPI

from app.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="ThrowAway_or_PickUp API",
        description="Paper screening API for ThrowAway_or_PickUp",
        version="0.1.0",
    )

    app.include_router(health.router)
    return app


app = create_app()


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "ThrowAway_or_PickUp API",
        "docs": "/docs",
        "health": "/health",
    }
