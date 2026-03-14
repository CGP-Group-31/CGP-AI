import re
from datetime import datetime, date, time, timedelta, timezone

_TZ_OFFSET_RE = re.compile(r"([+-])\s*(\d{2}):(\d{2})")


def parse_offset_minutes(tz_text: str) -> int:
    if not tz_text:
        return 0

    match = _TZ_OFFSET_RE.search(tz_text)
    if not match:
        return 0

    sign = 1 if match.group(1) == "+" else -1
    hh = int(match.group(2))
    mm = int(match.group(3))

    return sign * (hh * 60 + mm)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_to_local(utc_dt: datetime, offset_minutes: int) -> datetime:
    return utc_dt + timedelta(minutes=offset_minutes)


def local_date_for_offset(offset_minutes: int) -> date:
    return utc_to_local(utc_now(), offset_minutes).date()


def local_time_for_offset(offset_minutes: int) -> time:
    return utc_to_local(utc_now(), offset_minutes).time()


def local_slot_to_utc(local_d: date, local_t: time, offset_minutes: int) -> datetime:
    local_dt = datetime.combine(local_d, local_t)
    utc_dt = local_dt - timedelta(minutes=offset_minutes)
    return utc_dt.replace(tzinfo=timezone.utc)