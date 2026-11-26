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


def test_mandatory_group_cannot_be_dropped():
    matrix = [[0 if i == j else 60 for j in range(4)] for i in range(4)]
    with pytest.raises(RuntimeError, match="No feasible route"):
        solve_vrptw(matrix, [(0, 0), (10, 10), (20, 20), (120, 120)],
                   [0, 0, 0, 0], 1, [[1, 2]])


def test_exactly_one_alternative_even_when_both_are_feasible():
    matrix = [[0 if i == j else 60 for j in range(4)] for i in range(4)]
    route = solve_vrptw(matrix, [(0, 0), (60, 180), (60, 180), (240, 240)],
                        [0, 0, 0, 0], 1, [[1, 2]])
    assert route in ([0, 1, 3], [0, 2, 3])


def test_unreachable_leg_is_avoided():
    matrix = [[0, None, 60, None], [None, 0, None, 60],
              [None, 60, 0, None], [None, None, None, 0]]
    assert solve_vrptw(matrix, [(0, 0), (0, 300), (0, 300), (0, 300)],
                       [0, 0, 0, 0], 1) == [0, 2, 1, 3]


def test_unreachable_end_is_infeasible():
    with pytest.raises(RuntimeError, match="No feasible route"):
        solve_vrptw([[0, None], [None, 0]], [(0, 0), (0, 300)], [0, 0], 1)


def test_unreachable_alternative_can_be_inactive():
    matrix = [[0, None, 60, 60], [None, None, None, None],
              [60, None, 0, 60], [60, None, 60, 0]]
    assert solve_vrptw(matrix, [(0, 0), (0, 300), (0, 300), (0, 300)],
                       [0, 0, 0, 0], 1, [[1, 2]]) == [0, 2, 3]


def test_fractional_travel_duration_is_rounded_up():
    matrix = [[0, 60.1], [60.1, 0]]
    assert solve_vrptw(matrix, [(0, 0), (61, 61)], [0, 0], 1) == [0, 1]
    with pytest.raises(RuntimeError, match="No feasible route"):
        solve_vrptw(matrix, [(0, 0), (60, 60)], [0, 0], 1)


@pytest.mark.parametrize("matrix", [
    [[0, -1], [0, 0]], [[0, float("nan")], [0, 0]],
    [[0, float("inf")], [0, 0]], [[0, "60"], [0, 0]],
    [[0, True], [0, 0]], [[0], [0, 0]],
])
def test_invalid_matrix_rejected_without_debug(matrix):
    with pytest.raises(ValueError):
        solve_vrptw(matrix, [(0, 0), (0, 300)], [0, 0], 1)


@pytest.mark.parametrize("windows, services, limit", [
    ([(0, 0)], [0, 0], 1),
    ([(0, 0), (10, 0)], [0, 0], 1),
    ([(0, 0), (-1, 300)], [0, 0], 1),
    ([(0, 0), (0, 86401)], [0, 0], 1),
    ([(0, 0), (0, 300)], [0, -1], 1),
    ([(0, 0), (0, 300)], [0], 1),
    ([(0, 0), (0, 300)], [0, 0], 0),
    ([(0, 0), (0, 300)], [0, 0], 1.5),
])
def test_invalid_constraints_rejected(windows, services, limit):
    with pytest.raises(ValueError):
        solve_vrptw([[0, 60], [60, 0]], windows, services, limit)


@pytest.mark.parametrize("groups", [[[]], [[0, 1]], [[1, 3]], [[1, 1]], [[1], [1, 2]]])
def test_invalid_disjunctions_rejected(groups):
    matrix = [[0 if i == j else 60 for j in range(4)] for i in range(4)]
    with pytest.raises(ValueError):
        solve_vrptw(matrix, [(0, 300)] * 4, [0] * 4, 1, groups)
