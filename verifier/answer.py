"""answer_key: the tour it pins is a shortest tour of the map's true cities."""

from .checks import map_problem, result, truth
from .tsp import tour_length, tour_problem


def verify_input(value):
    problem = map_problem(value.map)
    if problem:
        return result(False, problem)
    return result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    """``output_value``: a contract AnswerKeyOutput, held to the optimum of the true cities."""
    problem = answer_key_problem(input_value.map, output_value)
    if problem:
        return result(False, problem)
    return result(True, f"the answer key is a shortest tour: {output_value.length}")


def answer_key_problem(name, key):
    """What is wrong with a contract AnswerKeyOutput for the map ``name``, or None."""
    distances, (length, _) = truth(name)
    tour = list(key.tour)
    if key.map != name or key.cities != len(distances):
        return f"the answer key is for {key.map!r} with {key.cities} cities, not {name!r} with {len(distances)}"
    problem = tour_problem(tour, len(distances))
    if problem:
        return f"the answer key's tour is not a tour: {problem}"
    if tour_length(tour, distances) != key.length or key.length != length:
        return f"the answer key pins length {key.length}; its tour is {tour_length(tour, distances)} and the shortest is {length}"
    return None
