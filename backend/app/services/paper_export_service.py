"""PickUp済み論文を外部ツール向けにexportするserviceです。"""

from io import BytesIO
import re
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

import httpx

from app.repositories import paper_repository
from app.schemas.analyses import PaperAIAnalysisResponse
from app.schemas.exports import PickedPaperExportResponse
from app.schemas.papers import PaperResponse
from app.schemas.signals import RelatedSignalResponse
from app.services import paper_analysis_service, paper_service


PaperExportStorageError = paper_repository.PaperRepositoryError
PaperExportDownloadError = RuntimeError
ARXIV_PDF_BASE_URL = "https://arxiv.org/pdf/"


def _build_pdf_url(paper: PaperResponse) -> str | None:
    if paper.arxiv_id is None:
        return None
    return f"{ARXIV_PDF_BASE_URL}{paper.arxiv_id}"


def _slugify_filename(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return normalized[:80] or "paper"


def _get_analysis(paper: PaperResponse) -> PaperAIAnalysisResponse | None:
    try:
        return paper_analysis_service.get_paper_ai_analysis(paper.id)
    except paper_analysis_service.PaperAnalysisStorageError:
        return None


def _get_related_signals(paper: PaperResponse) -> list[RelatedSignalResponse]:
    try:
        return paper_repository.list_related_signals(paper.id)
    except paper_repository.PaperRepositoryError:
        return []


def _format_difficulty(value: int | None) -> str:
    if value is None:
        return "未生成"
    normalized_value = min(max(value, 1), 5)
    return "★" * normalized_value + "☆" * (5 - normalized_value)


def _build_markdown_note(papers: list[PaperResponse]) -> tuple[str, list[str]]:
    lines = [
        "# PickUp Papers",
        "",
        "NotebookLMなどの外部ツールに渡すためのPickUp済み論文ノートです。",
        "",
    ]
    warnings: list[str] = []

    for index, paper in enumerate(papers, start=1):
        analysis = _get_analysis(paper)
        signals = _get_related_signals(paper)
        pdf_url = _build_pdf_url(paper)
        if pdf_url is None:
            warnings.append(f"{paper.title}: arXiv IDがないためPDF URLを生成できません。")

        lines.extend(
            [
                f"## {index}. {paper.title}",
                "",
                f"- arXiv ID: {paper.arxiv_id or 'なし'}",
                f"- PDF: {pdf_url or 'なし'}",
                f"- 原文: {paper.source_url or 'なし'}",
                f"- 公開日: {paper.published_at.isoformat() if paper.published_at else '不明'}",
                "",
            ]
        )

        if analysis is None:
            lines.extend(["### AI分析", "", "未生成", ""])
        else:
            lines.extend(
                [
                    "### AI要約",
                    "",
                    analysis.summary_ja,
                    "",
                    "### 難易度",
                    "",
                    f"- 実装難易度: {_format_difficulty(analysis.implementation_difficulty)}",
                    f"  - {analysis.implementation_reason}",
                    f"- 読解難易度: {_format_difficulty(analysis.reading_difficulty)}",
                    f"  - {analysis.reading_reason}",
                    f"- 数学難易度: {_format_difficulty(analysis.math_difficulty)}",
                    f"  - {analysis.math_reason}",
                    "",
                ]
            )

        if signals:
            lines.extend(["### 関連情報", ""])
            for signal in signals:
                lines.append(f"- {signal.source_type}: [{signal.title}]({signal.source_url})")
            lines.append("")

        if paper.abstract:
            lines.extend(["### Abstract", "", paper.abstract, ""])

    return "\n".join(lines).strip() + "\n", warnings


def _build_notebooklm_prompt(papers: list[PaperResponse]) -> str:
    return (
        "以下のPDF群は、私がPickUpした論文です。\n"
        "これらを横断的に読み、次の観点で日本語で整理してください。\n\n"
        "1. 共通テーマを3〜5個に分類する\n"
        "2. 最初に読むべき順番を提案する\n"
        "3. 情報系の学生が理解するための前提知識を整理する\n"
        "4. 実装に近い論文と、理論寄りの論文を分ける\n"
        "5. それぞれの論文について、何が新しく、何が嬉しいのかを説明する\n"
        "6. 自分で実装・検証するなら何から始めるべきか提案する\n\n"
        "対象論文:\n"
        + "\n".join(
            f"- {paper.title} ({_build_pdf_url(paper) or paper.source_url or 'URLなし'})"
            for paper in papers
        )
    )


def build_picked_papers_export(user_id: UUID) -> PickedPaperExportResponse:
    papers = paper_service.list_picked_papers(user_id)
    pdf_urls = [
        pdf_url
        for paper in papers
        if (pdf_url := _build_pdf_url(paper)) is not None
    ]
    markdown_note, warnings = _build_markdown_note(papers)
    return PickedPaperExportResponse(
        pdf_urls=pdf_urls,
        markdown_note=markdown_note,
        notebooklm_prompt=_build_notebooklm_prompt(papers),
        warnings=warnings,
    )


def _download_pdf(pdf_url: str) -> bytes:
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(pdf_url)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as error:
        raise PaperExportDownloadError(str(error)) from error


def build_picked_papers_pdf_zip(user_id: UUID) -> bytes:
    papers = paper_service.list_picked_papers(user_id)
    zip_buffer = BytesIO()
    failed_downloads: list[str] = []
    markdown_note, _warnings = _build_markdown_note(papers)

    with ZipFile(zip_buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("picked-papers-note.md", markdown_note)
        zip_file.writestr("notebooklm-prompt.txt", _build_notebooklm_prompt(papers))

        for index, paper in enumerate(papers, start=1):
            pdf_url = _build_pdf_url(paper)
            if pdf_url is None:
                continue

            filename = f"{index:02d}-{paper.arxiv_id}-{_slugify_filename(paper.title)}.pdf"
            try:
                zip_file.writestr(filename, _download_pdf(pdf_url))
            except PaperExportDownloadError:
                failed_downloads.append(f"{paper.title}: {pdf_url}")

        if failed_downloads:
            zip_file.writestr(
                "failed-downloads.txt",
                "\n".join(failed_downloads) + "\n",
            )

    return zip_buffer.getvalue()
