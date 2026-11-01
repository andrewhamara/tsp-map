from __future__ import annotations

from pathlib import Path

import pytest
from oracle import distance as float_distance
from oracle import optimum

from plugin.tsp import distance, shortest_tour, table, tour_length, tour_problem
from verifier.maps import MAPS

ROOT = Path(__file__).resolve().parents[1]


def test_the_verifier_measures_by_a_byte_for_byte_copy_of_the_rules() -> None:
    assert (ROOT / "verifier/tsp.py").read_bytes() == (ROOT / "src/plugin/tsp.py").read_bytes()


def test_distances_round_to_nearest_exactly_as_floating_point_does() -> None:
    for dx in range(120):
        for dy in range(120):
            assert distance((0, 0), (dx, dy)) == float_distance((0, 0), (dx, dy)), (dx, dy)
    # sqrt(20) = 4.47 rounds down, sqrt(34) = 5.83 up; distances are symmetric.
    assert (distance((0, 0), (4, 2)), distance((0, 0), (5, 3)), distance((5, 3), (0, 0))) == (4, 6, 6)


@pytest.mark.parametrize("name", sorted(MAPS))
def test_held_karp_finds_the_brute_force_optimum(name: str) -> None:
    distances = table(list(MAPS[name]))
    length, tour = shortest_tour(distances)
    best, tours = optimum(name)
    assert length == best
    assert tuple(tour) in tours and tour_length(tour, distances) == best


def test_the_boundary_maps_have_ties_or_the_shape_they_were_drawn_for() -> None:
    assert len(optimum("map-36")[1]) > 1 and optimum("map-36")[0] == 2 * (420 - 60)
    assert len(optimum("map-37")[1]) > 1
    # The plus sign: two arm-to-center steps of 100 and three diagonals of 141.
    assert len(optimum("map-40")[1]) > 1 and optimum("map-40")[0] == 2 * 100 + 3 * 141
    # Around the circle: consecutive cities by angle, which reading order does not give.
    assert len(optimum("map-38")[1]) == 1


@pytest.mark.parametrize(
    ("tour", "problem"),
    [
        ([1, 2, 3, 4, 5], None),
        ([3, 1, 5, 2, 4], None),
        ([1, 2, 3, 4], "city 5 is never visited"),
        ([1, 2, 3, 4, 4, 5], "city 4 is visited more than once"),
        ([1, 2, 3, 4, 5, 6], "city 6 is not on the map"),
        ([0, 1, 2, 3, 4, 5], "city 0 is not on the map"),
        ([], "cities 1, 2, 3, 4, 5 are never visited"),
    ],
)
def test_tour_problems(tour: list[int], problem: str | None) -> None:
    found = tour_problem(tour, 5)
    assert (found is None) if problem is None else (problem in found)


def test_a_tour_returns_to_its_first_city() -> None:
    distances = [[0, 3, 4], [3, 0, 5], [4, 5, 0]]
    assert tour_length([1, 2, 3], distances) == 3 + 5 + 4
    assert tour_length([2, 3, 1], distances) == tour_length([3, 2, 1], distances) == 12
