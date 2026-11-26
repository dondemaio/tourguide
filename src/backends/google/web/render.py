from urllib.parse import quote_plus, urlencode

from backends.base.render import RouteRenderer


class GoogleMapsURLRenderer(RouteRenderer):
    DEFAULT_MODE = "driving"

    def __init__(self):
        self.travel_mode = self.DEFAULT_MODE

    @staticmethod
    def _query(visit):
        location = visit["location"].strip()
        name = (visit.get("name") or "").strip()
        # Endpoint names are often private labels such as Home or Start.
        if visit.get("role") != "visit" or not name or name.casefold() in location.casefold():
            return location
        try:
            lon, lat = map(float, location.split(","))
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                return f"{lat},{lon}"
        except ValueError:
            pass
        return f"{name}, {location}"

    @staticmethod
    def _place_id(visit):
        return (visit.get("provider_ids", {}).get("google") or "").strip()

    def render_visits(self, visits):
        if len(visits) < 2:
            raise ValueError("Route requires start and end visits")
        queries = [self._query(visit) for visit in visits]
        ids = [self._place_id(visit) for visit in visits]
        params = {"api": 1, "origin": queries[0], "destination": queries[-1],
                  "travelmode": self.travel_mode}
        if ids[0]:
            params["origin_place_id"] = ids[0]
        if ids[-1]:
            params["destination_place_id"] = ids[-1]
        if len(visits) > 2:
            params["waypoints"] = "|".join(queries[1:-1])
            # Google requires a matching ID for every intermediate waypoint.
            if all(ids[1:-1]):
                params["waypoint_place_ids"] = "|".join(ids[1:-1])
        return "https://www.google.com/maps/dir/?" + urlencode(params)

    def build_route(self, locations, coord_locations, order):
        return self.build_route_with_params(locations, order)

    def build_route_with_params(self, locations, order):
        """
        locations: list of address strings or coordinates
        route_indices: list of indices defining the visit order
        Returns: full Google Maps directions URL
        """
        if not locations or not order:
            raise ValueError("Locations and route_indices must be non-empty")

        ordered = [locations[i] for i in order]
        origin = ordered[0]
        destination = ordered[-1]
        waypoints = ordered[1:-1]

        url = "https://www.google.com/maps/dir/?api=1"
        url += f"&origin={quote_plus(origin)}"
        url += f"&destination={quote_plus(destination)}"
        if waypoints:
            url += "&waypoints=" + "|".join(quote_plus(wp) for wp in waypoints)
        url += f"&travelmode={self.travel_mode}"

        return url

    def build_route_basic(self, locations, order):
        ordered_locations = [locations[i] for i in order]
        encoded = "/".join(quote_plus(loc) for loc in ordered_locations)

        return f"https://www.google.com/maps/dir/{encoded}"
