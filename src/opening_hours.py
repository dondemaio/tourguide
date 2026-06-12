from datetime import datetime, time


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
    windows = []
    weekday = route_date.weekday()

    for entry in opening_hours:
        if "special" in entry:
            continue

        days = entry.get("days", [])
        if weekday not in [_parse_day(day) for day in days]:
            continue

        for time_range in entry.get("times", []):
            start_time, end_time = _parse_time_range(time_range)
            windows.append(
                [
                    datetime.combine(route_date, start_time).isoformat(timespec="minutes"),
                    datetime.combine(route_date, end_time).isoformat(timespec="minutes"),
                ]
            )

    return windows


def _parse_day(day):
    key = str(day).strip().lower()
    if key not in DAY_ALIASES:
        raise ValueError(f"Unknown opening-hours day: {day}")
    return DAY_ALIASES[key]


def _parse_time_range(time_range):
    parts = str(time_range).split("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid opening-hours time range: {time_range}")
    start_text, end_text = parts
    start = _parse_time(start_text)
    end = _parse_time(end_text)
    if start >= end:
        raise ValueError(f"Opening-hours range must start before it ends: {time_range}")
    return start, end


def _parse_time(value):
    parts = value.strip().split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid opening-hours time: {value}")
    hour, minute = parts
    return time(int(hour), int(minute))
