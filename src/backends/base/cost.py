from abc import ABC, abstractmethod


class CostProvider(ABC):
    @abstractmethod
    def build_time_matrix(self, locations, departure_ts):
        """
        locations: list[str] (lat,lon or address depending on backend)
        departure_ts: int | None (unix seconds)
        returns: matrix[origin][destination] in seconds
        """
        pass
