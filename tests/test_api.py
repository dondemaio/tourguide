from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from api import create_app
from application import Application
from destinations import YamlDestinationRepository


@pytest.fixture
def client(tmp_path):
    plan = tmp_path / "plan.yaml"
    plan.write_text("stops: []\n", encoding="utf-8")
    application = Application(YamlDestinationRepository(tmp_path / "destinations.yaml"), {}, plan)
    with TestClient(create_app(application)) as client:
        yield client


def test_health_and_default_plan(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/plans/default").json() == {"stops": []}


def test_destination_crud(client):
    record = {"id": "a", "name": "Museum"}
    assert client.post("/api/destinations", json=record).status_code == 201
    assert client.get("/api/destinations/a").json() == record
    record["name"] = "Updated"
    assert client.put("/api/destinations/a", json=record).status_code == 200
    assert client.get("/api/destinations").json() == [record]
    assert client.delete("/api/destinations/a").status_code == 204
    assert client.get("/api/destinations/a").status_code == 404


def test_invalid_destination(client):
    assert client.post("/api/destinations", json={"name": "Missing ID"}).status_code == 422


def test_import_and_export(client):
    response = client.post("/api/import/review", json={
        "format": "csv", "content": "Name,Address\nMuseum,Example\n"})
    assert response.status_code == 200
    candidates = response.json()
    assert candidates[0]["status"] == "new"
    response = client.post("/api/import/commit", json={
        "candidates": candidates, "selected_indices": [0]})
    assert response.json()[0]["status"] == "added"
    assert "Museum" in client.post("/api/export", json={"format": "csv"}).text


def test_route_contract(client, monkeypatch):
    calculate = Mock(return_value={"route": {}, "rendering": {}})
    monkeypatch.setattr(client.app.state.application, "calculate", calculate)
    endpoint = {"location": "Example", "time_window": ["2026-11-23T09:00", "2026-11-23T10:00"]}
    plan = {"timezone": "Europe/Zurich", "start": endpoint, "end": endpoint,
            "stops": [{"destination_id": "a"}]}
    assert client.post("/api/routes", json=plan).status_code == 200
    calculate.assert_called_once_with(plan)
    plan["stops"][0]["required"] = "false"
    assert client.post("/api/routes", json=plan).status_code == 422
