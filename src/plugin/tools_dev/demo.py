"""A demo you can watch: tours of a few maps, scripted submissions, and the verifier's verdicts. No model runs.

    uv run python -m plugin.tools_dev.demo

For each map it prints what read_map found, the answer key, and how the verifier judges a few
submissions, and opens the map with a shortest tour (dashed gray) and the first submission's tour
(orange) drawn on it. The pictures are saved in a temporary folder whose path it prints.
"""

from __future__ import annotations

import tempfile
from itertools import pairwise
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from slimconfig import build_output, plain_output

import verifier
from contract import AnswerKeyOutput, MapInput, TourOutput
from plugin import answer_key, read_map
from plugin.read_map import map_path
from plugin.tsp import tour_length

BOLD, DIM, GREEN, RED, ORANGE, RESET = "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[0m"
MARKS = {True: f"{GREEN}✓{RESET}", False: f"{RED}✗{RESET}", None: f"{DIM}·{RESET}"}
SCALE = 2


def greedy(distances: list[list[int]]) -> list[int]:
    """Nearest neighbor from city 1: a quick tour, often not the shortest."""
    tour = [1]
    while len(tour) < len(distances):
        tour.append(min((d, j + 1) for j, d in enumerate(distances[tour[-1] - 1]) if j + 1 not in tour)[1])
    return tour


def picture(name: str, cities: list[tuple[int, int]], best: list[int], tour: list[int], folder: Path) -> Path:
    with Image.open(map_path(name)) as image:
        image = image.convert("RGB").resize((image.width * SCALE, image.height * SCALE), Image.NEAREST)
    pen = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=24)

    def points(order: list[int]) -> list[tuple[int, int]]:
        return [(cities[c - 1][0] * SCALE, cities[c - 1][1] * SCALE) for c in [*order, order[0]]]

    best_points = points(best)
    for a, b in pairwise(best_points):
        steps = max(abs(b[0] - a[0]), abs(b[1] - a[1])) // 10
        for k in range(0, steps, 2):
            start = (a[0] + (b[0] - a[0]) * k // steps, a[1] + (b[1] - a[1]) * k // steps)
            end = (a[0] + (b[0] - a[0]) * (k + 1) // steps, a[1] + (b[1] - a[1]) * (k + 1) // steps)
            pen.line([start, end], fill=(92, 107, 122), width=4)
    pen.line(points(tour), fill=(240, 140, 0), width=6, joint="curve")
    for number, (x, y) in enumerate(cities, 1):
        pen.ellipse((x * SCALE - 13, y * SCALE - 13, x * SCALE + 13, y * SCALE + 13), fill=(34, 74, 120))
        pen.text((x * SCALE + 16, y * SCALE - 34), str(number), fill=(34, 74, 120), font=font)
    path = folder / f"{name}.png"
    image.save(path)
    return path


def judge(name: str, key: dict, label: str, tour: list[int], claimed: int) -> None:
    verdict = verifier.verify_task(
        "shortest-tour",
        build_output({"map": name}, MapInput),
        build_output({"map": name, "tour": tour, "length": claimed}, TourOutput),
        build_output(key, AnswerKeyOutput),
        ".",
    )
    head = f"{GREEN}VALID{RESET}" if verdict["valid"] else f"{RED}INVALID{RESET}"
    print(f"\n  {BOLD}Submission — {label}:{RESET} tour {tour}, claimed length {claimed}")
    print(f"    {head}  score {verdict['score']:.2f}  {DIM}{verdict['message']}{RESET}")
    print("    " + "  ".join(f"{MARKS[c['ok']]} {c['id']}" for c in verdict["details"]["constraints"]))


def main() -> None:
    folder = Path(tempfile.mkdtemp(prefix="tsp-map-demo-"))
    for name, title in (("map-05", "Nine random cities"), ("map-40", "Boundary: a 3x3 grid, where four shortest tours tie")):
        print(f"\n{BOLD}━━━ {name}: {title} ━━━{RESET}")
        found = plain_output(read_map(MapInput(map=name), folder))
        cities = [(c["x"], c["y"]) for c in found["cities"]]
        print(f"  {DIM}read_map found {len(cities)} cities:{RESET} " + ", ".join(f"{i}{xy}" for i, xy in enumerate(cities, 1)))
        key = plain_output(answer_key(MapInput(map=name), folder))
        print(f"  {ORANGE}Answer key:{RESET} shortest length {key['length']}, e.g. {key['tour']}")
        distances = found["distances"]
        quick = greedy(distances)
        submissions = [
            ("the answer key's tour, backwards from city 3", None, None),
            ("nearest neighbor, honest length", quick, tour_length(quick, distances)),
            ("nearest neighbor, claiming the optimum", quick, key["length"]),
            ("a city left out", key["tour"][:-1], key["length"]),
        ]
        best = key["tour"]
        turned = list(reversed(best))
        turned = turned[turned.index(3) :] + turned[: turned.index(3)]
        submissions[0] = (submissions[0][0], turned, key["length"])
        for label, tour, claimed in submissions:
            judge(name, key, label, tour, claimed)
        path = picture(name, cities, best, quick, folder)
        print(f"\n  {DIM}picture (orange: nearest neighbor; dashed: a shortest tour): {path}{RESET}")
        Image.open(path).show()
    print(f"\n{DIM}Pictures in {folder}{RESET}\n")


if __name__ == "__main__":
    main()
