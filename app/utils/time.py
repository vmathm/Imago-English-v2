from __future__ import annotations

from datetime import datetime, timezone, timedelta, time, date
from zoneinfo import ZoneInfo

SP_TZ = ZoneInfo("America/Sao_Paulo")

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def now_sp() -> datetime:
    return datetime.now(SP_TZ)

def sp_midnight_as_utc(d: date) -> datetime:
    """
    Given a São Paulo *date*, return São Paulo midnight converted to UTC (aware).
    Store this in timestamptz columns.
    """
    local_midnight = datetime.combine(d, time.min, tzinfo=SP_TZ)
    return local_midnight.astimezone(timezone.utc)

def sp_midnight_utc_days_from_now(days: int) -> datetime:
    return sp_midnight_as_utc(now_sp().date() + timedelta(days=days))
