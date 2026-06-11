from copy import deepcopy

import yaml
from dateutil.parser import isoparse

from backends.factory import create_geocoder, create_cost_provider, create_route_renderer
from solver import solve_vrptw

# if sys.version_info >= (3, 12):
#     raise RuntimeError(
#         "Python 3.12 is not supported by OR-Tools Routing Solver. "
#         "Please use Python 3.10 or 3.11."
#     )

# Load config
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

# Load waypoints data
with open("data/waypoints.yaml") as f:
    data = yaml.safe_load(f)

DEBUG_ACTIVE: bool = cfg.get("debug", False)


def debug_print(*args):
    if DEBUG_ACTIVE:
        print("(Main) ", *args)


debug_print("Calculating nodes and disjunctions...")
disjunctions = []
nodes = [data["start"]]
for stop in data["stops"]:
    indices = []
    for i, tw in enumerate(stop["time_windows"]):
        node = deepcopy(stop)
        node["id"] = f"{stop['id']}@tw{i}"
        node["time_window"] = tw
        nodes.append(node)
        # Only create disjunctions for multi-window stops
        if len(stop["time_windows"]) > 1:
            indices.append(len(nodes) - 1)
    if indices:
        disjunctions.append(indices)
nodes = nodes + [data["end"]]
debug_print("Nodes and disjunctions calculated.")
debug_print("Nodes:")
for i, n in enumerate(nodes):
    debug_print("\t", i, n)
debug_print("Disjunctions:", disjunctions)

# Extract locations (to feed into geocoder / cost provider)
locations = [n["location"] for n in nodes]

# Optional geocoding
geocoder = create_geocoder(cfg.get("geocoder", {}))
if geocoder:
    debug_print("Running geocoder...")
    coord_locations = geocoder.geocode(locations)
    debug_print("Geocoder complete.")
    assert len(coord_locations) == len(locations)
else:
    debug_print("Not running geocoder.")
    coord_locations = locations
debug_print("Locations:")
for i, loc in enumerate(coord_locations):
    debug_print(f"\t{locations[i]} -> {loc}")

# Base timestamp = route start
base_ts = int(isoparse(data["start"]["time_window"][0]).timestamp())

# Build time windows and service times (OR-Tools expects relative seconds)
debug_print("Building time windows and service times...")
time_windows = []
service_times = []
for n in nodes:
    start_ts = int(isoparse(n["time_window"][0]).timestamp())
    end_ts = int(isoparse(n["time_window"][1]).timestamp())
    time_windows.append((start_ts - base_ts, end_ts - base_ts))
    service_times.append(n.get("service_minutes", 0) * 60)
debug_print("Time windows and service times built.")

# Build time matrix
debug_print("Calculating time matrix...")
cost_provider = create_cost_provider(cfg)
time_matrix = cost_provider.build_time_matrix(coord_locations, base_ts)
debug_print("Time matrix calculated.")

# Sanity checks.
assert len(time_matrix) == len(nodes), "time_matrix size mismatch"
assert len(time_windows) == len(nodes), "time_windows size mismatch"
assert len(service_times) == len(nodes), "service_times size mismatch"
for start, end in time_windows:
    assert 0 <= start <= end and end >= 0, f"Invalid time window: {start}-{end}"
for row in time_matrix:
    assert len(row) == len(nodes)

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
