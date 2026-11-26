from unittest.mock import Mock

from fastapi.testclient import TestClient

from api import create_app


def test_destination_management_page():
    with TestClient(create_app(Mock())) as client:
        page = client.get("/destinations")
        assert page.status_code == 200
        assert "Destination repository" in page.text
        assert "Review import" in page.text
        assert client.get("/static/destinations.js").status_code == 200
        assert client.get("/static/destinations.css").status_code == 200
        assert 'href="/destinations"' in client.get("/").text
