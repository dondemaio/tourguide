from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

from backends.factory import create_geocoder, create_cost_provider, create_route_renderer
from destinations import resolve_plan
from planning import prepare_plan
from solver import solve_vrptw


def build_result(nodes, locations, resolved_locations, solution, base_ts, timezone):
    zone = ZoneInfo(timezone)

    def timestamp(seconds):
        return datetime.fromtimestamp(base_ts + seconds, zone).isoformat()

    visits = []
    for position, visit in enumerate(solution.visits):
        index = visit.node_index
        node = nodes[index]
        role = "start" if position == 0 else "end" if position == len(solution.visits) - 1 else "visit"
        visits.append({
            "node_index": index,
            "role": role,
            "destination_id": node["id"] if role == "visit" else None,
            "name": node.get("name", node.get("id", role)),
            "location": locations[index],
            "resolved_location": resolved_locations[index],
            "provider_ids": deepcopy(node.get("provider_ids", {})),
            "arrival": timestamp(visit.arrival_seconds),
            "service_start": timestamp(visit.service_start_seconds),
            "departure": timestamp(visit.departure_seconds),
            "travel_seconds": visit.travel_seconds,
            "waiting_seconds": visit.waiting_seconds,
            "service_seconds": visit.service_seconds,
        })
    totals = {key: sum(visit[key] for visit in visits)
              for key in ("travel_seconds", "waiting_seconds", "service_seconds")}
    totals["elapsed_seconds"] = sum(totals.values())
    return {
        "timezone": timezone,
        "status": "feasible",
        "solver_status": solution.status,
        "visits": visits,
        "totals": totals,
    }


def calculate_route(plan, repository, config):
    """Calculate a route without CLI or HTTP dependencies."""
    nodes, windows, services, groups, base_ts = prepare_plan(resolve_plan(plan, repository))
    locations = [node["location"] for node in nodes]
    geocoder = create_geocoder(config.get("geocoder", {}))
    resolved_locations = geocoder.geocode(locations) if geocoder else locations
    if len(resolved_locations) != len(locations):
        raise ValueError("Geocoder returned an unexpected number of locations")
    provider = create_cost_provider(config)
    matrix = provider.build_time_matrix(resolved_locations, base_ts)
    solution = solve_vrptw(matrix, windows, services,
                           config["solver"]["time_limit_seconds"], groups,
                           config.get("debug", False))
    return build_result(nodes, locations, resolved_locations, solution, base_ts, plan["timezone"])


def render_route(result, config):
    """Render selected visits in their calculated order."""
    visits = result["visits"]
    return create_route_renderer(config).build_route(
        [visit["location"] for visit in visits],
        [visit["resolved_location"] for visit in visits],
        list(range(len(visits))),
    )
