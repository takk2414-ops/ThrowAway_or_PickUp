"""日次処理の日付判定をまとめるutilityです。"""

from datetime import date, datetime
from zoneinfo import ZoneInfo


JAPAN_TIME_ZONE = ZoneInfo("Asia/Tokyo")


def today_jst() -> date:
    """ユーザー向けの日次リストで使うJSTの日付を返します。"""

    return datetime.now(JAPAN_TIME_ZONE).date()
