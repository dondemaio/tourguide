from abc import ABC, abstractmethod


class Geocoder(ABC):
    @abstractmethod
    def geocode(self, locations):
        """
        Input:
          locations: list[str] (addresses or lon,lat)

        Output:
          list[str] in 'lon,lat' format
        """
        pass
