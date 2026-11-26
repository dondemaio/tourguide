import csv
import io
from uuid import uuid4
from threading import Lock
from dataclasses import dataclass

import yaml

from destinations import validate_destination


FIELDS = ("name", "address", "website", "opening hours", "notes")
_CSV_LOCK = Lock()
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
    return parse_csv_candidates(text)


def parse_csv_candidates(text):
    """Return candidate records, preserving unverified hours and notes."""
    if len(text.encode("utf-8")) > MAX_INPUT:
        raise ValueError("Import exceeds size limit")
    text = text.removeprefix("\ufeff")
    with _CSV_LOCK:
        previous = csv.field_size_limit(MAX_INPUT)
        try:
            delimiter = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;").delimiter if text.strip() and any(ch in text.splitlines()[0] for ch in ",;") else ","
            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter, strict=True)
            reader.fieldnames = [key.strip().casefold() for key in (reader.fieldnames or [])]
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or set(reader.fieldnames) - set(FIELDS):
                raise ValueError("Invalid CSV columns")
            records = []
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    records.append(ValueError("CSV row has incorrect number of fields"))
                    continue
                values = {key: value.strip() for key, value in row.items() if value.strip()}
                if not any(values.get(key) for key in ("name", "address", "website")):
                    records.append(ValueError("Candidate needs a name, address or website"))
                    continue
                record = {"id": str(uuid4()), "name": values.get("name") or values.get("address") or values["website"]}
                if values.get("address"):
                    record["location"] = values["address"]
                if values.get("website"):
                    record["website"] = values["website"]
                record["provenance"] = {"candidate": values}
                records.append(record)
            return records
        except csv.Error as exc:
            raise ValueError(f"Invalid CSV: {exc}") from exc
        finally:
            csv.field_size_limit(previous)


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
        provenance = record.get("provenance")
        candidate = provenance.get("candidate", {}) if isinstance(provenance, dict) else {}
        hours = candidate.get("opening hours", "")
        if "opening_hours" in record:
            hours = "; ".join(
                f"{entry.get('date', ', '.join(entry.get('days', [])))}"
                + (f" (week {entry['week_of_month']})" if "week_of_month" in entry else "")
                + ": " + (", ".join(entry["times"]) or "Closed")
                for entry in record["opening_hours"]
            )
        row = {"name": record["name"], "address": record.get("location", ""),
               "website": record.get("website", ""), "opening hours": hours,
               "notes": candidate.get("notes", "")}
        writer.writerow({key: "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else value
                         for key, value in row.items()})
    return stream.getvalue()
