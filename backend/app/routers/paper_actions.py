"""論文へのユーザーaction API routerです。"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.clients.supabase import SupabaseConfigError
from app.routers.dependencies import require_current_user_id, raise_storage_http_error
from app.schemas.actions import PaperActionCreate, PaperActionResponse
from app.schemas.papers import PaperResponse
from app.services import paper_service


router = APIRouter(prefix="/papers", tags=["paper-actions"])


@router.get("/picked", response_model=list[PaperResponse])
def list_picked_papers(
    user_id: UUID = Depends(require_current_user_id),
) -> list[PaperResponse]:
    try:
        return paper_service.list_picked_papers(user_id)
    except (SupabaseConfigError, paper_service.PaperStorageError) as error:
        raise_storage_http_error(error)


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
        raise_storage_http_error(error)

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return action
