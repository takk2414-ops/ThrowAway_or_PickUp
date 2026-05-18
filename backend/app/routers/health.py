from fastapi import APIRouter

# /health から始まるAPIをまとめるrouterです。
router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    # サーバーが正常に動いているか確認するための最小APIです。
    return {"status": "ok"}
