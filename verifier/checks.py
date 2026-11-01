"""Checks shared by the verifiers. Pure functions of contract instances and the maps' truth."""

from .maps import MAPS
from .tsp import shortest_tour, table


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def map_problem(name):
    if name not in MAPS:
        return f"no map {name!r}: the maps are map-01 to map-40"
    return None


def truth(name):
    """The map's true distance table and (length, tour) of a shortest tour."""
    distances = table(list(MAPS[name]))
    return distances, shortest_tour(distances)
