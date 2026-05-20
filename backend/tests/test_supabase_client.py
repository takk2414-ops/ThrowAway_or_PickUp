"""Supabase client作成処理のテストです。"""

import pytest

from app.clients.supabase import (
    SupabaseConfigError,
    create_supabase_auth_client,
    create_supabase_client,
)
from app.config import Settings


def test_create_supabase_client_uses_settings() -> None:
    settings = Settings(
        supabase_url="https://example.supabase.co/",
        supabase_anon_key="example-anon-key",
    )

    client = create_supabase_client(settings)

    assert str(client.base_url) == "https://example.supabase.co/rest/v1/"
    assert client.headers["apikey"] == "example-anon-key"
    assert client.headers["Authorization"] == "Bearer example-anon-key"
    assert client.headers["Content-Type"] == "application/json"
    client.close()


def test_create_supabase_client_requires_url() -> None:
    settings = Settings(
        supabase_url="",
        supabase_anon_key="example-anon-key",
    )

    with pytest.raises(SupabaseConfigError, match="SUPABASE_URL is required"):
        create_supabase_client(settings)


def test_create_supabase_client_requires_anon_key() -> None:
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_anon_key="",
    )

    with pytest.raises(SupabaseConfigError, match="SUPABASE_ANON_KEY is required"):
        create_supabase_client(settings)


def test_create_supabase_auth_client_uses_settings() -> None:
    settings = Settings(
        supabase_url="https://example.supabase.co/",
        supabase_anon_key="example-anon-key",
    )

    client = create_supabase_auth_client(settings)

    assert str(client.base_url) == "https://example.supabase.co/auth/v1/"
    assert client.headers["apikey"] == "example-anon-key"
    assert client.headers["Content-Type"] == "application/json"
    client.close()
