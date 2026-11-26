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


def test_yaml_exchange_roundtrip(repository, tmp_path):
    record = {"id": "a", "name": "=Example", "opening_hours": [
        {"days": ["Mon"], "times": ["09:00-12:00"]}], "tags": ["test"]}
    repository.add(record)
    other = YamlDestinationRepository(tmp_path / "other.yaml")
    candidates = review_import(export_destinations(repository, "yaml"), "yaml", other)
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


def test_csv_candidate_import(repository):
    candidates = review_import("Name;Address;Website;Opening hours;Notes\nCafé;Bern;;Mon-Fri 9-18;Check hours\n", "csv", repository)
    candidate = candidates[0]
    assert candidate.status == "new"
    assert candidate.record["name"] == "Café"
    assert candidate.record["location"] == "Bern"
    assert "opening_hours" not in candidate.record
    assert candidate.record["provenance"]["candidate"]["opening hours"] == "Mon-Fri 9-18"
    assert commit_import(candidates, [0], repository)[0].status == "added"
    assert review_import("Name,Address\nCafé,Bern\n", "csv", repository)[0].status == "potential_duplicate"


def test_csv_large_field(repository):
    notes = "x" * 140000
    candidates = review_import("Name,Notes\nMuseum," + notes + "\n", "csv", repository)
    assert candidates[0].record["provenance"]["candidate"]["notes"] == notes


def test_csv_incomplete_and_invalid_candidates(repository):
    candidates = review_import("Name,Website,Notes\n,https://example.org,Check\n,,Only notes\n", "csv", repository)
    assert candidates[0].status == "new"
    assert candidates[1].status == "invalid"


def test_csv_overview(repository):
    repository.add({"id": "a", "name": "=Example", "opening_hours": [
        {"days": ["Mon"], "times": ["09:00-12:00"]}]})
    output = export_destinations(repository, "csv")
    assert "name,address,website,opening hours,notes" in output
    assert "'=Example" in output
    assert "Mon: 09:00-12:00" in output
    assert "provider_ids" not in output


def test_csv_malformed_document(repository):
    with pytest.raises(ValueError, match="Invalid CSV"):
        review_import('Name,Notes\nMuseum,"unfinished', "csv", repository)
