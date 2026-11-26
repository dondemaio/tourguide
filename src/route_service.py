from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

from backends.factory import create_geocoder, create_cost_provider, create_route_renderer
from destinations import resolve_plan
from planning import prepare_plan
from solver import solve_vrptw
from provider_cache import ProviderCache, geocode_locations, travel_matrix


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
            "visit_index": node.get("visit_index"),
            "required": node.get("required", True),
            "priority": node.get("priority", 3) if not node.get("required", True) else None,
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
        "objective": solution.objective,
        "visits": visits,
        "totals": totals,
    }


def calculate_route(plan, repository, config):
    """Calculate a route without CLI or HTTP dependencies."""
    resolved = resolve_plan(plan, repository)
    nodes, windows, services, groups, base_ts, optional_groups, omitted = prepare_plan(resolved)
    locations = [node["location"] for node in nodes]
    geocoder = create_geocoder(config.get("geocoder", {}))
    settings = config.get("cache", {})
    cache = ProviderCache(settings.get("path", "cache/providers.sqlite3")) if settings.get("enabled", False) else None
    resolved_locations = geocode_locations(geocoder, locations, config, cache)
    if len(resolved_locations) != len(locations):
        raise ValueError("Geocoder returned an unexpected number of locations")
    provider = create_cost_provider(config)
    matrix = travel_matrix(provider, resolved_locations, base_ts, config, cache)
    solution = solve_vrptw(matrix, windows, services,
                           config["solver"]["time_limit_seconds"], groups,
                           config.get("debug", False), optional_groups=optional_groups)
    result = build_result(nodes, locations, resolved_locations, solution, base_ts, plan["timezone"])
    visited = {visit["visit_index"] for visit in result["visits"]}
    reasons = dict(omitted)
    result["omitted_visits"] = [
        {"visit_index": index, "destination_id": stop["id"], "name": stop["name"],
         "priority": stop.get("priority", 3),
         "reason": reasons.get(index, "not_selected_by_solver")}
        for index, stop in enumerate(resolved["stops"])
        if not stop.get("required", True) and index not in visited
    ]
    return result


def render_route(result, config):
    """Render selected visits in their calculated order."""
    visits = result["visits"]
    return create_route_renderer(config).build_route(
        [visit["location"] for visit in visits],
        [visit["resolved_location"] for visit in visits],
        list(range(len(visits))),
    )
