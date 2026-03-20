import re
from datetime import datetime, timedelta, timezone

# Supports:
# "IST +05:30"
# "+05:30"
# "UTC+05:30"
# "GMT +05:30"
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


def local_now_from_timezone_text(tz_text: str) -> datetime:
    offset_minutes = parse_offset_minutes(tz_text)
    return utc_now() + timedelta(minutes=offset_minutes)


def get_checkin_window(local_dt: datetime) -> str | None:
    hhmm = local_dt.strftime("%H:%M")

    if "08:00" <= hhmm <= "11:59":
        return "Morning"

    if "16:00" <= hhmm <= "23:59":
        return "Night"

    return None