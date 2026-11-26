import math
from numbers import Real

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


MAX_HORIZON = 24 * 3600
MAX_WAIT = 6 * 3600


class NoRouteFoundError(RuntimeError):
    """The solver did not find a feasible route within its search limits."""


def _seconds(value, label):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a non-negative finite number")
    if value < 0 or value > MAX_HORIZON:
        raise ValueError(f"{label} must be between 0 and {MAX_HORIZON} seconds")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return math.ceil(value)


def _validate_inputs(time_matrix, time_windows, service_times, time_limit_seconds, disjunctions):
    count = len(time_matrix)
    if count < 2 or len(time_windows) != count or len(service_times) != count:
        raise ValueError("Expected matching matrix, windows and service times with start and end")
    if any(len(row) != count for row in time_matrix):
        raise ValueError("Time matrix must be square")
    if isinstance(time_limit_seconds, bool) or not isinstance(time_limit_seconds, int):
        raise ValueError("Search time limit must be a positive integer in seconds")
    if not 0 < time_limit_seconds <= 2**63 - 1:
        raise ValueError("Search time limit must be a positive integer in seconds")

    windows = []
    for window in time_windows:
        if len(window) != 2:
            raise ValueError("Each time window must contain two bounds")
        start, end = window
        if any(isinstance(v, bool) or not isinstance(v, int) for v in window):
            raise ValueError("Time window bounds must be integer seconds")
        if not 0 <= start <= end <= MAX_HORIZON:
            raise ValueError(f"Invalid time window: {window}; supported horizon is 24 hours")
        windows.append((start, end))

    services = [_seconds(value, "Service duration") for value in service_times]
    matrix = []
    for row in time_matrix:
        normalized = []
        for value in row:
            if value is None:
                normalized.append(None)
                continue
            if isinstance(value, bool) or not isinstance(value, Real) or value < 0:
                raise ValueError("Travel duration must be a non-negative finite number or None")
            if not isinstance(value, int) and not math.isfinite(value):
                raise ValueError("Travel duration must be finite")
            # A leg longer than the entire planning horizon cannot be used.
            normalized.append(None if value > MAX_HORIZON else math.ceil(value))
        matrix.append(normalized)

    groups = []
    seen = set()
    for group in disjunctions or []:
        if not group:
            raise ValueError("Disjunction groups must not be empty")
        members = []
        for node in group:
            if isinstance(node, bool) or not isinstance(node, int) or not 0 < node < count - 1:
                raise ValueError("Disjunction members must be intermediate node indices")
            if node in seen:
                raise ValueError("Disjunction members must be unique across groups")
            seen.add(node)
            members.append(node)
        groups.append(members)
    return matrix, windows, services, groups


def solve_vrptw(time_matrix, time_windows, service_times, time_limit_seconds, disjunctions=None, debug=False):
    """Return node order for a single-day route; None denotes an unreachable leg.

    Each disjunction represents one mandatory visit with alternative nodes.
    Time windows constrain service start, not completion (opening-hours
    preprocessing is responsible for any closing-time adjustment).
    """
    matrix, windows, services, groups = _validate_inputs(
        time_matrix, time_windows, service_times, time_limit_seconds, disjunctions
    )
    count = len(matrix)
    manager = pywrapcp.RoutingIndexManager(count, 1, [0], [count - 1])
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_idx, to_idx):
        origin = manager.IndexToNode(from_idx)
        destination = manager.IndexToNode(to_idx)
        duration = matrix[origin][destination]
        # Keep the callback integer-valued even for forbidden arcs.
        if duration is None:
            return MAX_HORIZON + 1
        return duration + services[origin]

    transit = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimension(transit, MAX_WAIT, MAX_HORIZON, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")

    indices = [routing.Start(0)] + [
        manager.NodeToIndex(node) for node in range(1, count - 1)
    ] + [routing.End(0)]
    for idx, (start, end) in zip(indices, windows):
        time_dim.CumulVar(idx).SetRange(start, end)

    # Preserve self-loops: OR-Tools uses them for inactive alternative nodes.
    for origin in range(count - 1):
        for destination in range(1, count):
            if origin != destination and matrix[origin][destination] is None:
                routing.NextVar(indices[origin]).RemoveValue(indices[destination])

    for group in groups:
        # Negative penalty requires exactly one active member (max_cardinality=1).
        routing.AddDisjunction([indices[node] for node in group], -1)

    search = pywrapcp.DefaultRoutingSearchParameters()
    search.time_limit.seconds = time_limit_seconds
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search.log_search = debug
    solution = routing.SolveWithParameters(search)
    if not solution:
        raise NoRouteFoundError(
            f"No feasible route found within search limits (solver status: {routing.status()}); "
            "check time windows, travel connectivity and search time limit"
        )

    route = []
    idx = routing.Start(0)
    while not routing.IsEnd(idx):
        route.append(manager.IndexToNode(idx))
        idx = solution.Value(routing.NextVar(idx))
    route.append(manager.IndexToNode(idx))
    if debug:
        print("(Solver) found Route:", route)
    return route
