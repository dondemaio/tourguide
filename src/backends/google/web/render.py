from urllib.parse import quote_plus


class GoogleMapsURLRenderer:
    DEFAULT_MODE = "driving"

    def __init__(self):
        self.travel_mode = self.DEFAULT_MODE

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
