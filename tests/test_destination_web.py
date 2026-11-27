from unittest.mock import Mock

from fastapi.testclient import TestClient

from api import create_app


def test_destination_management_page():
    with TestClient(create_app(Mock())) as client:
        page = client.get("/destinations")
        assert page.status_code == 200
        assert "Destination catalog" in page.text
        assert 'id="drawer"' in page.text
        assert "Review import" not in page.text
        assert client.get("/static/destinations.js").status_code == 200
        assert client.get("/static/destinations.css").status_code == 200
        assert 'href="/destinations"' in client.get("/").text


def test_catalog_returns_existing_destinations(tmp_path):
    from application import Application
    from destinations import YamlDestinationRepository

    repository = YamlDestinationRepository(tmp_path / "destinations.yaml")
    record = {"id": "museum", "name": "Museum", "location": "Example address"}
    repository.add(record)
    with TestClient(create_app(Application(repository, {}, tmp_path / "plan.yaml"))) as client:
        assert client.get("/api/destinations").json() == [record]
