"""PickUp済み論文の外部ツール連携export API routerです。"""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.clients.supabase import SupabaseConfigError
from app.routers.dependencies import require_current_user_id, raise_storage_http_error
from app.schemas.exports import PickedPaperExportResponse
from app.services import paper_export_service


router = APIRouter(prefix="/papers/picked/export", tags=["paper-exports"])


@router.get("", response_model=PickedPaperExportResponse)
def export_picked_papers(
    user_id: UUID = Depends(require_current_user_id),
) -> PickedPaperExportResponse:
    try:
        return paper_export_service.build_picked_papers_export(user_id)
    except (
        SupabaseConfigError,
        paper_export_service.PaperExportStorageError,
    ) as error:
        raise_storage_http_error(error)


@router.get("/pdf-zip")
def export_picked_papers_pdf_zip(
    user_id: UUID = Depends(require_current_user_id),
) -> Response:
    try:
        zip_content = paper_export_service.build_picked_papers_pdf_zip(user_id)
    except (
        SupabaseConfigError,
        paper_export_service.PaperExportStorageError,
    ) as error:
        raise_storage_http_error(error)

    return Response(
        content=zip_content,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                'attachment; filename="picked-papers-notebooklm.zip"'
            )
        },
    )
