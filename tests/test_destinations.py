import pytest
import yaml

from destinations import YamlDestinationRepository, resolve_plan
from destination_exchange import review_import, commit_import, export_destinations


@pytest.fixture
def repository(tmp_path):
    return YamlDestinationRepository(tmp_path / "destinations.yaml")


def test_repository_roundtrip(repository):
    record = {"id": "a", "name": "Café", "location": "Example address"}
    repository.add(record)
    assert repository.get("a") == record
    with pytest.raises(ValueError):
        repository.add(record)


def test_resolve_plan(repository):
    repository.add({"id": "a", "name": "Café", "location": "Example address"})
    plan = {"stops": [{"destination_id": "a", "service_minutes": 20}]}
    resolved = resolve_plan(plan, repository)
    assert resolved["stops"][0]["name"] == "Café"
    assert resolved["stops"][0]["service_minutes"] == 20
    assert "service_minutes" not in repository.get("a")
    assert plan["stops"][0]["destination_id"] == "a"


def test_incomplete_record_cannot_be_planned(repository):
    repository.add({"id": "a", "name": "Café"})
    with pytest.raises(ValueError, match="no location"):
        resolve_plan({"stops": [{"destination_id": "a"}]}, repository)


@pytest.mark.parametrize("format", ["yaml", "csv"])
def test_exchange_roundtrip(repository, format, tmp_path):
    record = {"id": "a", "name": "=Example", "opening_hours": [
        {"days": ["Mon"], "times": ["09:00-12:00"]}], "tags": ["test"]}
    repository.add(record)
    other = YamlDestinationRepository(tmp_path / "other.yaml")
    candidates = review_import(export_destinations(repository, format), format, other)
    assert candidates[0].record == record
    assert commit_import(candidates, [0], other)[0].status == "added"
    assert other.get("a") == record


def test_review_and_selective_commit(repository):
    repository.add({"id": "a", "name": "Existing"})
    records = [{"id": "a", "name": "Existing"}, {"id": "a", "name": "Changed"},
               {"id": "b", "name": "New"}, {"id": "c", "name": "Existing"}, {}]
    candidates = review_import(yaml.safe_dump(records), "yaml", repository)
    assert [c.status for c in candidates] == ["identical", "duplicate_in_import", "new", "potential_duplicate", "invalid"]
    assert commit_import(candidates, [2], repository)[0].status == "added"
    assert len(repository.list()) == 2


def test_stale_review_cannot_overwrite(repository):
    candidates = review_import("- id: a\n  name: First\n", "yaml", repository)
    repository.add({"id": "a", "name": "Second"})
    assert commit_import(candidates, [0], repository)[0].status == "rejected"
    assert repository.get("a")["name"] == "Second"
