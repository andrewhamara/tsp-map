"""The shortest-tour task's verdict: the submitted tour against the optimum of the map's true cities.

Six constraints, in order; every one must hold. Each is {id, constraint, ok, expected, actual,
message}: ok is true, false, or null when a constraint it needs did not hold. Any failure of 1 to 4
scores 0. Otherwise the score is the shortest length over the tour's length, halved when the claimed
length is wrong, and at most 0.99 unless all six hold.
"""

from .answer import answer_key_problem
from .checks import map_problem, result, truth
from .tsp import tour_length, tour_problem

CONSTRAINTS = (
    ("map", "The map exists"),
    ("answer-key", "The answer key pinned a shortest tour of the map's true cities"),
    ("same-map", "The submission is for the task's map"),
    ("tour-complete", "The tour visits every city exactly once"),
    ("length-claimed", "The claimed length is the tour's real length"),
    ("shortest", "The tour is a shortest tour"),
)
GUARDS = 4  # constraints 1 to 4: a failure scores 0


def verify_task(arguments, output, reference, workspace):
    """``arguments``: a contract MapInput; ``output``: TourOutput; ``reference``: AnswerKeyOutput or None."""
    checks = {}

    def put(key, ok, expected=None, actual=None, message=""):
        checks[key] = {"ok": ok, "expected": expected, "actual": actual, "message": "" if ok else message}

    name, tour = arguments.map, list(output.tour)
    problem = map_problem(name)
    put("map", problem is None, message=problem)
    real = None
    if problem is None:
        distances, (shortest, best) = truth(name)
        count = len(distances)
        if reference is None:
            put("answer-key", False, shortest, None, "No answer key: answer_key never ran for this map.")
        else:
            wrong = answer_key_problem(name, reference)
            put("answer-key", wrong is None, shortest, reference.length, f"The answer key is wrong: {wrong}.")
        put("same-map", output.map == name, name, output.map, f"The submission is for {output.map!r}, not {name!r}.")
        broken = tour_problem(tour, count)
        put("tour-complete", broken is None, count, tour, f"The tour is not a tour of the {count} cities: {broken}.")
        if broken is None:
            real = tour_length(tour, distances)
            put(
                "length-claimed",
                output.length == real,
                real,
                output.length,
                f"The tour is claimed to be {output.length} long but is {real}: the sum of the distances along it, "
                "the return to the first city included.",
            )
            longer = (real - shortest) / shortest * 100
            put(
                "shortest",
                real == shortest,
                shortest,
                real,
                f"The tour is {real} long; the shortest is {shortest} ({longer:.1f}% longer), e.g. "
                f"{' → '.join(map(str, best + best[:1]))}.",
            )

    constraints = []
    for key, text in CONSTRAINTS:
        check = checks.get(key)
        if check is None:
            waiting = next(k for k, _ in CONSTRAINTS if checks.get(k, {"ok": True})["ok"] is False)
            check = {"ok": None, "expected": None, "actual": None, "message": f"Not checked: {waiting} did not hold."}
        constraints.append({"id": key, "constraint": text, **check})
    failed = [item for item in constraints if item["ok"] is False]
    details = {"constraints": constraints}
    if problem is None:
        details |= {"expected": {"length": shortest, "tour": best}, "cities": count, "length": real}
    if not failed:
        return result(
            True,
            f"All {len(CONSTRAINTS)} checks hold: the tour of {name}'s {count} cities is {real} long, the shortest possible.",
            **details,
        )
    first = failed[0]
    message = f"{first['id']}: {first['message']}" + (f" (+{len(failed) - 1} more)" if len(failed) > 1 else "")
    if any(item["ok"] is not True for item in constraints[:GUARDS]):
        return result(False, message, score=0.0, **details)
    ratio = shortest / real
    score = min(0.99, ratio if output.length == real else ratio / 2)
    return result(False, message, score=round(score, 4), ratio=round(ratio, 4), **details)
