"""An independent oracle for the tests, written apart from tsp.py: distances by floating point, and
the optimum by brute force over every tour."""

from __future__ import annotations

from functools import cache
from itertools import permutations
from math import floor, hypot

from verifier.maps import MAPS


def distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return floor(hypot(a[0] - b[0], a[1] - b[1]) + 0.5)


def length(tour: list[int], cities: tuple[tuple[int, int], ...]) -> int:
    return sum(distance(cities[a - 1], cities[b - 1]) for a, b in zip(tour, tour[1:] + tour[:1]))


@cache
def longest(name: str) -> tuple[int, ...]:
    """A longest tour: never a shortest one on these maps."""
    cities = MAPS[name]
    return max(((1, *rest) for rest in permutations(range(2, len(cities) + 1))), key=lambda t: length(list(t), cities))


@cache
def optimum(name: str) -> tuple[int, tuple[tuple[int, ...], ...]]:
    """The shortest length and every shortest tour, each once: starting at city 1, in the direction
    whose second city is smaller."""
    cities = MAPS[name]
    best, tours = None, []
    for rest in permutations(range(2, len(cities) + 1)):
        if rest[0] > rest[-1]:
            continue
        tour = (1, *rest)
        size = length(list(tour), cities)
        if best is None or size < best:
            best, tours = size, [tour]
        elif size == best:
            tours.append(tour)
    return best, tuple(tours)
