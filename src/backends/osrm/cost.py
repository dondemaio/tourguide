import requests
from backends.base.cost import CostProvider


class OSRMCostProvider(CostProvider):
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def build_time_matrix(self, locations, departure_ts=None):
        coords = ";".join(locations)

        url = f"{self.base_url}/table/v1/driving/{coords}"
        params = {"annotations": "duration"}

        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        if data.get("code") != "Ok":
            raise RuntimeError(data)

        return data["durations"]
