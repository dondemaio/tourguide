import json

import requests

from backends.base.render import RouteRenderer

_osrm_params = {
    "overview": "full",
    "geometries": "polyline",
    "steps": "true",
}
_geojson_params = {
    "overview": "full",
    "geometries": "geojson",
    "steps": "true",
}


class OSRMRouteRenderer(RouteRenderer):
    def __init__(self, base_url, style="osrm"):
        self.base_url = base_url.rstrip("/")
        self.style = style

    def build_route(self, locations, coord_locations, order):
        ordered = [coord_locations[i] for i in order]
        coords = ";".join(ordered)

        url = f"{self.base_url}/route/v1/driving/{coords}"

        if self.style is None or self.style == "osrm":
            params = _osrm_params
        elif self.style == "geojson":
            params = _geojson_params
        else:
            params = _osrm_params

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        route_data = r.json()

        if self.style is None or self.style == "osrm":
            return route_data
        elif self.style == "geojson":
            geojson = {
                "type": "Feature",
                "geometry": route_data["routes"][0]["geometry"],
                "properties": {}
            }
            return json.dumps(geojson)
        else:
            return route_data
