# REST API

Run from the repository root:

```sh
docker compose -f docker/tourguide.yml up --build -d
```

Open http://localhost:8000/docs for interactive OpenAPI documentation.

For development:

```sh
docker compose -f docker/tourguide.yml -f docker/tourguide-dev.yml up --build -d
```

The default image contains its source. The development override mounts src and enables reload. Data, configuration and cache remain mounted. The CLI remains available with:

```sh
docker compose -f docker/tourguide.yml exec tourguide python src/main.py
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | Process health |
| GET | /api/plans/default | Existing YAML plan |
| POST | /api/routes | Calculate and render submitted plan |
| GET | /api/destinations | List destinations |
| GET | /api/destinations/{key} | Retrieve destination |
| POST | /api/destinations | Create destination |
| PUT | /api/destinations/{key} | Replace destination (ID unchanged) |
| DELETE | /api/destinations/{key} | Delete destination |
| POST | /api/import/review | Review YAML or CSV content |
| POST | /api/import/commit | Commit selected reviewed candidates |
| POST | /api/export | Export YAML or CSV, optionally selected IDs |

Route responses contain route and rendering; rendering is provider-specific. The existing plan schema is used. Import review accepts content and format; commit accepts candidates and selected_indices. Commit revalidates against current repository contents. Candidate payloads are not authorization tokens.

## Deployment limitations

Trusted local single-user use only. No authentication, authorization, cross-process write locking, request quotas or saved-plan CRUD yet. Run one server worker; writes through one application instance are serialized, but external file edits and separate CLI writers are not coordinated. Deleting destinations can invalidate existing plans. Do not expose this API publicly. The host API port is bound to loopback. Provider configuration and credentials are not exposed by an endpoint. Configuration is loaded at startup; restart after changing it. Provider failures are returned without raw upstream exception details.

The Web UI and saved plans are subsequent roadmap tasks.
