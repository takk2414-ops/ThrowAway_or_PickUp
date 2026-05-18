from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.paper import (
    PaperActionCreate,
    PaperActionResponse,
    PaperCreate,
    PaperResponse,
)
from app.services import paper_service

# 論文に関するAPIをまとめるrouterです。
router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[PaperResponse])
def list_papers() -> list[PaperResponse]:
    return paper_service.list_papers()


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: UUID) -> PaperResponse:
    paper = paper_service.get_paper(paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return paper


@router.post("", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
def create_paper(paper_create: PaperCreate) -> PaperResponse:
    return paper_service.create_paper(paper_create)


@router.post(
    "/{paper_id}/actions",
    response_model=PaperActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper_action(
    paper_id: UUID,
    paper_action_create: PaperActionCreate,
) -> PaperActionResponse:
    action = paper_service.create_paper_action(paper_id, paper_action_create)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )
    return action
