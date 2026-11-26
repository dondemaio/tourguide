from copy import deepcopy
from pathlib import Path
from typing import Protocol
import os
import re
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
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", record["id"]):
        raise ValueError("Destination ID must be URL-safe (letters, digits, underscores, hyphens and non-leading dots)")
    for key in ("location", "website"):
        if key in record and (not isinstance(record[key], str) or not record[key].strip()):
            raise ValueError(f"Invalid destination {key}")
    if "opening_hours" in record:
        opening_hours_to_time_windows(record["opening_hours"], date(2026, 1, 1))
    if set(record) - {"id", "name", "location", "website", "opening_hours", "provider_ids", "tags", "provenance"}:
        raise ValueError("Unknown destination fields")
    if "provider_ids" in record and (not isinstance(record["provider_ids"], dict)
            or any(not isinstance(k, str) or not isinstance(v, str)
                   for k, v in record["provider_ids"].items())):
        raise ValueError("provider_ids must map strings to strings")
    if "tags" in record and (not isinstance(record["tags"], list)
            or any(not isinstance(tag, str) for tag in record["tags"])):
        raise ValueError("tags must be a list of strings")
    if "provenance" in record:
        provenance = record["provenance"]
        if not isinstance(provenance, dict):
            raise ValueError("provenance must be a mapping")
        candidate = provenance.get("candidate", {})
        if not isinstance(candidate, dict) or any(not isinstance(v, str) for v in candidate.values()):
            raise ValueError("candidate provenance must contain string values")
    return deepcopy(record)


class DestinationRepository(Protocol):
    def list(self) -> list[dict]: ...
    def get(self, destination_id: str) -> dict: ...
    def add(self, record: dict) -> None: ...
    def replace(self, destination_id: str, record: dict) -> None: ...
    def delete(self, destination_id: str) -> None: ...


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
        self._write(records)

    def replace(self, destination_id, record):
        record = validate_destination(record)
        if record["id"] != destination_id:
            raise ValueError("Destination ID cannot change")
        records = self.list()
        for index, existing in enumerate(records):
            if existing["id"] == destination_id:
                records[index] = record
                self._write(records)
                return
        raise ValueError(f"Unknown destination: {destination_id}")

    def delete(self, destination_id):
        records = self.list()
        remaining = [record for record in records if record["id"] != destination_id]
        if len(remaining) == len(records):
            raise ValueError(f"Unknown destination: {destination_id}")
        self._write(remaining)

    def _write(self, records):
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
    if not isinstance(plan, dict) or not isinstance(plan.get("stops"), list):
        raise ValueError("Plan requires a stops list")
    resolved = deepcopy(plan)
    stops = []
    records = {record["id"]: record for record in repository.list()}
    for visit in resolved["stops"]:
        if not isinstance(visit, dict) or not isinstance(visit.get("destination_id"), str):
            raise ValueError("Visit requires a destination_id")
        key = visit["destination_id"]
        if key not in records:
            raise ValueError(f"Unknown destination: {key}")
        destination = deepcopy(records[key])
        if not destination.get("location"):
            raise ValueError(f"Destination {destination['id']} has no location")
        if set(visit) - {"destination_id", "service_minutes", "opening_hours", "required", "priority"}:
            raise ValueError("Unknown visit fields")
        destination.update({key: value for key, value in visit.items() if key != "destination_id"})
        stops.append(destination)
    resolved["stops"] = stops
    return resolved
