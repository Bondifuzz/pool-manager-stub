from datetime import datetime, timedelta, timezone
from re import Match
from re import match as regex_match


def to_utc(date: datetime):
    return date.astimezone(timezone.utc)


def date_now():
    return datetime.now(tz=timezone.utc)


def date_future(date: datetime, add_seconds: int):
    return date + timedelta(seconds=add_seconds)


def date_pretty(date: datetime):
    return date.strftime("%c")


def rfc3339(date: datetime):
    return date.strftime(r"%Y-%m-%dT%H:%M:%SZ")


def from_rfc3339(s: str):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def validate_rfc3339(s: str):

    if not s.endswith("Z"):
        raise ValueError("Date must end with 'Z'")

    try:
        from_rfc3339(s)
    except ValueError as e:
        raise ValueError("Not a valid rfc3339 date") from e


def duration_in_seconds(value: str):

    match: Match = regex_match(r"^(\d+)([s,m,h,d])$", value)

    if not match:
        raise ValueError("Usage: 30s, 5m, 2h, 1d")

    units_dict = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
    }

    ival = int(match.group(1))
    unit = match.group(2)

    return ival * units_dict[unit]
