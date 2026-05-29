"""Supabase接続を担当する場所です。

今後、DBへアクセスするときは router から直接 Supabase を呼ばず、
service 層を経由して、この client を使う形にします。
"""

from functools import lru_cache

import httpx

from app.config import Settings, get_settings


class SupabaseConfigError(RuntimeError):
    """Supabase接続に必要な設定が不足している場合のエラーです。"""


def _build_rest_api_url(supabase_url: str) -> str:
    base_url = supabase_url.strip().rstrip("/")
    if not base_url:
        raise SupabaseConfigError("SUPABASE_URL is required")
    return f"{base_url}/rest/v1"


def _build_auth_api_url(supabase_url: str) -> str:
    base_url = supabase_url.strip().rstrip("/")
    if not base_url:
        raise SupabaseConfigError("SUPABASE_URL is required")
    return f"{base_url}/auth/v1"


def create_supabase_client(settings: Settings) -> httpx.Client:
    """Supabase REST APIへ接続するためのHTTP clientを作ります。"""

    supabase_api_key = (
        settings.supabase_service_role_key
        or settings.supabase_anon_key
    )
    if not supabase_api_key:
        raise SupabaseConfigError(
            "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY is required"
        )

    return httpx.Client(
        base_url=_build_rest_api_url(settings.supabase_url),
        headers={
            "apikey": supabase_api_key,
            "Authorization": f"Bearer {supabase_api_key}",
            "Content-Type": "application/json",
        },
        timeout=10.0,
    )


def create_supabase_auth_client(settings: Settings) -> httpx.Client:
    """Supabase Auth APIへ接続するためのHTTP clientを作ります。"""

    if not settings.supabase_anon_key:
        raise SupabaseConfigError("SUPABASE_ANON_KEY is required")

    return httpx.Client(
        base_url=_build_auth_api_url(settings.supabase_url),
        headers={
            "apikey": settings.supabase_anon_key,
            "Content-Type": "application/json",
        },
        timeout=10.0,
    )


@lru_cache
def get_supabase_client() -> httpx.Client:
    """アプリ全体で再利用するSupabase clientを返します。"""

    return create_supabase_client(get_settings())


@lru_cache
def get_supabase_auth_client() -> httpx.Client:
    """アプリ全体で再利用するSupabase Auth clientを返します。"""

    return create_supabase_auth_client(get_settings())
