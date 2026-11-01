"""A map's tour rules: distances, a tour's length, and the shortest tour.

src/plugin/tsp.py and verifier/tsp.py are byte-for-byte copies (a test enforces it): the tools and
the verifier measure by the same rules. Pure standard library, on plain values: a city is an
(x, y) pair of integers, and city i of a map (1-based) is its list's item i - 1.

A distance is TSPLIB's EUC_2D: the straight-line distance rounded to the nearest whole number,
computed exactly with integers (nint(sqrt(s)) is r = isqrt(s), plus 1 when s - r*r > r, since
(r + 1/2)^2 = r*r + r + 1/4 and s is a whole number).
"""

from math import isqrt


def distance(a, b):
    squared = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    root = isqrt(squared)
    return root + 1 if squared - root * root > root else root


def table(cities):
    """Every pair's distance: row i, column j is city i + 1 to city j + 1."""
    return [[distance(a, b) for b in cities] for a in cities]


def cities_are(cities):
    """ "city 4 is" or "cities 4, 5 are"."""
    names = ", ".join(map(str, cities))
    return f"city {names} is" if len(cities) == 1 else f"cities {names} are"


def tour_problem(tour, count):
    """What is wrong with ``tour`` as a tour of cities 1 to ``count``, or None."""
    unknown = sorted({city for city in tour if not 1 <= city <= count})
    if unknown:
        return f"{cities_are(unknown)} not on the map (its cities are 1 to {count})"
    repeated = sorted({city for city in tour if tour.count(city) > 1})
    if repeated:
        return f"{cities_are(repeated)} visited more than once"
    missing = [city for city in range(1, count + 1) if city not in tour]
    if missing:
        return f"{cities_are(missing)} never visited"
    return None


def tour_length(tour, distances):
    """The length of the closed tour: each step's distance, and the return to the first city."""
    return sum(distances[a - 1][b - 1] for a, b in zip(tour, tour[1:] + tour[:1]))


def shortest_tour(distances):
    """(length, tour) of a shortest closed tour, by Held-Karp: the tour starts at city 1 and, of the
    two directions, takes the one whose second city has the smaller id. Ties go to smaller ids."""
    count = len(distances)
    if count == 1:
        return 0, [1]
    full = (1 << count) - 1
    # best[(mask, end)]: the shortest path from city 1 through the cities of mask, ending at end.
    best = {(1 | 1 << end, end): (distances[0][end], 0) for end in range(1, count)}
    for size in range(3, count + 1):
        for mask in range(1, full + 1, 2):
            if mask.bit_count() != size:
                continue
            for end in range(1, count):
                if not mask >> end & 1:
                    continue
                before = mask ^ 1 << end
                options = [
                    (best[(before, last)][0] + distances[last][end], last)
                    for last in range(1, count)
                    if before >> last & 1 and (before, last) in best
                ]
                best[(mask, end)] = min(options)
    length, end = min((best[(full, end)][0] + distances[end][0], end) for end in range(1, count))
    path, mask = [], full
    while end:
        path.append(end + 1)
        mask, end = mask ^ 1 << end, best[(mask, end)][1]
    tour = [1, *reversed(path)]
    if count > 2 and tour[1] > tour[-1]:
        tour = [1, *reversed(tour[1:])]
    return length, tour
