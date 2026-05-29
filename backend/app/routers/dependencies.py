"""router間で共有する認証・エラー変換処理です。"""

from typing import NoReturn
from uuid import UUID

from fastapi import Header, HTTPException, status

from app.clients.supabase import SupabaseConfigError
from app.services import auth_service, paper_analysis_service, paper_service


def raise_storage_http_error(error: Exception) -> NoReturn:
    if isinstance(error, SupabaseConfigError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paper storage is not configured",
        ) from error

    if isinstance(error, paper_service.PaperStorageError):
        if error.supabase_code in {"PGRST205", "42P01", "42703"}:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supabase schema is not applied",
            ) from error

        if error.supabase_code == "42501" or error.status_code in {401, 403}:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supabase RLS blocked request",
            ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Paper storage request failed",
    ) from error


def raise_import_http_error(error: Exception) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="arXiv import request failed",
    ) from error


def raise_analysis_http_error(error: Exception) -> NoReturn:
    if isinstance(error, paper_analysis_service.PaperAnalysisConfigError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis is not configured",
        ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="AI analysis request failed",
    ) from error


def raise_auth_http_error(error: Exception) -> NoReturn:
    if isinstance(error, auth_service.InvalidAuthTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
        ) from error

    if isinstance(error, SupabaseConfigError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth storage is not configured",
        ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Auth request failed",
    ) from error


def require_current_user_id(
    authorization: str | None = Header(default=None),
) -> UUID:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token is required",
        )

    try:
        return auth_service.verify_access_token(token)
    except (
        SupabaseConfigError,
        auth_service.AuthServiceError,
    ) as error:
        raise_auth_http_error(error)
