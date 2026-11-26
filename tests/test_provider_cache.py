from unittest.mock import Mock

import pytest

from provider_cache import ProviderCache, geocode_locations, travel_matrix


def test_geocode_reuses_individual_locations(tmp_path):
    path = tmp_path / "cache.sqlite3"
    geocoder = Mock(base_url="https://example.org")
    geocoder.geocode.return_value = ["1,1", "2,2"]
    config = {"geocoder": {"backend": "nominatim"}, "cache": {}}
    assert geocode_locations(geocoder, ["A", "B", "A"], config, ProviderCache(path)) == ["1,1", "2,2", "1,1"]
    assert geocode_locations(geocoder, ["B", "A"], config, ProviderCache(path)) == ["2,2", "1,1"]
    geocoder.geocode.assert_called_once_with(["A", "B"])


def test_matrix_reorders_and_preserves_unreachable_legs(tmp_path):
    cache = ProviderCache(tmp_path / "cache.sqlite3")
    provider = Mock(base_url="http://example.org")
    provider.build_time_matrix.return_value = [[0, None], [12.5, 0]]
    config = {"cost_provider": {"backend": "osrm"}, "cache": {}}
    assert travel_matrix(provider, ["B", "A", "B"], 100, config, cache) == [
        [0, 12.5, 0], [None, 0, None], [0, 12.5, 0]]
    assert travel_matrix(provider, ["A", "B"], 200, config, cache) == [[0, None], [12.5, 0]]
    provider.build_time_matrix.assert_called_once_with(["A", "B"], 100)
    config["cache"]["dataset_revision"] = "new"
    travel_matrix(provider, ["A", "B"], 200, config, cache)
    assert provider.build_time_matrix.call_count == 2


def test_expiry(tmp_path, monkeypatch):
    cache = ProviderCache(tmp_path / "cache.sqlite3")
    monkeypatch.setattr("provider_cache.time.time", lambda: 100)
    cache.put("key", "value", 10)
    assert cache.get("key") == "value"
    monkeypatch.setattr("provider_cache.time.time", lambda: 110)
    assert cache.get("key") is None


def test_provider_failure_not_cached(tmp_path):
    cache = ProviderCache(tmp_path / "cache.sqlite3")
    provider = Mock(base_url="http://example.org")
    provider.build_time_matrix.side_effect = [RuntimeError("offline"), [[0, 0], [0, 0]]]
    config = {"cost_provider": {"backend": "osrm"}, "cache": {}}
    with pytest.raises(RuntimeError):
        travel_matrix(provider, ["A"], 100, config, cache)
    assert travel_matrix(provider, ["A"], 100, config, cache) == [[0]]


def test_google_bypasses_cache(tmp_path):
    cache = ProviderCache(tmp_path / "cache.sqlite3")
    provider = Mock()
    config = {"cost_provider": {"backend": "google"}, "cache": {}}
    travel_matrix(provider, ["A"], 100, config, cache)
    travel_matrix(provider, ["A"], 100, config, cache)
    assert provider.build_time_matrix.call_count == 2


def test_single_unique_location_requests_two_coordinates(tmp_path):
    cache = ProviderCache(tmp_path / "cache.sqlite3")
    provider = Mock(base_url="http://example.org")
    provider.build_time_matrix.return_value = [[0, 0], [0, 0]]
    config = {"cost_provider": {"backend": "osrm"}, "cache": {}}
    assert travel_matrix(provider, ["A", "A"], 100, config, cache) == [[0, 0], [0, 0]]
    assert travel_matrix(provider, ["A", "A", "A"], 200, config, cache) == [[0] * 3] * 3
    provider.build_time_matrix.assert_called_once_with(["A", "A"], 100)
