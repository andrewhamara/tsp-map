"""read_map: the cities it reports are the ones drawn on the map, and its distances are theirs."""

from .checks import map_problem, result, truth
from .maps import HEIGHT, MAPS, WIDTH


def verify_input(value):
    problem = map_problem(value.map)
    if problem:
        return result(False, problem)
    return result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    """``output_value``: a contract MapOutput, held to the map's true cities."""
    name = input_value.map
    if output_value.map != name:
        return result(False, f"the output is for {output_value.map!r}, not {name!r}")
    if (output_value.width, output_value.height) != (WIDTH, HEIGHT):
        return result(False, f"the image is {WIDTH}x{HEIGHT} px, not {output_value.width}x{output_value.height}")
    drawn = MAPS[name]
    found = [(city.id, city.x, city.y) for city in output_value.cities]
    expected = [(number, x, y) for number, (x, y) in enumerate(drawn, 1)]
    for item, true in zip(found, expected):
        if item != true:
            return result(False, f"city {true[0]} of {name} is reported at {item[1:]}, not {true[1:]}")
    if len(found) != len(expected):
        return result(False, f"{name} has {len(expected)} cities, not {len(found)}")
    distances, _ = truth(name)
    if [list(row) for row in output_value.distances] != distances:
        return result(False, f"the distance table of {name} is not its cities' rounded distances")
    return result(True, f"all {len(drawn)} cities of {name} and their distances are reported as drawn", cities=len(drawn))
