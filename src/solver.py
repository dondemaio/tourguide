from ortools.constraint_solver import pywrapcp, routing_enums_pb2

_must_visit: int = 10 ** 9


def solve_vrptw(time_matrix, time_windows, service_times, time_limit_seconds, disjunctions=None, debug=False):
    node_count = len(time_matrix)

    def debug_print(*args):
        if debug:
            print("(Solver) ", *args)

    # Sanity checks.
    if debug:
        assert len(time_matrix) == len(time_windows) == len(service_times), "Mismatch lengths"
        for tw in time_windows:
            start, end = tw
            assert 0 <= start <= end and end >= 0, f"Invalid time window {tw}"
        for row in time_matrix:
            assert len(row) == len(time_matrix), "Time matrix not square"

    # Routing index manager with separate start and end nodes
    debug_print("Step 1: Creating RoutingIndexManager...")
    manager = pywrapcp.RoutingIndexManager(
        node_count,
        1,  # single vehicle
        [0],  # start node index
        [node_count - 1]  # end node index
    )
    debug_print("Step 1: RoutingIndexManager created.")

    debug_print("Step 2: Creating RoutingModel...")
    routing = pywrapcp.RoutingModel(manager)
    debug_print("Step 2: RoutingModel created.")

    # Transit callback: travel time + service time at origin
    def time_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return time_matrix[from_node][to_node] + service_times[from_node]

    debug_print("Step 3: Registering transit callback...")
    transit_cb = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)
    debug_print("Step 3: Transit callback registered.")

    # Add Time dimension with slack
    debug_print("Step 4: Adding time dimension...")
    routing.AddDimension(
        transit_cb,
        6 * 3600,  # max waiting slack (6h)
        24 * 3600,  # max route duration (24h)
        False,  # do not force start at zero
        "Time"
    )
    time_dim = routing.GetDimensionOrDie("Time")
    debug_print("Step 4: Time dimension added.")

    # Apply time windows
    debug_print("Step 5: Applying time windows...")
    for node, (start, end) in enumerate(time_windows):
        debug_print(f"\tNode {node} time window: {start}-{end}")
        if node == len(time_windows) - 1:  # index of end node
            idx = routing.End(0)  # vehicle 0
        else:
            idx = manager.NodeToIndex(node)
        debug_print(f"\tgot index: {idx}")
        time_dim.CumulVar(idx).SetRange(start, end)
        debug_print(f"\tset range...")
    debug_print("Step 5: Time windows applied.")

    # TODO dafuq is this?
    # routing.AddVariableMinimizedByFinalizer(time_dim.CumulVar(routing.End(0)))

    debug_print("Step 6: Adding disjunctions...")
    for group in disjunctions or []:
        routing.AddDisjunction(group, _must_visit)
        debug_print(f"\tDisjunction group added: {group}")
    debug_print("Step 6: Disjunctions added.")

    # Search parameters
    debug_print("Step 7: Solving...")
    search = pywrapcp.DefaultRoutingSearchParameters()
    search.time_limit.seconds = time_limit_seconds
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH

    solution = routing.SolveWithParameters(search)
    if not solution:
        raise RuntimeError("No feasible route found (check time windows)")

    # Extract route order
    route = []
    idx = routing.Start(0)
    while not routing.IsEnd(idx):
        route.append(manager.IndexToNode(idx))
        idx = solution.Value(routing.NextVar(idx))
    route.append(manager.IndexToNode(idx))

    debug_print("found Route:", route)

    return route
