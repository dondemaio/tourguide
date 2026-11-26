import math
from copy import deepcopy
from datetime import datetime
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dateutil.parser import isoparse
from dateutil.tz import datetime_exists, datetime_ambiguous

from opening_hours import opening_hours_to_time_windows


def _timestamp(value, zone):
    dt = isoparse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zone)
        if not datetime_exists(dt) or datetime_ambiguous(dt):
            raise ValueError(f"Ambiguous or nonexistent local time: {value}")
    if dt.microsecond:
        raise ValueError("Planning timestamps must use whole seconds")
    return int(dt.timestamp())


def _duration(node):
    minutes = node.get("service_minutes", 0)
    if type(minutes) not in (int, float) or not 0 <= minutes <= 1440:
        raise ValueError("service_minutes must be between 0 and 1440")
    return math.ceil(minutes * 60)


DEFAULT_PRIORITY = 3
PRIORITY_PENALTY_SECONDS = 1800


@dataclass
class PreparedPlan:
    nodes: list
    windows: list
    services: list
    groups: list
    base_ts: int
    optional_groups: list
    omitted: list


def prepare_plan(data):
    """Return nodes, relative service-start windows, durations, mandatory groups, epoch, optional groups and omissions."""
    zone = ZoneInfo(data["timezone"])
    start, end = data["start"], data["end"]
    start_low, start_high = [_timestamp(v, zone) for v in start["time_window"]]
    end_low, end_high = [_timestamp(v, zone) for v in end["time_window"]]
    if not start_low <= start_high <= end_high or not start_low <= end_low <= end_high:
        raise ValueError("Invalid start/end planning windows")
    route_date = datetime.fromtimestamp(start_low, zone).date()
    if datetime.fromtimestamp(end_high, zone).date() != route_date or end_high - start_low > 86400:
        raise ValueError("Only single-day plans of up to 24 hours are supported")
    nodes = [deepcopy(start)]
    windows = [(0, start_high - start_low)]
    services = [_duration(start)]
    groups = []
    optional_groups = []
    omitted = []
    for visit_index, stop in enumerate(data["stops"]):
        required = stop.get("required", True)
        priority = stop.get("priority", DEFAULT_PRIORITY)
        if type(required) is not bool:
            raise ValueError("required must be boolean")
        if type(priority) is not int or not 1 <= priority <= 5:
            raise ValueError("priority must be an integer from 1 to 5")
        if required and "priority" in stop:
            raise ValueError("priority applies only to optional visits")
        duration = _duration(stop)
        indices = []
        if "opening_hours" not in stop:
            raise ValueError(f"Stop {stop['id']} needs opening_hours")
        for low, high in opening_hours_to_time_windows(stop["opening_hours"], route_date):
            opening = _timestamp(low, zone)
            closing = _timestamp(high, zone)
            earliest = max(start_low, opening)
            latest = min(end_high - duration, closing - max(duration, 1))
            if earliest > latest:
                continue
            indices.append(len(nodes))
            nodes.append({**deepcopy(stop), "visit_index": visit_index})
            windows.append((earliest - start_low, latest - start_low))
            services.append(duration)
        if not indices:
            if not required:
                omitted.append((visit_index, "no_fitting_opening_window"))
                continue
            raise ValueError(f"Stop {stop['id']} has no opening window fitting the visit")
        if not required:
            optional_groups.append((indices, priority * PRIORITY_PENALTY_SECONDS))
        elif len(indices) > 1:
            groups.append(indices)
    nodes.append(deepcopy(end))
    windows.append((end_low - start_low, end_high - start_low))
    services.append(_duration(end))
    return PreparedPlan(nodes, windows, services, groups, start_low, optional_groups, omitted)
