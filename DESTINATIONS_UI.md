# Destination management

Open /destinations using the navigation bar. Search the repository by name, ID, address or tags. Create, edit and delete records. IDs are generated for new records and immutable after creation. Opening hours support weekday rules, optional week of month and specific dates. Provider IDs and provenance are editable JSON objects. The server validates all records.

Select records for export or export all. YAML preserves structured metadata; CSV is a simplified exchange format. Import accepts pasted YAML/CSV or a local file up to 2 MB. Review candidates, inspect details and select new records explicitly before committing. Conflicts, duplicates and invalid candidates cannot be committed; the server rechecks selected records. CSV opening hours and notes remain unverified provenance.

Deleting a destination may invalidate a plan; the UI warns before deletion. The application remains local and single-user. No new frontend dependencies. Plan editing, discovery and enrichment remain separate tasks.

Browser QA: create/edit/delete a disposable record, verify opening rules and metadata survive editing, search and export selected records, review mixed valid/invalid/duplicate candidates, commit only selected new records, reload and verify persistence. Check cancel and unsaved changes warning.
