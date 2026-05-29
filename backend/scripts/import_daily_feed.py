"""4:00 JSTのcronから呼ぶ日次表示リスト生成スクリプトです。"""

from pathlib import Path
import sys


sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.schemas.paper import DailyImportRequest  # noqa: E402
from app.services import paper_service  # noqa: E402


def main() -> None:
    response = paper_service.import_daily_papers(DailyImportRequest())
    print(
        "daily feed import completed: "
        f"date={response.import_date.isoformat()} "
        f"imported_count={response.imported_count} "
        f"paper_count={len(response.papers)} "
        f"skipped={response.skipped} "
        f"ai_analysis_generated_count={response.ai_analysis_generated_count} "
        f"ai_analysis_failed_count={response.ai_analysis_failed_count}"
    )


if __name__ == "__main__":
    main()
