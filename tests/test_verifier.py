from __future__ import annotations

from pathlib import Path

import pytest
from oracle import length, optimum
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, AnswerKeyOutput, MapInput, Task, Tool
from plugin import answer_key, read_map
from verifier.maps import MAPS


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def key_for(name: str) -> dict:
    return plain_output(answer_key(MapInput(map=name), Path(".")))


def verify_task(name: str, tour: list[int], claimed: int | None = None, reference=..., arguments=None) -> dict:
    given, made = TASKS[Task.SHORTEST_TOUR]
    reference = key_for(name) if reference is ... else reference
    claimed = length(tour, MAPS[name]) if claimed is None else claimed
    return verifier.verify_task(
        "shortest-tour",
        build_output(arguments or {"map": name}, given),
        build_output({"map": name, "tour": tour, "length": claimed}, made),
        None if reference is None else build_output(reference, AnswerKeyOutput),
        ".",
    )


def checks(verdict: dict) -> dict:
    return {item["id"]: item["ok"] for item in verdict["details"]["constraints"]}


# Correct


def test_approves_a_shortest_tour() -> None:
    best, tours = optimum("map-05")
    verdict = verify_task("map-05", list(tours[0]))
    assert verdict["valid"] is True and verdict["score"] == 1.0
    assert verdict["message"] == f"All 6 checks hold: the tour of map-05's 9 cities is {best} long, the shortest possible."


def test_a_shortest_tour_passes_from_any_start_in_either_direction() -> None:
    tour = list(optimum("map-12")[1][0])
    for start in range(len(tour)):
        turned = tour[start:] + tour[:start]
        assert verify_task("map-12", turned)["valid"] is True
        assert verify_task("map-12", list(reversed(turned)))["valid"] is True


@pytest.mark.parametrize("name", ["map-36", "map-37", "map-40"])
def test_every_tied_shortest_tour_passes(name: str) -> None:
    _, tours = optimum(name)
    assert len(tours) > 1
    assert all(verify_task(name, list(tour))["valid"] for tour in tours)


# Incorrect


def test_a_longer_tour_scores_by_how_close_it_comes() -> None:
    best, _ = optimum("map-05")
    tour = list(range(1, 10))
    real = length(tour, MAPS["map-05"])
    verdict = verify_task("map-05", tour)
    assert verdict["valid"] is False and verdict["score"] == round(best / real, 4)
    assert checks(verdict)["shortest"] is False and checks(verdict)["length-claimed"] is True
    assert f"The tour is {real} long; the shortest is {best}" in verdict["message"]


def test_a_wrong_claimed_length_halves_the_score() -> None:
    best, tours = optimum("map-05")
    verdict = verify_task("map-05", list(tours[0]), claimed=best - 1)
    assert verdict["valid"] is False and verdict["score"] == 0.5
    assert verdict["message"].startswith(f"length-claimed: The tour is claimed to be {best - 1} long but is {best}")


def test_claiming_the_optimum_for_a_longer_tour_is_caught() -> None:
    best, _ = optimum("map-05")
    tour = list(range(1, 10))
    verdict = verify_task("map-05", tour, claimed=best)
    assert checks(verdict)["length-claimed"] is False and checks(verdict)["shortest"] is False
    assert verdict["score"] == round(best / length(tour, MAPS["map-05"]) / 2, 4)


def test_the_wrong_map_scores_zero() -> None:
    tour = list(optimum("map-05")[1][0])
    given, made = TASKS[Task.SHORTEST_TOUR]
    verdict = verifier.verify_task(
        "shortest-tour",
        build_output({"map": "map-05"}, given),
        build_output({"map": "map-10", "tour": tour, "length": 0}, made),
        build_output(key_for("map-05"), AnswerKeyOutput),
        ".",
    )
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["message"].startswith("same-map:")


# Missing


def test_an_empty_tour_scores_zero() -> None:
    verdict = verify_task("map-01", [], claimed=0)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert "cities 1, 2, 3, 4, 5 are never visited" in verdict["message"]
    assert checks(verdict)["length-claimed"] is None and checks(verdict)["shortest"] is None


def test_a_tour_missing_a_city_scores_zero() -> None:
    verdict = verify_task("map-05", [1, 2, 3, 4, 5, 6, 7, 8], claimed=100)
    assert verdict["score"] == 0.0 and "city 9 is never visited" in verdict["message"]


def test_no_answer_key_scores_zero() -> None:
    verdict = verify_task("map-05", list(optimum("map-05")[1][0]), reference=None)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["message"].startswith("answer-key: No answer key")


# Malformed


@pytest.mark.parametrize(
    ("tour", "message"),
    [
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 1], "city 1 is visited more than once"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 10], "city 10 is not on the map"),
        ([0, 1, 2, 3, 4, 5, 6, 7, 8], "city 0 is not on the map"),
    ],
)
def test_a_repeated_or_unknown_city_scores_zero(tour: list[int], message: str) -> None:
    verdict = verify_task("map-05", tour, claimed=1000)
    assert verdict["valid"] is False and verdict["score"] == 0.0 and message in verdict["message"]


def test_an_answer_key_that_is_not_shortest_fails_the_run() -> None:
    wrong = key_for("map-05") | {"tour": list(range(1, 10)), "length": length(list(range(1, 10)), MAPS["map-05"])}
    verdict = verify_task("map-05", list(optimum("map-05")[1][0]), reference=wrong)
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["message"].startswith("answer-key:")


def test_an_unknown_map_scores_zero() -> None:
    given, made = TASKS[Task.SHORTEST_TOUR]
    verdict = verifier.verify_task(
        "shortest-tour",
        build_output({"map": "map-99"}, given),
        build_output({"map": "map-99", "tour": [1], "length": 0}, made),
        None,
        ".",
    )
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["message"].startswith("map:")


# Boundary


def test_on_a_line_going_out_and_back_is_shortest() -> None:
    assert verify_task("map-36", [1, 2, 3, 4, 5])["valid"] is True
    assert verify_task("map-36", [1, 3, 5, 4, 2])["valid"] is True
    zigzag = verify_task("map-36", [1, 4, 2, 5, 3])
    assert zigzag["valid"] is False and 0 < zigzag["score"] < 1


def test_the_grid_needs_one_diagonal() -> None:
    # 1-2-3 / 4-5-6 / 7-8-9: eight grid steps and one diagonal is 1016; a tour of 2 diagonals is longer.
    assert verify_task("map-40", [1, 2, 3, 6, 9, 5, 8, 7, 4])["valid"] is True
    assert verify_task("map-40", [1, 2, 3, 6, 5, 9, 8, 7, 4])["valid"] is False


# Tool calls


def test_checks_tool_inputs_and_outputs() -> None:
    def verify_input(tool: str, name: str) -> bool:
        return verifier.verify_input(tool, build_output({"map": name}, TOOLS[Tool(tool)][0]))["valid"]

    assert verify_input("read_map", "map-01") and not verify_input("read_map", "map-41")
    assert verify_input("answer_key", "map-40") and not verify_input("answer_key", "map")

    def verify_output(tool: str, name: str, made: dict) -> dict:
        given, output = TOOLS[Tool(tool)]
        return verifier.verify_output(tool, build_output({"map": name}, given), build_output(made, output), ".")

    found = plain_output(read_map(MapInput(map="map-05"), Path(".")))
    assert verify_output("read_map", "map-05", found)["valid"] is True
    moved = found | {"cities": [found["cities"][0] | {"x": 1}, *found["cities"][1:]]}
    assert "city 1 of map-05 is reported at" in verify_output("read_map", "map-05", moved)["message"]
    dropped = found | {"cities": found["cities"][:-1]}
    assert "has 9 cities, not 8" in verify_output("read_map", "map-05", dropped)["message"]
    shifted = found | {"distances": [[d + 1 for d in row] for row in found["distances"]]}
    assert "distance table" in verify_output("read_map", "map-05", shifted)["message"]
    assert verify_output("read_map", "map-06", found)["valid"] is False
    key = key_for("map-05")
    assert verify_output("answer_key", "map-05", key)["valid"] is True
    assert verify_output("answer_key", "map-05", key | {"length": key["length"] - 1})["valid"] is False


def test_the_read_map_task_is_judged_as_its_tool() -> None:
    found = plain_output(read_map(MapInput(map="map-38"), Path(".")))
    given, made = TASKS[Task.READ_MAP]
    verdict = verifier.verify_task("read-map", build_output({"map": "map-38"}, given), build_output(found, made), None, ".")
    assert verdict["valid"] is True


def test_the_verdict_is_the_same_twice() -> None:
    assert verify_task("map-05", [1, 2, 3, 4, 5, 6, 7, 8, 9], claimed=5) == verify_task(
        "map-05", [1, 2, 3, 4, 5, 6, 7, 8, 9], claimed=5
    )
