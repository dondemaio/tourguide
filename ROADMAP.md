# Tourguide roadmap

This is a living plan. Deliver small reviewable PRs targeting `develop`, keep the application usable, and update this document as scope changes. PR numbers below are provisional.

## Near-term sequence

| PR | Scope |
|---|---|
| #1 | Switzerland OSM download script (merged; download tested by user) |
| #2 | Architecture and roadmap |
| #3 | Test infrastructure and baseline tests |
| #4 | Solver correctness, mandatory visits, disjunctions and error handling |
| #5 | Opening-hours processing, validation, clipping and exceptions |
| #6 | Reusable location database and route references |
| #7 | Structured route results, schedule and travel metrics |
| #8 | Geocoding and travel cost caching |
| #9 | Optional destinations and visit priorities |
| #10 | Date-range optimization (best single day) |
| #11 | Application service layer and REST API |
| #12 | Initial Web UI and interactive route map |
| #13 | Location database management UI |
| #14 | Interactive route planning UI |
| #15 | Destination discovery interface and first backend |
| #16 | Geographic discovery UI, candidate review and import |
| #17 | Website-based location enrichment |
| #18 | Verification and field-level change review UI |
| #19+ | Advanced optimization, additional backends and multi-day trips |

Move through #2–10 quickly without overengineering. Prepare the shared application layer throughout. If caching, optional visits or date-range planning delay the first Web UI materially, defer them rather than blocking a usable product. The essential UI prerequisites are reliable solver behavior, reusable locations, structured results and callable application logic. Discovery is an early product priority, not a distant optional extension.

## Product milestones

- **v0.1 — Reliable CLI:** validated inputs, reusable location data, solver correctness and structured results.
- **v0.2 — Usable Web application:** select and edit locations, define trips, calculate routes, inspect itinerary and map. Retain CLI and Docker deployment.
- **v0.3 — Destination discovery:** search by term within a geographic area; show candidates with available metadata, review duplicates and import selected entries. Start with bounding box/radius and map viewport; expand area types later. Show coverage and provider limitations.
- **v0.4 — Location enrichment and verification:** visit optional official websites to find missing addresses, hours and other attributes or detect changes. Present source-backed suggestions for approval; retain provenance and verification dates.
- **v0.5 — Advanced planning:** distribute visits across independent day trips, then continuous multi-day trips with overnight stays.

## Feature backlog

- Planning: fixed appointments, visit completion constraints, alternative destinations, precedence, travel/distance/waiting limits, configurable objectives and priorities.
- Location data: weekly hours, special recurring hours, date-specific exceptions, tags, coordinates, inline destinations and per-trip overrides.
- Visualization: exact route geometry where available, arrival/departure schedule, waiting and service times, HTML maps, GeoJSON and GPX exports, comparison of alternatives.
- Discovery: interchangeable providers, geographic filtering, deduplication, provenance, incomplete coverage reporting, optional local OSM indexing.
- Enrichment: structured website metadata first, contact pages, more complex documents and optional LLM extraction later; no automatic overwrites.
- Quality: validation, diagnostics, automated tests, provider isolation, reproducibility, caching and documentation.

## Development process

Discuss scope, inspect current implementation, implement on a dedicated branch, test, open a PR to `develop`, and review before merging. Keep PRs focused; document limitations and decisions. Revisit the roadmap after each milestone. Version labels and future PR boundaries are planning proposals rather than release commitments.
