from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.clients.supabase import SupabaseConfigError
from app.schemas.paper import (
    ArxivImportRequest,
    ArxivImportResponse,
    PaperActionCreate,
    PaperActionResponse,
    PaperCreate,
    PaperResponse,
    RelatedSignalCreate,
    RelatedSignalDiscoveryResponse,
    RelatedSignalResponse,
    RisingImportRequest,
    RisingImportResponse,
)
from app.services import auth_service, paper_service, rising_service

# 論文に関するAPIをまとめるrouterです。
router = APIRouter(prefix="/papers", tags=["papers"])


def _raise_storage_http_error(error: Exception) -> NoReturn:
    if isinstance(error, SupabaseConfigError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paper storage is not configured",
        ) from error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Paper storage request failed",
    ) from error


def _raise_import_http_error(error: Exception) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="arXiv import request failed",
    ) from error


def _raise_auth_http_error(error: Exception) -> NoReturn:
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
        _raise_auth_http_error(error)


@router.get("", response_model=list[PaperResponse])
def list_papers() -> list[PaperResponse]:
    try:
        return paper_service.list_papers()
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: UUID) -> PaperResponse:
    try:
        paper = paper_service.get_paper(paper_id)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return paper


@router.post("", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
def create_paper(paper_create: PaperCreate) -> PaperResponse:
    try:
        return paper_service.create_paper(paper_create)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)


@router.post(
    "/import/arxiv",
    response_model=ArxivImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_arxiv_papers(
    import_request: ArxivImportRequest,
) -> ArxivImportResponse:
    try:
        return paper_service.import_arxiv_papers(import_request)
    except paper_service.PaperImportError as error:
        _raise_import_http_error(error)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)


@router.post(
    "/import/rising",
    response_model=RisingImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_rising_papers(
    import_request: RisingImportRequest,
) -> RisingImportResponse:
    try:
        return rising_service.import_rising_papers(import_request)
    except rising_service.RisingImportError as error:
        _raise_import_http_error(error)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)


@router.post(
    "/{paper_id}/actions",
    response_model=PaperActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper_action(
    paper_id: UUID,
    paper_action_create: PaperActionCreate,
    user_id: UUID = Depends(require_current_user_id),
) -> PaperActionResponse:
    try:
        action = paper_service.create_paper_action(
            paper_id,
            paper_action_create,
            user_id,
        )
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return action


@router.get(
    "/{paper_id}/related-signals",
    response_model=list[RelatedSignalResponse],
)
def list_related_signals(paper_id: UUID) -> list[RelatedSignalResponse]:
    try:
        signals = paper_service.list_related_signals(paper_id)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)

    if signals is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return signals


@router.post(
    "/{paper_id}/related-signals",
    response_model=RelatedSignalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_related_signal(
    paper_id: UUID,
    related_signal_create: RelatedSignalCreate,
) -> RelatedSignalResponse:
    try:
        signal = paper_service.create_related_signal(
            paper_id,
            related_signal_create,
        )
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)

    if signal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return signal


@router.post(
    "/{paper_id}/related-signals/discover",
    response_model=RelatedSignalDiscoveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def discover_related_signals(
    paper_id: UUID,
) -> RelatedSignalDiscoveryResponse:
    try:
        discovery = paper_service.discover_related_signals(paper_id)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        _raise_storage_http_error(error)

    if discovery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return discovery
