from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # アプリの実行環境です。local / staging / production などを想定します。
    app_env: str = "local"

    # Supabase接続に使うURLです。実際の値は .env に書きます。
    supabase_url: str = ""

    # Supabaseの公開用キーです。秘密情報をコードに直接書かないため、.env から読みます。
    supabase_anon_key: str = ""

    # backend専用のSupabase service role keyです。RLSを通してサーバー側でDB保存します。
    supabase_service_role_key: str = ""

    # 1日に表示する論文数の初期値です。DBでは固定せず、アプリ側の設定として扱います。
    daily_paper_limit: int = 20

    # Qiita APIの認証トークンです。未設定でも動きますが、レート制限や403を避けるには設定します。
    qiita_access_token: str = ""

    # OpenAI APIで論文分析を生成するための設定です。
    openai_api_key: str = ""
    openai_analysis_model: str = "gpt-4.1-mini"

    # Gemini APIで論文分析を生成するための設定です。
    gemini_api_key: str = ""
    gemini_analysis_model: str = "gemini-2.5-flash"

    # .env ファイルから環境変数を読み込む設定です。
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    # 設定値は毎回作り直さず、初回だけ読み込んで再利用します。
    return Settings()
