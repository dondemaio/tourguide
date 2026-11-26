from copy import deepcopy
from pathlib import Path
from typing import Protocol
import os
import tempfile

import yaml

from opening_hours import opening_hours_to_time_windows
from datetime import date


def validate_destination(record):
    if not isinstance(record, dict):
        raise ValueError("Destination must be a mapping")
    for key in ("id", "name"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"Destination requires a nonempty {key}")
    for key in ("location", "website"):
        if key in record and (not isinstance(record[key], str) or not record[key].strip()):
            raise ValueError(f"Invalid destination {key}")
    if "opening_hours" in record:
        opening_hours_to_time_windows(record["opening_hours"], date(2026, 1, 1))
    if set(record) - {"id", "name", "location", "website", "opening_hours", "provider_ids", "tags", "provenance"}:
        raise ValueError("Unknown destination fields")
    return deepcopy(record)


class DestinationRepository(Protocol):
    def list(self) -> list[dict]: ...
    def get(self, destination_id: str) -> dict: ...
    def add(self, record: dict) -> None: ...


class YamlDestinationRepository:
    """Single-user storage; concurrent writers are not supported."""

    def __init__(self, path):
        self.path = Path(path)

    def list(self):
        if not self.path.exists():
            return []
        records = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("Destination repository must contain a list")
        records = [validate_destination(record) for record in records]
        if len({record["id"] for record in records}) != len(records):
            raise ValueError("Duplicate destination IDs")
        return records

    def get(self, destination_id):
        for record in self.list():
            if record["id"] == destination_id:
                return record
        raise ValueError(f"Unknown destination: {destination_id}")

    def add(self, record):
        record = validate_destination(record)
        records = self.list()
        if any(existing["id"] == record["id"] for existing in records):
            raise ValueError(f"Destination already exists: {record['id']}")
        records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                yaml.safe_dump(records, stream, allow_unicode=True, sort_keys=False)
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def resolve_plan(plan, repository: DestinationRepository):
    resolved = deepcopy(plan)
    stops = []
    for visit in resolved["stops"]:
        destination = repository.get(visit["destination_id"])
        if not destination.get("location"):
            raise ValueError(f"Destination {destination['id']} has no location")
        if set(visit) - {"destination_id", "service_minutes", "opening_hours"}:
            raise ValueError("Unknown visit fields")
        destination.update({key: value for key, value in visit.items() if key != "destination_id"})
        stops.append(destination)
    resolved["stops"] = stops
    return resolved
