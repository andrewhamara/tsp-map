# TSP Map

A `nanoagent.plugin/v0001` plugin: the traveling salesman problem on a map
image, for a text-only agent. Each of 40 bundled maps shows 5 to 9 cities as
dots. The agent cannot see pixels, so its one tool, a deterministic map
reader, finds the cities in the image and measures the distance between every
two; the agent searches for the shortest round trip through all of them and
states its length. The verifier knows where every city was drawn, computes the
true optimum with Held-Karp, and checks the tour, the claimed length, and how
close the tour comes to the shortest.

## Tools

| Tool | Does | Code |
|---|---|---|
| `read_map` | Finds every city in a map's PNG from its pixels (each 13 px dot of the city color), with an id in reading order and its center, and the whole-number distance between every two cities | `src/plugin/read_map.py`, `src/plugin/tsp.py` |
| `answer_key` | The answer key: a shortest tour by Held-Karp over `read_map`'s distances | `src/plugin/answer.py`, `src/plugin/tsp.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `shortest-tour` | Finds a shortest closed tour of the map's cities and states its length | `agent`, with `read_map`; reference `answer_key` |
| `read-map` | Shows a map's picture and lists its cities and distances | `tool` (`read_map`) |

The page shows each result on the map's picture (`ui/renderers.js`):
`read-map` with every city numbered and the distance table, `shortest-tour`
with the agent's tour and, when it is not a shortest one, a shortest tour
dashed beside it, the lengths and the verdict's checks.

## The task

The input is a map, `map-01` to `map-40`. The agent submits `tour` (the city
ids in visiting order, each once; the return to the first city is implied)
and `length`, the tour's length as it computed it. The rules, in `tsp.py`:

- **Distances** are TSPLIB's EUC_2D: the straight-line distance between two
  cities' centers in pixels, rounded to the nearest whole number. They are
  computed exactly with integers (`isqrt`), never with floating point.
- **A tour's length** is the sum of the distances between consecutive
  cities, the return from the last to the first included.
- **Any shortest tour passes**, from any starting city, in either direction.

## Ground truth

`src/plugin/tools_dev/make_maps.py` draws every map, `ui/maps/map-NN.png`,
from fixed seeds (maps 01 to 35, seven each of 5, 6, 7, 8 and 9 cities) or by
hand (36 to 40, the boundary maps), and writes the cities it drew to
`verifier/maps.py` (and `ui/maps.js`, for the page). It refuses to write
anything unless `read_map` finds exactly the drawn cities in every image, and
the tests check that again. The verifier never reads an image and never
trusts a tool: it recomputes every distance from its own copy of the cities
and the optimum by Held-Karp, which the tests check against brute force over
every tour of every map.

| Map | Boundary it tests |
|---|---|
| `map-36` | Five cities on one line: every shortest tour goes out and back, and several tie |
| `map-37` | A square's corners and its center: symmetric ties |
| `map-38` | Nine cities on a circle: the shortest tour goes around it |
| `map-39` | Two clusters far apart: a shortest tour crosses between them exactly twice |
| `map-40` | A 3x3 grid: many tours tie, and one diagonal is needed |

## Constraints

`verifier/task.py` judges a `shortest-tour` submission against 6
constraints, in order. Each entry of `details.constraints` is
`{id, constraint, ok, expected, actual, message}`; `ok` is `null` when a
constraint it needs did not hold.

| # | id | What it checks |
|---|---|---|
| 1 | `map` | The map exists |
| 2 | `answer-key` | The answer key pinned a shortest tour of the map's true cities |
| 3 | `same-map` | The submission is for the task's map |
| 4 | `tour-complete` | The tour visits every city exactly once (no unknown, repeated or missing city) |
| 5 | `length-claimed` | The claimed length is the tour's real length |
| 6 | `shortest` | The tour is a shortest tour |

Valid only when all 6 hold, with score 1.0. Any failure of 1 to 4 scores 0.
Otherwise the score is the shortest length over the tour's length (a tour
10% too long scores about 0.91), halved when the claimed length is wrong, and
at most 0.99. Each tool call is checked too: `read_map`'s cities and
distances must be exactly the map's, and `answer_key`'s tour must be a
shortest one.

## Limitations

- **The agent never sees pixels.** It tests combinatorial search over a perceived map, not perception; the reader works only on these flat, synthetic maps.
- **Small maps.** At most 9 cities, so that Held-Karp, and brute force in the tests, stay instant. An agent that could enumerate all 20,160 tours of 9 cities would solve every map.
- **A fixed set of 40 maps.** An agent could in principle memorize them; new seeds make new maps.
- **Rounded distances.** Distances are whole numbers, so the optimum is for the rounded table, as in TSPLIB, not for exact Euclidean lengths.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions (no network), tools, tasks and the agent's instructions
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml   # pillow reads the maps' PNGs
├── uv.lock
├── .gitignore
├── .env             # needed environment variable names (none here)
├── src/plugin/      # the MCP server (__main__.py), read_map.py, answer.py, tsp.py (the rules),
│                    #   and tools_dev/ (make_maps.py draws the maps; demo.py shows a few verdicts)
├── tests/           # the reader, the rules against brute force, the verifier and scripted agents
├── ui/              # maps/ (the 40 PNGs, which read_map reads and the page shows), maps.js (their
│                    #   cities, for drawing tours) and renderers.js/.css (results on the map)
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier: maps.py (the truth), tsp.py (a copy of the rules),
                     #   one module per tool, and task.py for shortest-tour
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run python -m plugin.tools_dev.demo        # a few submissions and their verdicts, with pictures
uv run python -m plugin.tools_dev.make_maps   # redraws the maps; the same files each time
```

NanoAgent passes the folder the plugin may write to as `NANOAGENT_WORKSPACE`;
this plugin writes nothing there.
