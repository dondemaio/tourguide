import json
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pytest
from backends.factory import create_geocoder, create_cost_provider, create_route_renderer
from backends.google.cost import GoogleCostProvider
from backends.google.web.render import GoogleMapsURLRenderer
from backends.nominatim.geocode import NominatimGeocoder
from backends.osrm.cost import OSRMCostProvider
from backends.osrm.render import OSRMRouteRenderer


def test_osrm_matrix(monkeypatch):
    response = Mock()
    response.json.return_value = {"code": "Ok", "durations": [[0, 12.5], [13, 0]]}
    get = Mock(return_value=response)
    monkeypatch.setattr("backends.osrm.cost.requests.get", get)
    assert OSRMCostProvider("http://osrm/").build_time_matrix(["8,47", "9,48"]) == [[0, 12.5], [13, 0]]
    get.assert_called_once_with("http://osrm/table/v1/driving/8,47;9,48",
                                params={"annotations": "duration"}, timeout=30)
    response.raise_for_status.assert_called_once()


def test_osrm_error(monkeypatch):
    response = Mock()
    response.json.return_value = {"code": "NoTable"}
    monkeypatch.setattr("backends.osrm.cost.requests.get", Mock(return_value=response))
    with pytest.raises(RuntimeError):
        OSRMCostProvider("http://osrm").build_time_matrix(["8,47", "9,48"])


def test_geojson_uses_ordered_coordinates(monkeypatch):
    geometry = {"type": "LineString", "coordinates": [[8, 47], [9, 48]]}
    response = Mock()
    response.json.return_value = {"routes": [{"geometry": geometry}]}
    get = Mock(return_value=response)
    monkeypatch.setattr("backends.osrm.render.requests.get", get)
    result = OSRMRouteRenderer("http://osrm", "geojson").build_route(
        ["End", "Start"], ["9,48", "8,47"], [1, 0])
    assert json.loads(result) == {"type": "Feature", "geometry": geometry, "properties": {}}
    get.assert_called_once_with("http://osrm/route/v1/driving/8,47;9,48",
                                params={"overview": "full", "geometries": "geojson", "steps": "true"},
                                timeout=30)


def test_google_maps_url_preserves_order_and_addresses():
    url = GoogleMapsURLRenderer().build_route(["Zürich & Co", "Bern", "Luzern"], [], [1, 0, 2])
    assert parse_qs(urlparse(url).query) == {
        "api": ["1"], "origin": ["Bern"], "destination": ["Luzern"],
        "waypoints": ["Zürich & Co"], "travelmode": ["driving"],
    }


def test_nominatim_geocodes_addresses_and_passes_coordinates(monkeypatch):
    response = Mock()
    response.json.return_value = [{"lon": "8.5", "lat": "47.3"}]
    get = Mock(return_value=response)
    monkeypatch.setattr("backends.nominatim.geocode.requests.get", get)
    sleep = Mock()
    monkeypatch.setattr("backends.nominatim.geocode.time.sleep", sleep)
    assert NominatimGeocoder(delay=1).geocode(["8,47", "Zürich"]) == ["8,47", "8.5,47.3"]
    get.assert_called_once()
    assert get.call_args.kwargs["params"]["q"] == "Zürich"
    sleep.assert_called_once_with(1)


def test_factory_selects_backends():
    cfg = {"cost_provider": {"backend": "osrm", "osrm": {"base_url": "http://osrm"}},
           "route_renderer": {"backend": "geojson"}}
    assert create_geocoder({}) is None
    assert isinstance(create_geocoder({"backend": "nominatim"}), NominatimGeocoder)
    assert isinstance(create_cost_provider(cfg), OSRMCostProvider)
    assert create_route_renderer(cfg).style == "geojson"


@pytest.mark.parametrize("factory, config", [
    (create_geocoder, {"backend": "unknown"}),
    (create_cost_provider, {"cost_provider": {"backend": "unknown"}}),
    (create_route_renderer, {"route_renderer": {"backend": "unknown"}}),
])
def test_factory_rejects_unknown_backend(factory, config):
    with pytest.raises(ValueError, match="Unknown"):
        factory(config)


def test_google_zero_results_is_unreachable(monkeypatch):
    response = Mock()
    response.json.return_value = {"status": "OK", "rows": [
        {"elements": [{"status": "OK", "duration": {"value": 0}}, {"status": "ZERO_RESULTS"}]},
        {"elements": [{"status": "OK", "duration": {"value": 60}}, {"status": "OK", "duration": {"value": 0}}]},
    ]}
    monkeypatch.setattr("backends.google.cost.requests.get", Mock(return_value=response))
    assert GoogleCostProvider("dummy").build_time_matrix(["A", "B"], 0) == [[0, None], [60, 0]]


def test_google_other_element_errors_remain_errors(monkeypatch):
    response = Mock()
    response.json.return_value = {"status": "OK", "rows": [{"elements": [{"status": "NOT_FOUND"}]}]}
    monkeypatch.setattr("backends.google.cost.requests.get", Mock(return_value=response))
    with pytest.raises(RuntimeError, match="Matrix element error"):
        GoogleCostProvider("dummy").build_time_matrix(["A"], 0)
