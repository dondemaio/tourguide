import requests
from backends.base.cost import CostProvider


class GoogleCostProvider(CostProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    def build_time_matrix(self, locations, departure_ts):
        """
        Returns a travel-time matrix in seconds using Google Distance Matrix API.
        """
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": "|".join(locations),
            "destinations": "|".join(locations),
            "mode": "driving",
            "departure_time": departure_ts,
            "key": self.api_key,
        }

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        if data.get("status") != "OK":
            raise RuntimeError(f"Google Distance Matrix error: {data}")

        matrix = []
        for row in data["rows"]:
            row_values = []
            for el in row["elements"]:
                if el.get("status") == "ZERO_RESULTS":
                    row_values.append(None)
                    continue
                if el.get("status") != "OK":
                    raise RuntimeError(f"Matrix element error: {el}")
                # Prefer duration_in_traffic if present
                dur = el.get("duration_in_traffic", el["duration"])["value"]
                row_values.append(dur)
            matrix.append(row_values)

        return matrix
