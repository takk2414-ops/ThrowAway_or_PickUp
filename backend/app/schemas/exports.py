"""外部ツール連携exportのschemaです。"""

from pydantic import BaseModel, Field


class PickedPaperExportResponse(BaseModel):
    # NotebookLMなど外部ツールへ渡すためのPickUp済み論文exportです。
    pdf_urls: list[str]
    markdown_note: str
    notebooklm_prompt: str
    warnings: list[str] = Field(default_factory=list)
