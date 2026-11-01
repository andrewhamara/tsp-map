"""Scripted agents, no model, on every map, each run as NanoAgent runs the task.

answer_key pins the answer first; each scripted agent calls read_map and submits a tour; the
verifier judges it. An exact agent (brute force, tests/oracle.py) must pass on every map with every
shortest tour; a nearest-neighbor agent must pass exactly when its tour is shortest and otherwise
score the optimum over its length; a lying agent, which claims the optimum for its nearest-neighbor
tour, must fail the length check wherever its tour is longer.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from oracle import optimum
from slimconfig import build_output, plain_output

import verifier
from contract import AnswerKeyOutput, MapInput, TourOutput
from plugin import answer_key, read_map
from verifier.maps import MAPS


def nearest_neighbor(distances: list[list[int]]) -> list[int]:
    tour = [1]
    while len(tour) < len(distances):
        here = tour[-1] - 1
        tour.append(min((d, j + 1) for j, d in enumerate(distances[here]) if j + 1 not in tour)[1])
    return tour


def judge(name: str, tour: list[int], claimed: int, workspace: Path) -> dict:
    given = MapInput(map=name)
    key = build_output(plain_output(answer_key(given, workspace)), AnswerKeyOutput)
    output = build_output({"map": name, "tour": tour, "length": claimed}, TourOutput)
    return verifier.verify_task("shortest-tour", build_output({"map": name}, MapInput), output, key, str(workspace))


@pytest.mark.parametrize("name", sorted(MAPS))
def test_scripted_agents_on_every_map(tmp_path: Path, name: str) -> None:
    seen = read_map(MapInput(map=name), tmp_path)
    distances = seen.distances
    best, tours = optimum(name)

    def real(tour: list[int]) -> int:
        return sum(distances[a - 1][b - 1] for a, b in zip(tour, tour[1:] + tour[:1]))

    for tour in tours:
        assert judge(name, list(tour), best, tmp_path)["valid"] is True
    greedy = nearest_neighbor(distances)
    verdict = judge(name, greedy, real(greedy), tmp_path)
    assert verdict["valid"] is (real(greedy) == best)
    assert verdict["score"] == (1.0 if real(greedy) == best else min(0.99, round(best / real(greedy), 4)))
    lie = judge(name, greedy, best, tmp_path)
    assert lie["valid"] is (real(greedy) == best)
    print(f"{name}: {len(distances)} cities, optimum {best} ({len(tours)} shortest tours), "
          f"nearest neighbor {real(greedy)} scores {verdict['score']}")
