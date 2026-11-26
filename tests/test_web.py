from unittest.mock import Mock

from fastapi.testclient import TestClient

from api import create_app
from application import Application


def test_web_assets():
    with TestClient(create_app(Mock())) as client:
        assert client.get("/").status_code == 200
        assert "Calculate route" in client.get("/").text
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/static/style.css").status_code == 200


def test_osrm_geometry_preserves_configured_rendering(monkeypatch, tmp_path):
    config = {"cost_provider": {"backend": "osrm"}, "route_renderer": {"backend": "google-web"}}
    app = Application(Mock(), config, tmp_path / "plan.yaml")
    route = {"visits": []}
    monkeypatch.setattr("application.calculate_route", Mock(return_value=route))
    geometry = {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[8, 47], [9, 48]]}}
    render = Mock(side_effect=["https://www.google.com/maps/dir/", geometry])
    monkeypatch.setattr("application.render_route", render)
    result = app.calculate({})
    assert result["geometry"] == geometry
    assert result["rendering"] == "https://www.google.com/maps/dir/"
    assert config["route_renderer"]["backend"] == "google-web"
    assert render.call_args.args[1]["route_renderer"]["backend"] == "geojson"


def test_geometry_failure_preserves_itinerary(monkeypatch, tmp_path):
    app = Application(Mock(), {"cost_provider": {"backend": "osrm"}, "route_renderer": {"backend": "google-web"}}, tmp_path / "plan.yaml")
    monkeypatch.setattr("application.calculate_route", Mock(return_value={"visits": []}))
    monkeypatch.setattr("application.render_route", Mock(side_effect=["link", RuntimeError("failure")]))
    result = app.calculate({})
    assert result["geometry"] is None
    assert result["geometry_warning"]
    assert result["route"] == {"visits": []}
