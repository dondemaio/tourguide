from datetime import date
import pytest
from opening_hours import opening_hours_to_time_windows


def test_split_hours_and_aliases():
    hours = [{"days": [" MONDAY ", "Tue"], "times": ["08:30-12:00", "13:30-17:30"]},
             {"days": ["Fri"], "times": ["09:00-10:00"]}]
    assert opening_hours_to_time_windows(hours, date(2026, 11, 23)) == [
        ["2026-11-23T08:30", "2026-11-23T12:00"],
        ["2026-11-23T13:30", "2026-11-23T17:30"],
    ]


def test_closed_day():
    assert opening_hours_to_time_windows(
        [{"days": ["Mon"], "times": ["09:00-10:00"]}], date(2026, 11, 24)
    ) == []


@pytest.mark.parametrize("interval", ["09:00", "10:00-09:00", "09:00-09:00", "25:00-26:00"])
def test_invalid_range(interval):
    with pytest.raises(ValueError):
        opening_hours_to_time_windows(
            [{"days": ["Mon"], "times": [interval]}], date(2026, 11, 23)
        )


def test_unknown_day():
    with pytest.raises(ValueError, match="Unknown opening-hours day"):
        opening_hours_to_time_windows(
            [{"days": ["Funday"], "times": ["09:00-10:00"]}], date(2026, 11, 23)
        )
