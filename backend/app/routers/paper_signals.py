"""論文の関連シグナルAPI routerです。"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.clients.supabase import SupabaseConfigError
from app.routers.dependencies import raise_storage_http_error
from app.schemas.signals import (
    RelatedSignalCreate,
    RelatedSignalDiscoveryResponse,
    RelatedSignalResponse,
)
from app.services import paper_service


router = APIRouter(prefix="/papers", tags=["paper-signals"])


@router.get(
    "/{paper_id}/related-signals",
    response_model=list[RelatedSignalResponse],
)
def list_related_signals(paper_id: UUID) -> list[RelatedSignalResponse]:
    try:
        signals = paper_service.list_related_signals(paper_id)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)

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
        raise_storage_http_error(error)

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
        raise_storage_http_error(error)

    if discovery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return discovery
