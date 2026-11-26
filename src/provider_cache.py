import hashlib
import json
import math
import sqlite3
import time
from contextlib import closing
from pathlib import Path


class ProviderCache:
    """Disposable SQLite cache, independent of destination persistence."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS entries "
                       "(key TEXT PRIMARY KEY, value TEXT NOT NULL, expires REAL NOT NULL)")

    def get(self, key):
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT value FROM entries WHERE key = ? AND expires > ?",
                             (key, time.time())).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, value, ttl):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM entries WHERE expires <= ?", (time.time(),))
            db.execute("INSERT OR REPLACE INTO entries VALUES (?, ?, ?)",
                       (key, json.dumps(value, allow_nan=False), time.time() + ttl))


def _key(*parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def _ttl(settings, key, default):
    value = settings.get(key, default)
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{key} must be a positive finite number")
    return value


def geocode_locations(geocoder, locations, config, cache):
    if geocoder is None:
        return locations
    settings = config.get("geocoder", {})
    if cache is None or settings.get("backend") != "nominatim":
        return geocoder.geocode(locations)
    ttl = _ttl(config["cache"], "geocode_ttl_seconds", 30 * 86400)
    namespace = ("geocode-v1", "nominatim", geocoder.base_url)
    resolved = {}
    missing = []
    for location in dict.fromkeys(locations):
        value = cache.get(_key(namespace, location))
        if value is None:
            missing.append(location)
        else:
            resolved[location] = value
    if missing:
        values = geocoder.geocode(missing)
        if len(values) != len(missing) or any(not isinstance(v, str) or not v for v in values):
            raise ValueError("Geocoder returned invalid locations")
        for location, value in zip(missing, values):
            cache.put(_key(namespace, location), value, ttl)
            resolved[location] = value
    return [resolved[location] for location in locations]


def travel_matrix(provider, locations, departure_ts, config, cache):
    # Commercial provider caching requires separate terms review.
    if cache is None or config["cost_provider"]["backend"] != "osrm":
        return provider.build_time_matrix(locations, departure_ts)
    settings = config["cache"]
    ttl = _ttl(settings, "travel_ttl_seconds", 7 * 86400)
    unique = sorted(set(locations))
    key = _key("matrix-v1", "osrm", provider.base_url, "driving",
               settings.get("dataset_revision", "default"), unique)
    matrix = cache.get(key)
    if matrix is None:
        requested = unique * 2 if len(unique) == 1 else unique
        matrix = provider.build_time_matrix(requested, departure_ts)
        if len(matrix) != len(requested) or any(len(row) != len(requested) for row in matrix):
            raise ValueError("Provider returned invalid matrix dimensions")
        if any(v is not None and (type(v) not in (int, float) or not math.isfinite(v) or v < 0)
               for row in matrix for v in row):
            raise ValueError("Provider returned invalid travel durations")
        if len(unique) == 1:
            matrix = [[matrix[0][1]]]
        cache.put(key, matrix, ttl)
    indices = {location: index for index, location in enumerate(unique)}
    return [[matrix[indices[a]][indices[b]] for b in locations] for a in locations]
