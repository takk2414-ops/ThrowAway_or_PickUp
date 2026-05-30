"""日次処理の日付判定をまとめるutilityです。"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


JAPAN_TIME_ZONE = ZoneInfo("Asia/Tokyo")
DAILY_RESET_HOUR_JST = 4


def today_jst() -> date:
    """ユーザー向けの日次リストで使うJSTの日付を返します。"""

    return datetime.now(JAPAN_TIME_ZONE).date()


def current_daily_reset_started_at(now: datetime | None = None) -> datetime:
    """現在の4:00 JST区切りの開始時刻をUTCで返します。"""

    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)

    current_time_jst = current_time.astimezone(JAPAN_TIME_ZONE)
    reset_date = current_time_jst.date()
    if current_time_jst.time() < time(hour=DAILY_RESET_HOUR_JST):
        reset_date -= timedelta(days=1)

    reset_started_at_jst = datetime.combine(
        reset_date,
        time(hour=DAILY_RESET_HOUR_JST),
        tzinfo=JAPAN_TIME_ZONE,
    )
    return reset_started_at_jst.astimezone(UTC)
