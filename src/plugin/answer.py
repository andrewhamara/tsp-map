"""answer_key: a shortest tour of the map, by Held-Karp over the distances read_map finds.

NanoAgent runs it before the agent, out of its sight, and the verifier checks it against the
optimum of the map's true cities.
"""

from __future__ import annotations

from pathlib import Path

from contract import AnswerKeyOutput, MapInput
from plugin.read_map import read_map
from plugin.tsp import shortest_tour


def answer_key(given: MapInput, workspace: Path) -> AnswerKeyOutput:
    found = read_map(given, workspace)
    length, tour = shortest_tour(found.distances)
    return AnswerKeyOutput(map=given.map, cities=len(found.cities), tour=tour, length=length)
