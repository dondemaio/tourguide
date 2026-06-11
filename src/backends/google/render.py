import requests
from backends.base.render import RouteRenderer


class GoogleRouteRenderer(RouteRenderer):
    def __init__(self, api_key):
        self.api_key = api_key

    def build_route(self, locations, coord_locations, order):
        """
        Returns a Google Directions API JSON response.
        locations: list of strings (addresses or lat,lng)
        order: list of indices for the optimized order
        """
        ordered = [locations[i] for i in order]

        params = {
            "origin": ordered[0],
            "destination": ordered[-1],
            "waypoints": "|".join(ordered[1:-1]) if len(ordered) > 2 else None,
            "mode": "driving",
            "key": self.api_key,
        }

        # Remove None parameters
        params = {k: v for k, v in params.items() if v is not None}

        r = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        if data.get("status") != "OK":
            raise RuntimeError(f"Google Directions API error: {data}")

        return data
