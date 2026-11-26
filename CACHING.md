# Provider caching

Caching is opt-in. Add the following to your local configuration:

```yaml
cache:
  enabled: true
  path: cache/providers.sqlite3
  geocode_ttl_seconds: 2592000
  travel_ttl_seconds: 604800
  dataset_revision: "1"
```

SQLite is included in Python; no additional service is needed. Docker mounts docker/git-ignored/cache at /app/cache. Cache files are disposable and contain resolved locations and travel durations; keep them private and out of Git. Stop the application before deleting the cache file. The cache is separate from destination persistence.

Nominatim results are cached per exact input and endpoint. Repeated locations are resolved once per cached request. OSRM caches a complete matrix per unique location set, endpoint, driving profile and dataset revision; reorder and expand it to match the requested nodes. OSRM ignores departure time, so its static matrix can be reused across dates. Change dataset_revision when rebuilding OSRM data or changing routing profile. Different location sets require a fresh matrix; partial matrix reuse is deferred. Google requests bypass persistent caching pending provider terms review. No provider errors are cached. Unreachable legs remain null.

Default TTLs are 30 days for geocoding and seven days for travel costs. Expired entries are ignored and removed on subsequent writes. No size cap, automatic dataset detection, cache administration UI or cross-process request coalescing yet. Cache storage errors propagate; disable caching or remove a damaged cache to recover. Enable only where provider terms permit.
