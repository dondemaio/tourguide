# Tourguide architecture

## Purpose

Tourguide is a locally deployable itinerary planner for reusable destinations, availability constraints and interchangeable routing services. The Web UI is the primary product interface for collaborative use; the REST API is the programmatic interface for automation and integrations. A dedicated application CLI is not a long-term product requirement.

## Current baseline

The Python application uses YAML configuration and waypoint input, OR-Tools for route optimization, and interchangeable geocoding, cost and rendering backends. Opening hours are expanded into date-specific time windows before solving. The Docker setup supports local OSRM routing; the Switzerland OSM extract can be downloaded with `./download-osm.sh`. This baseline is not a claim that all constraints or integrations have been fully tested.

## Target architecture

```mermaid
flowchart TD
    EXT[Scripts and external integrations] --> API[REST API]
    UI[Web UI] --> API[REST API]
    API --> APP
    APP --> LOC[Location repository]
    APP --> PRE[Planning preprocessing]
    PRE --> SOL[Route solver]
    APP --> BACK[Backend interfaces]
    BACK --> GEO[Geocoding]
    BACK --> COST[Travel costs]
    BACK --> RENDER[Rendering]
    BACK --> DISC[Destination discovery]
    BACK --> ENRICH[Location enrichment]
    LOC --> STORE[Persistence]
```

Keep domain logic independent of HTTP, CLI, persistence and external providers. Extract application services incrementally rather than rewriting the existing application. Proposed initial Web stack: FastAPI, plain HTML/CSS/JavaScript, Leaflet, and Docker Compose. Keep the existing CLI functional only as a transitional entry point until the Web UI covers its functionality. Do not invest in new CLI-specific features or maintain feature parity thereafter. Retire it once the Web UI is usable for the existing workflows. Retain independent application services and infrastructure/administration scripts such as the OSM downloader. Use a configurable map tile provider with appropriate attribution and usage compliance.

## Data and planning

- Keep application configuration, reusable location data and individual route definitions separate.
- A reusable location has a stable ID, name, address, optional coordinates, website, recurring opening hours, exceptions, tags and provenance.
- A route references locations or defines inline destinations; visit duration, priority and overrides belong to the planning request.
- Start and end retain absolute datetime time windows. Expand recurring opening hours for the relevant planning dates before solving, using explicit local timezone semantics and clipping to the planning horizon. Handle closed days, multiple intervals, exceptional dates and visits that must finish before closing.
- Normalize solver inputs into indexed nodes, integer travel costs, service durations and time windows. Alternative windows for one mandatory visit must enforce exactly one visit. Keep optional visits explicitly distinct.
- Return structured results with visit order, arrival/departure times, waiting, service, travel duration, distance where available, and skipped visits. Distinguish infeasibility from timeouts and provider errors.
- Use a canonical coordinate representation and convert to provider-specific ordering at backend boundaries. Cache geocoding and travel costs with provider/profile-aware keys.

## Destination discovery

Provide a separate discovery interface accepting a search term and geographic area. Initial area types are bounding box and radius; later support polygons and administrative regions. The Web UI can use the visible map bounds. Candidate results may include name, address, coordinates, opening hours, website, provider identifiers and provenance. Review and deduplicate candidates before importing them into the location repository.

Potential providers include Google Places, Overpass and a separately indexed local OSM extract. OSRM is a routing service, not a discovery index. Respect provider terms, attribution, storage restrictions, rate limits and result caps. Report incomplete coverage and missing fields rather than claiming exhaustive results. Provider selection and indexing design remain open.

## Destination import and export

Use a shared, source-independent import service for manually collected destinations, uploaded files, pasted structured text and discovery candidates. Initially support YAML and CSV, with JSON and extraction from unstructured chats or emails as later extensions. Keep format parsing separate from normalization, validation, duplicate detection and persistence.

Accept incomplete but identifiable destinations; missing attributes can be enriched later. Preview new records, identical duplicates, missing-field supplements, potential duplicates, conflicting values and invalid records. Allow selective approval and report record-level errors without blocking unrelated valid records. Do not silently overwrite existing values. Preserve provenance where available and assign stable IDs to new records.

Export individual destinations, selected groups or the entire database. YAML exports must support lossless round trips, including nested opening hours, exceptions and provenance. Document CSV field mappings and any format limitations. Provide application service support first, followed by Web UI file upload, pasted YAML/CSV, import review and export downloads. Automated discovery must reuse the same import workflow.

## Website enrichment and verification

An optional website on a location is an input to enrichment (missing fields) and verification (existing fields). A dedicated backend may extract structured metadata such as JSON-LD, then relevant contact/opening-hours pages. More complex HTML, PDFs or LLM-assisted interpretation can follow. Return field-level proposed changes with source URLs, retrieval dates and uncertainty; never silently overwrite maintained records. Distinguish unreachable sources from confirmed closure. Limit requests, respect site policies, and protect server-side fetching against private-network access, unsafe redirects and unbounded responses. Treat retrieved content as untrusted data.

## Collaborative use

Plan for a shared destination repository, concurrent editing without lost updates, personal and shared route plans, contributor identity and access control, change history and import provenance. These are future requirements, not prerequisites for the initial Web UI. Before exposing the application to untrusted users, establish appropriate authentication, authorization and deployment protections.

YAML is an initial persistence option; evaluate SQLite or another transactional store as collaborative requirements mature. Keep persistence behind repository interfaces and YAML/CSV exchange formats independent of internal storage. No specific authentication or database solution is selected yet.

## Deployment and quality

Prefer local operation without mandatory commercial APIs. Keep credentials and private data out of Git. Maintain unit tests for domain logic and solver constraints, mocked provider tests and optional live integration tests. Keep UI usable while features are incomplete, with clear errors and limitations. Add features vertically across application, API and UI once the initial Web product exists.

## Open decisions

Exact location schema, timezone/exception rules, optimization objectives, persistence concurrency, discovery provider choice, and frontend details will be settled in their respective PRs. YAML is the initial storage proposal, not a permanent restriction.
