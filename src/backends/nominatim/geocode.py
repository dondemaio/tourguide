import time
import math
from threading import Lock

import requests
from backends.base.geocode import Geocoder


_REQUEST_LOCK = Lock()


class NominatimGeocoder(Geocoder):
    def __init__(self, base_url="https://nominatim.openstreetmap.org", delay=1.0):
        self.base_url = base_url.rstrip("/")
        if type(delay) not in (int, float) or not math.isfinite(delay) or delay < 0:
            raise ValueError("Geocoder delay must be a finite nonnegative number")
        if self.base_url == "https://nominatim.openstreetmap.org" and delay < 1:
            raise ValueError("Public Nominatim requires at least one second between requests")
        self.delay = delay

    def geocode(self, locations):
        coords = []

        for loc in locations:
            # Already coordinates → pass through
            if "," in loc and self._looks_like_coords(loc):
                coords.append(loc)
                continue

            with _REQUEST_LOCK:
                try:
                    r = requests.get(
                        f"{self.base_url}/search",
                        params={"q": loc, "format": "json", "limit": 1},
                        headers={"User-Agent": "tourguide/1.0"},
                        timeout=30,
                    )
                    r.raise_for_status()
                finally:
                    time.sleep(self.delay)
            data = r.json()

            if not data:
                raise RuntimeError(f"Geocoding failed for '{loc}'")

            lon = data[0]["lon"]
            lat = data[0]["lat"]
            coordinate = f"{lon},{lat}"
            if not self._looks_like_coords(coordinate):
                raise RuntimeError("Geocoder returned invalid coordinates")
            coords.append(coordinate)

        return coords

    def _looks_like_coords(self, value):
        try:
            lon, lat = value.split(",", 1)
            return -180 <= float(lon) <= 180 and -90 <= float(lat) <= 90
        except ValueError:
            return False
