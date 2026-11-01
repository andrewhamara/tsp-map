"""Draws the bundled maps, ui/maps/map-NN.png, and writes their true cities to verifier/maps.py and,
for the page's pictures, ui/maps.js.

    uv run python -m plugin.tools_dev.make_maps

Maps 01 to 35 are random from fixed seeds, 5 cities on odd maps and 4 on even ones; 36 to 40 are
drawn by hand for boundary cases, 5 cities each; 41 is the six-city challenge map. Maps stay this small because RUSH Lab's model must
find and submit a tour within one 2,048-token reply, reasoning included: at 6 cities and more it
mostly ran out of that reply before submitting. Each image is checked before anything is written: read_map must
find exactly the cities drawn. Running it again writes the same files.
"""

from __future__ import annotations

import json
import random
from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw

from plugin.read_map import CITY, DOT, GRID, MAPS, PAPER, find_cities

ROOT = Path(__file__).resolve().parents[3]
TRUTH = ROOT / "verifier" / "maps.py"
PAGE = ROOT / "ui" / "maps.js"
WIDTH, HEIGHT = 480, 360
MARGIN = 24  # the fewest pixels from a city's center to the edge
APART = 40  # the fewest pixels between two random cities' centers
GRID_STEP = 40


def ring(count: int, radius: int, cx: int, cy: int) -> list[tuple[int, int]]:
    return [
        (round(cx + radius * cos(2 * pi * k / count)), round(cy + radius * sin(2 * pi * k / count)))
        for k in range(count)
    ]


# Boundary maps: each city's center (x, y).
BY_HAND = {
    # Five cities on one line: every shortest tour goes out and back, and several tie.
    36: [(60, 180), (150, 180), (240, 180), (330, 180), (420, 180)],
    # A square's corners and its center: the symmetry makes several shortest tours tie.
    37: [(140, 80), (340, 80), (140, 280), (340, 280), (240, 180)],
    # Five cities on a circle, not in reading order around it: the shortest tour goes around it.
    38: ring(5, 140, 240, 180),
    # Two clusters far apart: a shortest tour crosses between them exactly twice.
    39: [(60, 60), (130, 50), (90, 120), (380, 260), (430, 310)],
    # A plus sign: four arms around a center, so the center sits between any two neighboring arms and
    # several tours tie; arm to arm is a rounded diagonal.
    40: [(240, 80), (140, 180), (240, 180), (340, 180), (240, 280)],
    # map-41, the challenge map: six cities, one more than the others, laid out as a trap. From every
    # starting city, going to the nearest unvisited city gives a tour (672 from city 1) that no single
    # 2-opt swap improves, yet the shortest tour is 622, 8% shorter: the only one of 200,000 random
    # six-city maps searched with that property. RUSH Lab's model, within its 2,048-token reply, has
    # not finished a six-city map: it runs out of the reply while checking tours, before submitting.
    41: [(215, 128), (281, 210), (399, 218), (190, 225), (268, 282), (350, 319)],
}


def random_map(seed: int, count: int) -> list[tuple[int, int]]:
    rng = random.Random(seed)
    cities: list[tuple[int, int]] = []
    while len(cities) < count:
        x, y = rng.randint(MARGIN, WIDTH - MARGIN), rng.randint(MARGIN, HEIGHT - MARGIN)
        if all((x - a) ** 2 + (y - b) ** 2 >= APART**2 for a, b in cities):
            cities.append((x, y))
    return cities


def draw(cities: list[tuple[int, int]]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    pen = ImageDraw.Draw(image)
    for x in range(GRID_STEP, WIDTH, GRID_STEP):
        pen.line([(x, 0), (x, HEIGHT - 1)], fill=GRID)
    for y in range(GRID_STEP, HEIGHT, GRID_STEP):
        pen.line([(0, y), (WIDTH - 1, y)], fill=GRID)
    r = DOT // 2
    for x, y in cities:
        pen.ellipse((x - r, y - r, x + r, y + r), fill=CITY)
    return image


def main() -> None:
    maps = {}
    for number in range(1, 42):
        cities = BY_HAND.get(number) or random_map(2026_11 + number, 4 + number % 2)
        image = draw(cities)
        expected = sorted(cities, key=lambda city: (city[1], city[0]))
        found = find_cities(image)
        if found != expected:
            raise SystemExit(f"map-{number:02d}: read_map finds {found}, not the drawn {expected}")
        maps[f"map-{number:02d}"] = (image, expected)
    MAPS.mkdir(parents=True, exist_ok=True)
    for name, (image, _) in maps.items():
        image.save(MAPS / f"{name}.png", optimize=True)
    truth = [
        '"""Each bundled map\'s true cities, (x, y) in id order, as src/plugin/tools_dev/make_maps.py drew them.',
        'Generated: do not edit."""',
        "",
        f"WIDTH = {WIDTH}",
        f"HEIGHT = {HEIGHT}",
        "MAPS = {",
        *(f"    {name!r}: {tuple(cities)!r}," for name, (_, cities) in maps.items()),
        "}",
    ]
    TRUTH.write_text("\n".join(truth) + "\n")
    page = [
        "// Each map's cities, [x, y] in id order, as src/plugin/tools_dev/make_maps.py drew them, for",
        "// renderers.js to draw tours over the map. Generated: do not edit.",
        f"export const WIDTH = {WIDTH};",
        f"export const HEIGHT = {HEIGHT};",
        "export const MAPS = {",
        *(f'  "{name}": {json.dumps([list(city) for city in cities])},' for name, (_, cities) in maps.items()),
        "};",
    ]
    PAGE.write_text("\n".join(page) + "\n")
    print(f"wrote {len(maps)} maps to {MAPS}, {TRUTH} and {PAGE}")


if __name__ == "__main__":
    main()
