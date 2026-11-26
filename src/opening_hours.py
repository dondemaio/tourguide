import re
from datetime import date, datetime, time


DAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def opening_hours_to_time_windows(opening_hours, route_date):
    """Expand structured recurring hours and date overrides into local windows."""
    if not isinstance(opening_hours, list):
        raise ValueError("Opening hours must be a list")
    recurring = []
    exceptions = {}
    for entry in opening_hours:
        if not isinstance(entry, dict) or "times" not in entry:
            raise ValueError("Opening-hours entries require times")
        if not isinstance(entry["times"], list):
            raise ValueError("Opening-hours times must be a list")
        intervals = [_parse_time_range(value) for value in entry["times"]]
        if "date" in entry:
            if set(entry) != {"date", "times"}:
                raise ValueError("Date exceptions cannot contain recurring rules")
            day = date.fromisoformat(str(entry["date"]))
            if day in exceptions:
                raise ValueError(f"Duplicate opening-hours exception: {day}")
            exceptions[day] = intervals
        else:
            if set(entry) - {"days", "times", "week_of_month"} or not isinstance(entry.get("days"), list) or not entry["days"]:
                raise ValueError("Recurring opening hours require days and times")
            days = [_parse_day(day) for day in entry["days"]]
            week = entry.get("week_of_month")
            if "week_of_month" in entry and (type(week) is not int or not 1 <= week <= 5):
                raise ValueError("week_of_month must be an integer from 1 to 5")
            if route_date.weekday() in days and (week is None or week == (route_date.day - 1) // 7 + 1):
                recurring.extend(intervals)

    merged = []
    for start, end in sorted(exceptions.get(route_date, recurring)):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return [[datetime.combine(route_date, start).isoformat(timespec="minutes"),
             datetime.combine(route_date, end).isoformat(timespec="minutes")]
            for start, end in merged]


def _parse_day(day):
    key = str(day).strip().lower()
    if key not in DAY_ALIASES:
        raise ValueError(f"Unknown opening-hours day: {day}")
    return DAY_ALIASES[key]


def _parse_time_range(value):
    parts = str(value).split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid opening-hours time range: {value}")
    start, end = map(_parse_time, parts)
    if start >= end:
        raise ValueError(f"Opening-hours range must start before it ends: {value}")
    return start, end


def _parse_time(value):
    if not re.fullmatch(r"\d{2}:\d{2}", value.strip()):
        raise ValueError(f"Invalid opening-hours time: {value}")
    hour, minute = map(int, value.strip().split(":"))
    return time(hour, minute)
