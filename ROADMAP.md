# Tourguide roadmap

This living document describes delivery order and product milestones. See [ARCHITECTURE.md](ARCHITECTURE.md) for requirements and design principles. Future PR numbers and version labels are provisional, not release commitments.

## Delivery priorities

Move through the foundational work quickly, without overengineering. The Web UI is the primary product interface; the REST API supports automation. Keep the existing CLI only as a transitional entry point, without new CLI-specific features.

Reliable solver behavior, reusable destinations, structured results and callable application logic are the essential prerequisites for the initial route-planning UI. Import/export must be available by the usable Web milestone, but need not block the first route-map UI. If caching, optional visits or date-range optimization delay it materially, defer those features. Destination discovery is the next major product priority after the usable Web application.

## Near-term PR sequence

| PR | Scope |
|---|---|
| #1 | Switzerland OSM download script (merged; download tested by user) |
| #2 | Architecture and roadmap |
| #3 | Test infrastructure and baseline tests |
| #4 | Solver correctness, mandatory visits, disjunctions, unreachable legs and error handling |
| #5 | Opening-hours processing, validation, clipping and exceptions |
| #6 | Reusable destination repository, route references, lossless YAML exchange and simple CSV candidate collection |
| #7 | Structured route results, destination identities, schedule and travel metrics |
| #8 | Geocoding and travel cost caching |
| #9 | Optional destinations and visit priorities |
| #10 | Date-range optimization (best single day) |
| #11 | Complete initial application service layer and REST API for planning and destination management; extract shared logic throughout earlier PRs; mount the data directory for atomic writes (not individual destination files) |
| #12 | Initial Web UI: calculate a route from existing inputs, display itinerary and interactive map with named markers |
| #13 | Destination management UI, file upload, pasted YAML/CSV, candidate inbox and import review, overview and lossless export |
| #14 | Interactive route definition, saved plans and calculation; complete existing workflows and retire transitional CLI when covered |
| #15 | Destination discovery interface and first backend |
| #16 | Geographic discovery UI, candidate review and shared import workflow |
| #17 | Website-based enrichment and verification, including incomplete imported records |
| #18 | Field-level change review UI |
| #19+ | Advanced planning, additional providers and collaborative features; order to be decided |

## Product milestones

| Milestone | Completion criteria |
|---|---|
| v0.1 — Application foundation | Validated inputs, reusable destinations, tested solver constraints and structured results; import/export services targeted here but may finish before v0.2. |
| v0.2 — Usable Web application | Manage, import and export destinations; define trips; calculate and inspect routes on a map and in an itinerary. Docker deployment and REST API available. Retire the CLI once its workflows are covered. |
| v0.3 — Destination discovery | Search by term and geographic area, review available candidate metadata and coverage limitations, deduplicate and import selected records. |
| v0.4 — Enrichment and verification | Retrieve missing information and detect changes from destination websites; review source-backed proposals before applying them. |
| v0.5 — Advanced planning | Complete any deferred date-range optimization; distribute visits across independent day trips, then support continuous multi-day trips with overnight stays. |

The first Web deployment may be single-user in a trusted environment. Shared access requires appropriate security and safe persistence before it is enabled; this is a deployment gate, not a reason to postpone the initial UI. Full collaborative features have no fixed milestone yet.

If any near-term feature is deferred to accelerate the Web UI, keep it explicitly on the roadmap and reschedule it rather than silently dropping it. Shared deployment safeguards must be implemented before collaborative access, regardless of PR numbering.

## Additional backlog

Items below extend the near-term scope; their order is not yet agreed.

- Low priority: overnight opening hours and flexible visit durations: preferred and minimum duration, shortening penalties and configurable trade-offs with travel and waiting time.
- Rendering: preserve destination names in Google Maps links using provider place IDs where available or name/address matching; preserve named features in exports.
- Planning: fixed appointments, alternative destinations, precedence, travel/distance/waiting limits, configurable objectives and route comparison.
- Destination collection: downloadable simple spreadsheet template, direct XLSX imports, shared Excel/Google Sheets workflows, map URL submissions, pasted unstructured chats/emails, and JSON programmatic exchange.
- Candidate inbox: persist incomplete and unverified submissions separately, track source/contributor, normalize and enrich before approval, preserve raw information and review state; common workflow for discovery and manual submissions.
- Collaboration: mobile-friendly contribution form, invitation-based shared collections, restricted contributor access and review ownership; security and transactional persistence before shared deployment.
- Discovery: additional providers, polygon and administrative-region searches, optional local OSM indexing.
- Enrichment: complex documents, optional LLM extraction, periodic verification and change reports.
- Visualization: standalone HTML maps, GeoJSON, GPX and printable itineraries.
- Collaboration: personal/shared plans, contributor identity, access control, change history and concurrent editing; evaluate transactional persistence as needed.
- Quality and operations: expanded integration and UI tests, reproducibility, backup/recovery and deployment documentation. Basic tests and deployment instructions accompany the corresponding near-term features.

## Development process

Discuss scope, inspect current implementation, implement on a dedicated branch, test and open a PR targeting `develop`. Review before merging. No backwards compatibility or migration layers are required during personal-project development; update schemas and examples directly. Keep PRs focused, record limitations and decisions, and update this roadmap as milestones and priorities change. After the first Web product, prefer vertical feature delivery across application services, API and UI rather than long backend-only phases.
