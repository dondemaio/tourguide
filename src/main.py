import argparse

import yaml

from planning import prepare_plan
from destinations import YamlDestinationRepository, resolve_plan

# if sys.version_info >= (3, 12):
#     raise RuntimeError(
#         "Python 3.12 is not supported by OR-Tools Routing Solver. "
#         "Please use Python 3.10 or 3.11."
#     )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--waypoints", default="data/waypoints.yaml")
    parser.add_argument("--destinations", default="data/destinations.yaml")
    return parser.parse_args()


args = parse_args()

# Load config
with open(args.config) as f:
    cfg = yaml.safe_load(f)

# Load waypoints data
with open(args.waypoints) as f:
    data = yaml.safe_load(f)

DEBUG_ACTIVE: bool = cfg.get("debug", False)


def debug_print(*args):
    if DEBUG_ACTIVE:
        print("(Main) ", *args)


nodes, time_windows, service_times, disjunctions, base_ts = prepare_plan(resolve_plan(data, YamlDestinationRepository(args.destinations)))

# Extract locations (to feed into geocoder / cost provider)
locations = [n["location"] for n in nodes]

from backends.factory import create_geocoder, create_cost_provider, create_route_renderer
from solver import solve_vrptw

# Optional geocoding
geocoder = create_geocoder(cfg.get("geocoder", {}))
if geocoder:
    debug_print("Running geocoder...")
    coord_locations = geocoder.geocode(locations)
    debug_print("Geocoder complete.")
    if len(coord_locations) != len(locations):
        raise ValueError("Geocoder returned an unexpected number of locations")
else:
    debug_print("Not running geocoder.")
    coord_locations = locations
debug_print("Locations:")
for i, loc in enumerate(coord_locations):
    debug_print(f"\t{locations[i]} -> {loc}")

# Build time matrix
debug_print("Calculating time matrix...")
cost_provider = create_cost_provider(cfg)
time_matrix = cost_provider.build_time_matrix(coord_locations, base_ts)
debug_print("Time matrix calculated.")

# Solver validates matrix, windows and service times before invoking OR-Tools.
debug_print("Nodes with time windows and service times:")
for i, n in enumerate(nodes):
    debug_print(i, n["id"], time_windows[i], service_times[i])

# TODO do more sanity checks?
# if cost_provider.requires_coordinates and locations == coord_locations:
#     raise RuntimeError(
#         "OSRM backend requires coordinates, but no geocoder is configured."
#     )

# Solve VRPTW
debug_print("Calling solver...")
route = solve_vrptw(
    time_matrix,
    time_windows,
    service_times,
    cfg["solver"]["time_limit_seconds"],
    disjunctions,
    DEBUG_ACTIVE,
)
debug_print("Solver called.")

# Generate route directions (backend-specific)
renderer = create_route_renderer(cfg)
route_data = renderer.build_route(locations, coord_locations, route)

print("Visit order (node indices):", route)
print("Route data returned from backend:")
print(route_data)
