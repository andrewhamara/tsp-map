from __future__ import annotations

from pathlib import Path

import pytest
from oracle import distance
from PIL import Image, ImageDraw

from contract import MapInput
from plugin import read_map
from plugin.read_map import CITY, PAPER, find_cities
from verifier.maps import MAPS


@pytest.mark.parametrize("name", sorted(MAPS))
def test_finds_exactly_the_cities_each_map_was_drawn_with(tmp_path: Path, name: str) -> None:
    found = read_map(MapInput(map=name), tmp_path)
    assert (found.width, found.height) == (480, 360)
    assert [(city.id, city.x, city.y) for city in found.cities] == [(n, x, y) for n, (x, y) in enumerate(MAPS[name], 1)]
    cities = MAPS[name]
    assert found.distances == [[distance(a, b) for b in cities] for a in cities]


@pytest.mark.parametrize("name", ["map-00", "map-41", "map-1", "../map-01", ""])
def test_refuses_a_map_that_is_not_bundled(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="no map"):
        read_map(MapInput(map=name), tmp_path)


def test_refuses_a_color_that_is_not_part_of_a_map() -> None:
    image = Image.new("RGB", (100, 100), PAPER)
    image.putpixel((50, 50), (255, 0, 0))
    with pytest.raises(ValueError, match="not part of a map"):
        find_cities(image)


def test_refuses_a_region_that_is_not_a_city_dot() -> None:
    image = Image.new("RGB", (100, 100), PAPER)
    ImageDraw.Draw(image).rectangle((10, 10, 30, 22), fill=CITY)
    with pytest.raises(ValueError, match="not a city dot"):
        find_cities(image)


def test_the_page_draws_the_cities_the_maps_were_drawn_with() -> None:
    import json
    import re

    text = (Path(__file__).resolve().parents[1] / "ui" / "maps.js").read_text()
    body = text.split("export const MAPS = ", 1)[1].rstrip().removesuffix(";")
    page = json.loads(re.sub(r",(\s*})", r"\1", body))
    assert page == {name: [list(city) for city in cities] for name, cities in MAPS.items()}
