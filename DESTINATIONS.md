# Destination storage and exchange

The YAML repository stores a list of records with required stable string id and name. Optional location is an address or existing lon,lat coordinate string; website, opening_hours, provider_ids, tags and provenance are optional. Missing location or opening hours prevents planning unless sufficient information is supplied. Route visits reference destination_id and specify service_minutes; opening_hours can be overridden for a visit.

The transitional CLI reads data/destinations.yaml and data/waypoints.yaml by default. The --destinations argument selects another repository file.

The DestinationRepository protocol isolates storage. YAML writes replace the file atomically, but concurrent writers are unsupported. SQLite and PostgreSQL adapters can implement the same interface; transaction boundaries and concurrent editing will be addressed before shared deployment.

Exchange services accept YAML lists or CSV with id and name columns and optional location, website, opening_hours, provider_ids, tags and provenance columns. Nested CSV fields contain JSON. Blank optional cells mean absent fields. CSV export prefixes formula-like text with an apostrophe; import reverses that convention. YAML is the preferred lossless exchange format; CSV converts date-like nested values to strings.

Review returns per-record statuses. Commit adds selected new records only and rechecks against current storage. Existing IDs, potential duplicates and conflicting records are not overwritten. Field-level merge and explicit duplicate resolution are deferred to the import review UI. IDs must currently be supplied by the source. Import size is limited to 2 MB; malformed documents can fail as a whole.

The repository is intended for trusted local use. Do not expose import or concurrent writes to untrusted users until API-level resource limits, schema validation and transactional safeguards are implemented.
