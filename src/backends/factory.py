from backends.google.cost import GoogleCostProvider
from backends.google.render import GoogleRouteRenderer
from backends.google.web.render import GoogleMapsURLRenderer
from backends.nominatim.geocode import NominatimGeocoder
from backends.osrm.cost import OSRMCostProvider
from backends.osrm.render import OSRMRouteRenderer


def create_geocoder(cfg):
    backend = cfg.get("backend")
    if backend is None:
        return None

    if backend == "nominatim":
        return NominatimGeocoder(**cfg.get("nominatim", {}))

    raise ValueError(f"Unknown geocoder backend: {backend}")


def create_cost_provider(cfg):
    backend = cfg["cost_provider"]["backend"]

    if backend == "google":
        return GoogleCostProvider(
            cfg["cost_provider"]["google"]["api_key"]
        )
    if backend == "osrm":
        return OSRMCostProvider(
            cfg["cost_provider"]["osrm"]["base_url"]
        )

    raise ValueError(f"Unknown cost backend: {backend}")


def create_route_renderer(cfg):
    backend = cfg["route_renderer"]["backend"]

    if backend == "google":
        return GoogleRouteRenderer(
            cfg["cost_provider"]["google"]["api_key"]
        )

    if backend == "google-web":
        return GoogleMapsURLRenderer()

    if backend == "osrm":
        return OSRMRouteRenderer(
            cfg["cost_provider"]["osrm"]["base_url"], "osrm"
        )
    if backend == "geojson":
        return OSRMRouteRenderer(
            cfg["cost_provider"]["osrm"]["base_url"], "geojson"
        )

    raise ValueError(f"Unknown render backend: {backend}")
