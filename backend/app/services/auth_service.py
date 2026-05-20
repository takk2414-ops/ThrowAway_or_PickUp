"""Supabase Auth のユーザー検証を担当する service です。"""

from uuid import UUID

import httpx

from app.clients.supabase import SupabaseConfigError, get_supabase_auth_client


class AuthServiceError(RuntimeError):
    """Supabase Auth への問い合わせに失敗した場合のエラーです。"""


class InvalidAuthTokenError(AuthServiceError):
    """Authorization token が無効な場合のエラーです。"""


def verify_access_token(access_token: str) -> UUID:
    """Supabase Auth に問い合わせて access token の user_id を返します。"""

    token = access_token.strip()
    if not token:
        raise InvalidAuthTokenError("Access token is required")

    try:
        response = get_supabase_auth_client().get(
            "user",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code in (401, 403):
            raise InvalidAuthTokenError("Access token is invalid")
        response.raise_for_status()
    except InvalidAuthTokenError:
        raise
    except SupabaseConfigError:
        raise
    except httpx.HTTPError as error:
        raise AuthServiceError("Supabase Auth request failed") from error

    try:
        data = response.json()
    except ValueError as error:
        raise AuthServiceError("Supabase Auth returned invalid JSON") from error

    if not isinstance(data, dict) or "id" not in data:
        raise AuthServiceError("Supabase Auth returned unexpected JSON shape")

    try:
        return UUID(str(data["id"]))
    except ValueError as error:
        raise AuthServiceError("Supabase Auth returned invalid user id") from error
