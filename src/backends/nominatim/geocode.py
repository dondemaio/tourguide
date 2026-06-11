import time

import requests
from backends.base.geocode import Geocoder


class NominatimGeocoder(Geocoder):
    def __init__(self, base_url="https://nominatim.openstreetmap.org", delay=1.0):
        self.base_url = base_url.rstrip("/")
        self.delay = delay  # politeness delay (seconds)

    def geocode(self, locations):
        coords = []

        for loc in locations:
            # Already coordinates → pass through
            if "," in loc and self._looks_like_coords(loc):
                coords.append(loc)
                continue

            r = requests.get(
                f"{self.base_url}/search",
                params={
                    "q": loc,
                    "format": "json",
                    "limit": 1,
                },
                headers={
                    "User-Agent": "tourguide/1.0"
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()

            if not data:
                raise RuntimeError(f"Geocoding failed for '{loc}'")

            lon = data[0]["lon"]
            lat = data[0]["lat"]
            coords.append(f"{lon},{lat}")

            time.sleep(self.delay)  # respect Nominatim usage policy

        return coords

    def _looks_like_coords(self, value):
        try:
            lon, lat = value.split(",", 1)
            float(lon)
            float(lat)
            return True
        except Exception:
            return False
