from abc import ABC, abstractmethod


class RouteRenderer(ABC):
    @abstractmethod
    def build_route(self, locations, coord_locations, order):
        """
        locations: list[str]
        coord_locations: list[str]
        order: list[int]
        returns: backend-specific route payload
        """
        pass
