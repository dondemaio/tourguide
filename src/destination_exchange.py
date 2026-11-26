import csv
import io
import json
from dataclasses import dataclass

import yaml

from destinations import validate_destination


FIELDS = ("id", "name", "location", "website", "opening_hours", "provider_ids", "tags", "provenance")
NESTED = {"opening_hours", "provider_ids", "tags", "provenance"}
MAX_INPUT = 2_000_000


@dataclass
class ImportCandidate:
    index: int
    status: str
    record: dict | None
    message: str = ""


def _parse(text, format):
    if len(text.encode("utf-8")) > MAX_INPUT:
        raise ValueError("Import exceeds size limit")
    if format == "yaml":
        records = yaml.safe_load(text)
        if not isinstance(records, list):
            raise ValueError("YAML import must contain a list")
        return records
    if format != "csv":
        raise ValueError("Unsupported exchange format")
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if not reader.fieldnames or not {"id", "name"} <= set(reader.fieldnames):
        raise ValueError("CSV requires id and name columns")
    if len(set(reader.fieldnames)) != len(reader.fieldnames) or set(reader.fieldnames) - set(FIELDS):
        raise ValueError("Invalid CSV columns")
    records = []
    for row in reader:
        try:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("CSV row has incorrect number of fields")
            record = {}
            for key, value in row.items():
                if not value:
                    continue
                if key in NESTED:
                    record[key] = json.loads(value)
                else:
                    # Reverse spreadsheet-safe escaping from our exporter.
                    record[key] = value[1:] if value.startswith("'") and value[1:2] in ("=", "+", "-", "@", "\t", "\r", "\n", "'") else value
            records.append(record)
        except ValueError as exc:
            records.append(exc)
    return records


def review_import(text, format, repository):
    existing = {record["id"]: record for record in repository.list()}
    seen = set()
    candidates = []
    for index, raw in enumerate(_parse(text, format)):
        try:
            if isinstance(raw, Exception):
                raise raw
            record = validate_destination(raw)
            key = record["id"]
            if key in seen:
                status = "duplicate_in_import"
            elif key in existing:
                status = "identical" if record == existing[key] else "conflict"
            elif any(record["name"].strip().casefold() == other["name"].strip().casefold()
                     or (record.get("location") and record["location"] == other.get("location"))
                     for other in existing.values()):
                status = "potential_duplicate"
            else:
                status = "new"
            seen.add(key)
            if status == "new":
                existing[key] = record
            candidates.append(ImportCandidate(index, status, record))
        except (ValueError, TypeError) as exc:
            candidates.append(ImportCandidate(index, "invalid", None, str(exc)))
    return candidates


def commit_import(candidates, selected_indices, repository):
    """Add selected new records only; never overwrite existing records."""
    selected = set(selected_indices)
    results = []
    for candidate in candidates:
        if candidate.index not in selected:
            continue
        if candidate.status != "new":
            results.append(ImportCandidate(candidate.index, "rejected", candidate.record, "Not a new record"))
            continue
        try:
            current = review_import(yaml.safe_dump([candidate.record]), "yaml", repository)[0]
            if current.status != "new":
                raise ValueError(f"Import candidate is now {current.status}")
            repository.add(candidate.record)
            results.append(ImportCandidate(candidate.index, "added", candidate.record))
        except ValueError as exc:
            results.append(ImportCandidate(candidate.index, "rejected", candidate.record, str(exc)))
    return results


def export_destinations(repository, format, ids=None):
    records = repository.list() if ids is None else [repository.get(key) for key in ids]
    if format == "yaml":
        return yaml.safe_dump(records, allow_unicode=True, sort_keys=False)
    if format != "csv":
        raise ValueError("Unsupported exchange format")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS)
    writer.writeheader()
    for record in records:
        row = {}
        for key, value in record.items():
            if key in NESTED:
                row[key] = json.dumps(value, ensure_ascii=False, default=str)
            else:
                row[key] = "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r", "\n", "'")) else value
        writer.writerow(row)
    return stream.getvalue()
