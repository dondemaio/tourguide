# Destination catalog

Open /destinations from the navigation bar. The full-width catalog loads existing records immediately and supports search by name, address, ID and tags. Refresh retries loading. New destination and pencil icons open the same right-hand modal drawer; trash icons delete after confirmation. Search remains intact when the drawer closes. Escape and Cancel confirm discarding unsaved edits. Opening hours support weekdays, week of month and specific dates. Advanced metadata uses JSON objects. IDs are immutable after creation.

Import/export UI is postponed; existing REST endpoints remain available. No new dependencies. The app remains local and single-user. Deletion can invalidate plans and warns accordingly.

QA: verify initial catalog loading, including HTTP access from another device; search, create/edit/delete a disposable record, verify metadata and opening hours persist, check Escape/Cancel and reload persistence. Verify error reporting and Refresh after a failed list request.
