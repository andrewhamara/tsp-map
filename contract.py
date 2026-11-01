"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    READ_MAP = "read_map"
    ANSWER_KEY = "answer_key"


class Task(Enum):
    SHORTEST_TOUR = "shortest-tour"
    READ_MAP = "read-map"


MAP = "A bundled map, map-01 to map-40"
CITY_ID = "A city's id: 1, 2, ... in reading order (top to bottom by y, then left to right by x)"
TOUR = (
    "The cities in visiting order, each exactly once, e.g. [1, 4, 2, 5, 3]; the tour returns from the last city "
    "to the first, so the first is not repeated at the end"
)


@dataclass
class MapInput(Output):
    map: Annotated[str, MAP]


@dataclass
class City(Output):
    id: Annotated[int, CITY_ID]
    x: Annotated[int, "The city's center, in pixels from the left edge"]
    y: Annotated[int, "The city's center, in pixels from the top edge"]


@dataclass
class MapOutput(Output):
    map: Annotated[str, MAP]
    width: Annotated[int, "The image's width in pixels"]
    height: Annotated[int, "The image's height in pixels"]
    cities: Annotated[list[City], "Every city found in the image, in id order"]
    distances: Annotated[
        list[list[int]],
        "The distance between every two cities: row i, column j is the distance from city i + 1 to city j + 1, "
        "the straight-line distance in pixels rounded to the nearest whole number",
    ]


@dataclass
class AnswerKeyOutput(Output):
    map: Annotated[str, MAP]
    cities: Annotated[int, "How many cities the map has"]
    tour: Annotated[list[int], "A shortest tour, starting at city 1"]
    length: Annotated[int, "The shortest tour's length: the sum of the distances along it, the return included"]


@dataclass
class TourOutput(Output):
    map: Annotated[str, MAP]
    tour: Annotated[list[int], TOUR]
    length: Annotated[
        int, "The tour's length: the sum of read_map's distances between consecutive cities, the return included"
    ]


TOOLS = {
    Tool.READ_MAP: (MapInput, MapOutput),
    Tool.ANSWER_KEY: (MapInput, AnswerKeyOutput),
}
TASKS = {
    Task.SHORTEST_TOUR: (MapInput, TourOutput),
    Task.READ_MAP: (MapInput, MapOutput),
}
