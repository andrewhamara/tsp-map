"""read_map: every city on a bundled map, found in the image's pixels, and the distances between them.

A map is a paper-colored background with a faint grid; a city is a 13 px dot of the city color.
Each 4-connected region of that color is one city, its center the middle of its box. Ids follow
reading order: top to bottom by y, then left to right by x. Any pixel of another color, or a
region that is not a 13 px dot, is refused: the maps hold nothing else.
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

from PIL import Image

from contract import City, MapInput, MapOutput
from plugin.tsp import table

# The maps live in ui/maps/, where the plugin's page shows them too.
MAPS = Path(__file__).resolve().parents[2] / "ui" / "maps"
MAP_ID = re.compile(r"^map-\d{2}$")
PAPER = (246, 241, 228)
GRID = (226, 218, 198)
CITY = (34, 74, 120)
DOT = 13  # a city's width and height in pixels


def map_path(name: str) -> Path:
    path = MAPS / f"{name}.png"
    if not MAP_ID.fullmatch(name) or not path.is_file():
        raise ValueError(f"no map {name!r}: the maps are map-01 to map-41")
    return path


def find_cities(image: Image.Image) -> list[tuple[int, int]]:
    """Each city's center (x, y), in reading order."""
    image = image.convert("RGB")
    width, height = image.size
    pixels = image.load()
    seen = [[False] * width for _ in range(height)]
    centers = []
    for top in range(height):
        for left in range(width):
            color = pixels[left, top]
            if color in (PAPER, GRID) or seen[top][left]:
                continue
            if color != CITY:
                raise ValueError(f"the color {color} at {(left, top)} is not part of a map")
            seen[top][left] = True
            stack, region = [(left, top)], []
            while stack:
                x, y = stack.pop()
                region.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx] and pixels[nx, ny] == CITY:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            xs, ys = [x for x, _ in region], [y for _, y in region]
            box = (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
            if box != (DOT, DOT) or not 0.7 < len(region) / DOT**2 < 0.9:
                raise ValueError(f"a {box[0]}x{box[1]} px region at {region[0]} is not a city dot")
            centers.append(((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2))
    return sorted(centers, key=lambda center: (center[1], center[0]))


@cache
def _read(name: str) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    """The map's image size and its cities' centers, read once: the bundled images never change."""
    with Image.open(map_path(name)) as image:
        return image.width, image.height, tuple(find_cities(image))


def read_map(given: MapInput, workspace: Path) -> MapOutput:
    """Every city on the map, found in its pixels, and every pair's distance."""
    width, height, centers = _read(given.map)
    cities = [City(id=number, x=x, y=y) for number, (x, y) in enumerate(centers, 1)]
    return MapOutput(map=given.map, width=width, height=height, cities=cities, distances=table(list(centers)))
