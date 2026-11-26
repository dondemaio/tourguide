import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from requests.exceptions import RequestException

from application import Application
from destination_exchange import ImportCandidate
from solver import NoRouteFoundError


logger = logging.getLogger(__name__)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Endpoint(StrictModel):
    id: str | None = None
    name: str | None = None
    location: str = Field(min_length=1)
    time_window: list[str] = Field(min_length=2, max_length=2)
    service_minutes: int | float = 0


class Visit(StrictModel):
    destination_id: str
    service_minutes: int | float = 0
    opening_hours: list[dict] | None = None
    required: bool = True
    priority: int | None = None


class Plan(StrictModel):
    timezone: str
    start: Endpoint
    end: Endpoint
    stops: list[Visit]


class ImportRequest(StrictModel):
    content: str = Field(max_length=2_000_000)
    format: Literal["yaml", "csv"]


class Candidate(StrictModel):
    index: int
    status: str
    record: dict | None
    message: str = ""


class CommitRequest(StrictModel):
    candidates: list[Candidate]
    selected_indices: list[int]


class ExportRequest(StrictModel):
    format: Literal["yaml", "csv"]
    ids: list[str] | None = None


def create_app(application=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.application = application or Application.from_files(
            os.getenv("TOURGUIDE_CONFIG", "config.yaml"),
            os.getenv("TOURGUIDE_DESTINATIONS", "data/destinations.yaml"),
            os.getenv("TOURGUIDE_PLAN", "data/waypoints.yaml"))
        yield

    app = FastAPI(title="Tourguide", lifespan=lifespan)
    web = Path(__file__).parent / "web"
    app.mount("/static", StaticFiles(directory=web), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(web / "index.html")

    def service(request: Request):
        return request.app.state.application

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(NoRouteFoundError)
    async def no_route(request, exc):
        return JSONResponse(status_code=409, content={
            "detail": str(exc), "solver_status": exc.status})

    @app.exception_handler(RequestException)
    @app.exception_handler(RuntimeError)
    async def provider_error(request, exc):
        # Provider exceptions can contain credentials or private addresses.
        logger.warning("Route provider or application operation failed: %s", type(exc).__name__)
        return JSONResponse(status_code=502, content={"detail": "Route provider or application operation failed"})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/plans/default")
    def default_plan(request: Request):
        return service(request).default_plan()

    @app.post("/api/routes")
    def route(plan: Plan, request: Request):
        return service(request).calculate(plan.model_dump(exclude_none=True, exclude_unset=True))

    @app.get("/api/destinations")
    def destinations(request: Request):
        return service(request).list_destinations()

    @app.get("/api/destinations/{key}")
    def destination(key: str, request: Request):
        try:
            return service(request).get_destination(key)
        except ValueError as exc:
            raise HTTPException(404, "Destination not found") from exc

    @app.post("/api/destinations", status_code=201)
    def add(record: dict, request: Request):
        service(request).add_destination(record)
        return record

    @app.put("/api/destinations/{key}")
    def replace(key: str, record: dict, request: Request):
        service(request).replace_destination(key, record)
        return record

    @app.delete("/api/destinations/{key}", status_code=204)
    def delete(key: str, request: Request):
        service(request).delete_destination(key)
        return Response(status_code=204)

    @app.post("/api/import/review")
    def review(body: ImportRequest, request: Request):
        return service(request).review(body.content, body.format)

    @app.post("/api/import/commit")
    def commit(body: CommitRequest, request: Request):
        candidates = [ImportCandidate(**candidate.model_dump()) for candidate in body.candidates]
        return service(request).commit(candidates, body.selected_indices)

    @app.post("/api/export")
    def export(body: ExportRequest, request: Request):
        content = service(request).export(body.format, body.ids)
        return PlainTextResponse(content, media_type="text/csv" if body.format == "csv" else "application/yaml")

    return app


app = create_app()
