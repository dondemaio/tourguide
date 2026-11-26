# Destination storage and exchange

The YAML repository stores a list of records with required stable string id and name. Optional location is an address or existing lon,lat coordinate string; website, opening_hours, provider_ids, tags and provenance are optional. Missing location or opening hours prevents planning unless sufficient information is supplied. Route visits reference destination_id and specify service_minutes; opening_hours can be overridden for a visit.

The transitional CLI reads data/destinations.yaml and data/waypoints.yaml by default. The --destinations argument selects another repository file.

The DestinationRepository protocol isolates storage. YAML writes replace the file atomically, but concurrent writers are unsupported. SQLite and PostgreSQL adapters can implement the same interface; transaction boundaries and concurrent editing will be addressed before shared deployment.

YAML exchange accepts structured lists with stable IDs and preserves nested fields. CSV is a human-readable candidate collection format, not a lossless exchange format. Supported headers (case-insensitive) are Name, Address, Website, Opening hours and Notes; any subset is allowed, but each row needs at least a name, address or website. Comma and semicolon delimiters and UTF-8 BOM are supported. IDs are generated internally. If name is absent, address or website is used as a provisional display name. Raw submitted fields are retained in provenance.candidate; free-text hours are not interpreted as verified opening_hours. CSV exports readable hours and notes, omit internal IDs and nested metadata, and prefix formula-like cells with an apostrophe for spreadsheet safety.

Review returns per-record statuses. Commit adds selected new records only and rechecks against current storage. Existing IDs, potential duplicates and conflicting records are not overwritten. Field-level merge and explicit duplicate resolution are deferred to the import review UI. YAML requires IDs; CSV generates them. A persistent candidate inbox, direct XLSX imports, contribution forms and shared links are deferred (see ROADMAP.md). Import size is limited to 2 MB; malformed documents can fail as a whole.

Docker currently mounts individual files for read-only planning; before enabling writes, mount the entire data directory to allow atomic replacement.

The repository is intended for trusted local use. Do not expose import or concurrent writes to untrusted users until API-level resource limits, schema validation and transactional safeguards are implemented.
