from unittest.mock import Mock

from destinations import YamlDestinationRepository
from route_service import calculate_route, render_route


def test_calculate_and_render_route(monkeypatch, tmp_path):
    repository = YamlDestinationRepository(tmp_path / "destinations.yaml")
    repository.add({"id": "museum", "name": "Museum", "location": "Example address",
                    "provider_ids": {"example": "123"},
                    "opening_hours": [{"days": ["Mon"], "times": ["09:05-10:00"]}]})
    repository.add({"id": "closed", "name": "Closed museum", "location": "Other address",
                    "opening_hours": [{"days": ["Tue"], "times": ["09:00-10:00"]}]})
    plan = {"timezone": "Europe/Zurich",
            "start": {"id": "start", "location": "Origin",
                      "time_window": ["2026-11-23T09:00", "2026-11-23T09:00"]},
            "end": {"id": "end", "location": "End",
                    "time_window": ["2026-11-23T09:10", "2026-11-23T09:10"]},
            "stops": [{"destination_id": "museum", "service_minutes": 2},
                      {"destination_id": "closed", "required": False, "priority": 4}]}
    geocoder = Mock()
    geocoder.geocode.return_value = ["1,1", "2,2", "3,3"]
    provider = Mock()
    provider.build_time_matrix.return_value = [[0, 60, 60], [60, 0, 60], [60, 60, 0]]
    monkeypatch.setattr("route_service.create_geocoder", lambda config: geocoder)
    monkeypatch.setattr("route_service.create_cost_provider", lambda config: provider)
    config = {"solver": {"time_limit_seconds": 1}}
    result = calculate_route(plan, repository, config)
    assert result["omitted_visits"] == [{"visit_index": 1, "destination_id": "closed",
                                         "name": "Closed museum", "priority": 4,
                                         "reason": "no_fitting_opening_window"}]
    visit = result["visits"][1]
    assert visit["destination_id"] == "museum"
    assert visit["name"] == "Museum"
    assert visit["provider_ids"] == {"example": "123"}
    assert visit["arrival"] == "2026-11-23T09:01:00+01:00"
    assert visit["service_start"] == "2026-11-23T09:05:00+01:00"
    assert visit["departure"] == "2026-11-23T09:07:00+01:00"
    assert result["totals"] == {"travel_seconds": 120, "waiting_seconds": 360,
                                "service_seconds": 120, "elapsed_seconds": 600}
    renderer = Mock()
    monkeypatch.setattr("route_service.create_route_renderer", lambda config: renderer)
    assert render_route(result, config) == renderer.build_route.return_value
    renderer.build_route.assert_called_once_with(
        ["Origin", "Example address", "End"], ["1,1", "2,2", "3,3"], [0, 1, 2])
