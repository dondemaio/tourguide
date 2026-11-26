import pytest
from solver import solve_vrptw


def test_fixed_start_and_end():
    assert solve_vrptw([[0, 60], [60, 0]], [(0, 0), (60, 60)], [0, 0], 1) == [0, 1]


def test_time_windows_force_order():
    matrix = [[0 if i == j else 60 for j in range(4)] for i in range(4)]
    assert solve_vrptw(matrix, [(0, 0), (300, 300), (60, 60), (420, 420)],
                       [0, 60, 60, 0], 1) == [0, 2, 1, 3]


def test_service_time_can_make_route_infeasible():
    matrix = [[0, 60, 60], [60, 0, 60], [60, 60, 0]]
    with pytest.raises(RuntimeError, match="No feasible route"):
        solve_vrptw(matrix, [(0, 0), (60, 60), (120, 120)], [0, 60, 0], 1)


def test_feasible_alternative_window():
    matrix = [[0 if i == j else 60 for j in range(4)] for i in range(4)]
    assert solve_vrptw(matrix, [(0, 0), (30, 30), (120, 120), (240, 240)],
                       [0, 0, 0, 0], 1, [[1, 2]]) == [0, 2, 3]
