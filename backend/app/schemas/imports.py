"""論文取り込みAPIのschemaです。"""

from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.schemas.papers import PaperResponse


class ArxivImportRequest(BaseModel):
    # arXiv APIから論文を取り込むときの入力形式です。
    search_query: str = Field("cat:cs.AI", min_length=1, max_length=200)
    max_results: int = Field(10, ge=1, le=50)


class ArxivImportResponse(BaseModel):
    # arXiv APIから取り込んだ論文の結果です。
    imported_count: int
    papers: list[PaperResponse]


class DailyImportRequest(BaseModel):
    # 毎日4:00 JSTに実行する日次表示リスト生成の入力形式です。
    search_query: str = Field("cat:cs.AI", min_length=1, max_length=200)
    max_results: int = Field(10, ge=1, le=50)
    signal_categories: list[str] = Field(
        default_factory=lambda: ["cs.AI", "cs.CL", "cs.LG"]
    )
    signal_max_results_per_category: int = Field(30, ge=1, le=50)
    signal_max_papers: int = Field(10, ge=1, le=20)
    signal_min_days_old: int = Field(0, ge=0, le=365)
    signal_max_days_old: int = Field(90, ge=1, le=365)

    @model_validator(mode="after")
    def validate_signal_day_range(self) -> "DailyImportRequest":
        if self.signal_min_days_old > self.signal_max_days_old:
            raise ValueError(
                "signal_min_days_old must be less than or equal to "
                "signal_max_days_old"
            )
        return self


class DailyImportResponse(BaseModel):
    # その日の表示リスト生成結果です。すでに生成済みなら skipped=True になります。
    import_date: date
    imported_count: int
    papers: list[PaperResponse]
    skipped: bool
    ai_analysis_generated_count: int = 0
    ai_analysis_failed_count: int = 0


class RisingImportRequest(BaseModel):
    # 関連シグナルが出始めた論文を取り込むときの入力形式です。
    categories: list[str] = Field(default_factory=lambda: ["cs.AI", "cs.CL", "cs.LG"])
    max_results_per_category: int = Field(10, ge=1, le=20)
    max_papers: int = Field(10, ge=1, le=20)
    min_days_old: int = Field(14, ge=1, le=365)
    max_days_old: int = Field(60, ge=1, le=365)

    @model_validator(mode="after")
    def validate_day_range(self) -> "RisingImportRequest":
        if self.min_days_old > self.max_days_old:
            raise ValueError("min_days_old must be less than or equal to max_days_old")
        return self


class RisingImportResponse(BaseModel):
    # 関連シグナルがある論文の取り込み結果です。
    imported_count: int
    papers: list[PaperResponse]
    signal_counts: dict[str, int] = Field(default_factory=dict)
    source_errors: list[str] = Field(default_factory=list)
