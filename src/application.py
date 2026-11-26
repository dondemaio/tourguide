from copy import deepcopy
from pathlib import Path
from threading import RLock

import yaml

from destination_exchange import review_import, commit_import, export_destinations
from destinations import YamlDestinationRepository
from route_service import calculate_route, render_route
from requests.exceptions import RequestException


class Application:
    """Single-process application boundary; serialize repository mutations."""

    def __init__(self, repository, config, plan_path):
        self.repository = repository
        self.config = config
        self.plan_path = Path(plan_path)
        self.lock = RLock()

    @classmethod
    def from_files(cls, config_path, destinations_path, plan_path):
        with open(config_path, encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        return cls(YamlDestinationRepository(destinations_path), config, plan_path)

    def default_plan(self):
        with self.plan_path.open(encoding="utf-8") as stream:
            return yaml.safe_load(stream)

    def calculate(self, plan):
        result = calculate_route(plan, self.repository, self.config)
        rendering = render_route(result, self.config)
        geometry = None
        warning = None
        if self.config.get("cost_provider", {}).get("backend") == "osrm":
            if self.config.get("route_renderer", {}).get("backend") == "geojson":
                geometry = rendering
            else:
                config = deepcopy(self.config)
                config["route_renderer"] = {"backend": "geojson"}
                try:
                    geometry = render_route(result, config)
                except (RequestException, RuntimeError, ValueError):
                    warning = "Road geometry unavailable; itinerary remains valid."
        else:
            warning = "Road geometry is not available for this cost provider."
        return {"route": result, "rendering": rendering,
                "geometry": geometry, "geometry_warning": warning}

    def list_destinations(self):
        return self.repository.list()

    def get_destination(self, key):
        return self.repository.get(key)

    def add_destination(self, record):
        with self.lock:
            self.repository.add(record)

    def replace_destination(self, key, record):
        with self.lock:
            self.repository.replace(key, record)

    def delete_destination(self, key):
        with self.lock:
            self.repository.delete(key)

    def review(self, content, format):
        return review_import(content, format, self.repository)

    def commit(self, candidates, indices):
        with self.lock:
            return commit_import(candidates, indices, self.repository)

    def export(self, format, ids):
        return export_destinations(self.repository, format, ids)
