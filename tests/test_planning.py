from datetime import date, datetime, timezone

import pytest

from opening_hours import opening_hours_to_time_windows
from planning import prepare_plan


def plan(times, duration=30):
    return {
        "timezone": "Europe/Zurich",
        "start": {"id": "start", "time_window": ["2026-11-23T09:00", "2026-11-23T09:00"]},
        "end": {"id": "end", "time_window": ["2026-11-23T10:00", "2026-11-23T17:00"]},
        "stops": [{"id": "shop", "service_minutes": duration,
                   "opening_hours": [{"days": ["Mon"], "times": times}]}],
    }


def test_clipping_and_service_completion():
    prepared = prepare_plan(plan(["08:00-10:00", "16:00-18:00"]))
    assert prepared.windows == [(0, 0), (0, 1800), (25200, 27000), (3600, 28800)]
    assert prepared.services == [0, 1800, 1800, 0]
    assert prepared.groups == [[1, 2]]
    assert prepared.nodes[1]["id"] == prepared.nodes[2]["id"] == "shop"
    assert prepared.base_ts == int(datetime(2026, 11, 23, 8, tzinfo=timezone.utc).timestamp())


def test_exact_fit():
    assert prepare_plan(plan(["09:00-09:30"])).windows[1] == (0, 0)


def test_short_window_rejected():
    with pytest.raises(ValueError, match="no opening window"):
        prepare_plan(plan(["09:00-09:20"]))


def test_short_alternative_removed():
    assert prepare_plan(plan(["09:00-09:20", "10:00-11:00"])).groups == []


def test_date_exception_overrides_recurring_hours():
    hours = [{"days": ["Mon"], "times": ["09:00-17:00"]},
             {"date": "2026-11-23", "times": []}]
    assert opening_hours_to_time_windows(hours, date(2026, 11, 23)) == []


def test_first_saturday():
    hours = [{"days": ["Sat"], "week_of_month": 1, "times": ["08:00-12:00"]}]
    assert opening_hours_to_time_windows(hours, date(2026, 11, 7)) == [
        ["2026-11-07T08:00", "2026-11-07T12:00"]]
    assert opening_hours_to_time_windows(hours, date(2026, 11, 14)) == []


def test_overlapping_windows_merged():
    hours = [{"days": ["Mon"], "times": ["10:00-12:00", "09:00-11:00"]}]
    assert opening_hours_to_time_windows(hours, date(2026, 11, 23)) == [
        ["2026-11-23T09:00", "2026-11-23T12:00"]]


def test_invalid_hours_on_other_day_rejected():
    with pytest.raises(ValueError):
        opening_hours_to_time_windows([{"days": ["Tue"], "times": ["bad"]}], date(2026, 11, 23))


def test_nonexistent_local_time_rejected():
    data = plan(["09:00-10:00"])
    data["start"]["time_window"] = ["2026-03-29T02:30"] * 2
    with pytest.raises(ValueError, match="nonexistent"):
        prepare_plan(data)


def test_optional_closed_visit_is_omitted():
    data = plan(["09:00-09:20"])
    data["stops"][0]["required"] = False
    prepared = prepare_plan(data)
    assert len(prepared.nodes) == 2
    assert prepared.optional_groups == []
    assert prepared.omitted == [(0, "no_fitting_opening_window")]


def test_optional_alternatives_share_penalty():
    data = plan(["09:00-10:00", "11:00-12:00"])
    data["stops"][0].update(required=False, priority=5)
    result = prepare_plan(data)
    assert result.groups == []
    assert result.optional_groups == [([1, 2], 9000)]


@pytest.mark.parametrize("priority", [0, 6, True, 1.5])
def test_invalid_priority(priority):
    data = plan(["09:00-10:00"])
    data["stops"][0].update(required=False, priority=priority)
    with pytest.raises(ValueError, match="priority"):
        prepare_plan(data)


@pytest.mark.parametrize("window", [None, "09:00", [], ["2026-11-23T09:00"], [None, None]])
def test_invalid_endpoint_window(window):
    data = plan(["09:00-10:00"])
    data["start"]["time_window"] = window
    with pytest.raises(ValueError):
        prepare_plan(data)


def test_invalid_timezone():
    data = plan(["09:00-10:00"])
    data["timezone"] = "Invalid/Zone"
    with pytest.raises(ValueError, match="timezone"):
        prepare_plan(data)
