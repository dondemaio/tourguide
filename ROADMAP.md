# Tourguide roadmap

This living document describes delivery order and product milestones. See [ARCHITECTURE.md](ARCHITECTURE.md) for requirements and design principles. Future PR numbers and version labels are provisional, not release commitments.

## Delivery priorities

Move through the foundational work quickly, without overengineering. The Web UI is the primary product interface; the REST API supports automation. Keep the existing CLI only as a transitional entry point, without new CLI-specific features.

Reliable solver behavior, reusable destinations, structured results and callable application logic are the essential prerequisites for the initial Web UI. If caching, optional visits or date-range optimization delay it materially, defer those features. Destination discovery is the next major product priority after the usable Web application.

## Near-term PR sequence

| PR | Scope |
|---|---|
| #1 | Switzerland OSM download script (merged; download tested by user) |
| #2 | Architecture and roadmap |
| #3 | Test infrastructure and baseline tests |
| #4 | Solver correctness, mandatory visits, disjunctions and error handling |
| #5 | Opening-hours processing, validation, clipping and exceptions |
| #6 | Reusable destination repository, route references, YAML/CSV import and export services |
| #7 | Structured route results, schedule and travel metrics |
| #8 | Geocoding and travel cost caching |
| #9 | Optional destinations and visit priorities |
| #10 | Date-range optimization (best single day) |
| #11 | Application service layer and REST API; extract shared logic throughout earlier PRs |
| #12 | Initial Web UI and interactive route map |
| #13 | Destination management UI, file upload, pasted YAML/CSV, import review and export |
| #14 | Interactive route planning UI; complete existing workflows and retire transitional CLI when covered |
| #15 | Destination discovery interface and first backend |
| #16 | Geographic discovery UI, candidate review and shared import workflow |
| #17 | Website-based enrichment and verification, including incomplete imported records |
| #18 | Field-level change review UI |
| #19+ | Advanced planning, additional providers and collaborative features; order to be decided |

## Product milestones

| Milestone | Completion criteria |
|---|---|
| v0.1 — Application foundation | Validated inputs, reusable destinations, import/export services, tested solver constraints and structured results. |
| v0.2 — Usable Web application | Manage, import and export destinations; define trips; calculate and inspect routes on a map and in an itinerary. Docker deployment and REST API available. Retire the CLI once its workflows are covered. |
| v0.3 — Destination discovery | Search by term and geographic area, review available candidate metadata and coverage limitations, deduplicate and import selected records. |
| v0.4 — Enrichment and verification | Retrieve missing information and detect changes from destination websites; review source-backed proposals before applying them. |
| v0.5 — Advanced planning | Distribute visits across independent day trips, then support continuous multi-day trips with overnight stays. |

The first Web deployment may be restricted to a trusted environment. Shared access requires appropriate security and safe persistence before it is enabled; this is a deployment gate, not a reason to postpone the initial UI. Full collaborative features have no fixed milestone yet.

## Additional backlog

Items below extend the near-term scope; their order is not yet agreed.

- Planning: fixed appointments, alternative destinations, precedence, travel/distance/waiting limits, configurable objectives and route comparison.
- Destination exchange: JSON and extraction from unstructured chats or emails.
- Discovery: additional providers, polygon and administrative-region searches, optional local OSM indexing.
- Enrichment: complex documents, optional LLM extraction, periodic verification and change reports.
- Visualization: standalone HTML maps, GeoJSON, GPX and printable itineraries.
- Collaboration: personal/shared plans, contributor identity, access control, change history and concurrent editing; evaluate transactional persistence as needed.
- Quality and operations: expanded integration and UI tests, reproducibility, backup/recovery and deployment documentation.

## Development process

Discuss scope, inspect current implementation, implement on a dedicated branch, test and open a PR targeting `develop`. Review before merging. Keep PRs focused, record limitations and decisions, and update this roadmap as milestones and priorities change. After the first Web product, prefer vertical feature delivery across application services, API and UI rather than long backend-only phases.
