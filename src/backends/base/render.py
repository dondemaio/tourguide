from abc import ABC, abstractmethod


class RouteRenderer(ABC):
    def render_visits(self, visits):
        """Render ordered structured visits; legacy backends use their location fields."""
        return self.build_route(
            [visit["location"] for visit in visits],
            [visit["resolved_location"] for visit in visits],
            list(range(len(visits))),
        )

    @abstractmethod
    def build_route(self, locations, coord_locations, order):
        """
        locations: list[str]
        coord_locations: list[str]
        order: list[int]
        returns: backend-specific route payload
        """
        pass
