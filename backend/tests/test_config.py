"""設定読み込みのテストです。

実際の .env ファイルは使わず、テスト中だけ環境変数を差し替えます。
"""

from app.config import Settings


def test_settings_reads_environment_variables(monkeypatch) -> None:
    # テスト中だけ環境変数を設定します。実際の .env は変更しません。
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "example-anon-key")
    monkeypatch.setenv("DAILY_PAPER_LIMIT", "30")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.supabase_url == "https://example.supabase.co"
    assert settings.supabase_anon_key == "example-anon-key"
    assert settings.daily_paper_limit == 30


def test_settings_uses_default_values(monkeypatch) -> None:
    # 環境変数がない場合に、デフォルト値が使われることを確認します。
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("DAILY_PAPER_LIMIT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "local"
    assert settings.supabase_url == ""
    assert settings.supabase_anon_key == ""
    assert settings.daily_paper_limit == 20
