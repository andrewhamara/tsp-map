// How this plugin's page draws its tasks' outputs: the map's picture (ui/maps/) with an SVG drawn
// over it as a data: image: each city's number, and for a tour, the agent's tour and, when it is not
// a shortest one, a shortest tour dashed beside it; then the lengths and the verdict's checks.
import { disclosure, h, plural } from "./kit/components.js";
import { HEIGHT, MAPS, WIDTH } from "./maps.js";

const INK = "#224a78";
const TOUR = "#f08c00";
const BEST = "#5c6b7a";

/** An SVG of the map's size, as an image source. */
const svg = (parts) =>
  `data:image/svg+xml,${encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}">${parts.join("")}</svg>`,
  )}`;

const loop = (cities, tour, stroke, extra) => {
  const points = tour.filter((id) => cities[id - 1]).map((id) => cities[id - 1].join(","));
  return points.length > 1
    ? `<polygon points="${points.join(" ")}" fill="none" stroke="${stroke}" stroke-linejoin="round" ${extra}/>`
    : "";
};

const dots = (cities) => cities.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="6.5" fill="${INK}"/>`).join("");

const labels = (cities) =>
  cities
    .map(
      ([x, y], i) =>
        `<text x="${x + 9}" y="${y - 7}" font-family="sans-serif" font-size="14" font-weight="700" fill="${INK}" ` +
        `stroke="#f6f1e4" stroke-width="4" paint-order="stroke">${i + 1}</text>`,
    )
    .join("");

/** The map's picture with `overlay` (SVG parts) over it. */
const picture = (name, overlay) =>
  h(
    "div",
    { class: "map-frame" },
    h("img", { class: "map-img", src: `maps/${name}.png`, alt: `The map ${name}`, width: WIDTH, height: HEIGHT }),
    h("img", { class: "map-overlay", src: svg(overlay), alt: "", width: WIDTH, height: HEIGHT }),
  );

const legend = (items) =>
  h(
    "p",
    { class: "map-legend muted" },
    items.map(([tone, text]) => h("span", { class: "map-key" }, h("span", { class: `map-swatch ${tone}` }), text)),
  );

const MARKS = { true: ["✓", "ok"], false: ["✗", "bad"], null: ["·", "skipped"] };

/** The verdict's checks, each with its mark and, when it failed or was skipped, why. */
const checks = (constraints) =>
  h(
    "ol",
    { class: "map-checks" },
    constraints.map(({ id, constraint, ok, message }) => {
      const [mark, tone] = MARKS[String(ok)];
      return h(
        "li",
        { class: `map-check ${tone}` },
        h("span", { class: "map-mark", text: mark }),
        h("span", {}, h("code", { text: id }), ` ${constraint}`, message ? h("span", { class: "map-why", text: message }) : null),
      );
    }),
  );

const distanceTable = (distances) =>
  h(
    "table",
    { class: "map-table" },
    h("thead", {}, h("tr", {}, h("th", { text: "" }), distances.map((_, j) => h("th", { text: String(j + 1) })))),
    h(
      "tbody",
      {},
      distances.map((row, i) => h("tr", {}, h("th", { text: String(i + 1) }), row.map((d) => h("td", { text: String(d) })))),
    ),
  );

const route = (tour) => (tour.length ? [...tour, tour[0]].join(" → ") : "no cities");

export default {
  MapOutput: ({ map, cities, distances }) => {
    const points = cities.map(({ x, y }) => [x, y]);
    return h(
      "div",
      { class: "map-card" },
      h("p", { class: "map-title" }, h("strong", { text: map }), ` · ${plural(cities.length, "city", "cities")}`),
      picture(map, [labels(points)]),
      disclosure({ summary: "Distances between cities", className: "map-distances" }, distanceTable(distances)),
    );
  },
  TourOutput: ({ map, tour, length }, { verdict }) => {
    const cities = MAPS[map] || [];
    const details = verdict.details || {};
    const best = details.expected || null;
    const shortest = best && details.length !== null && details.length !== undefined && details.length !== best.length;
    const overlay = [
      shortest ? loop(cities, best.tour, BEST, 'stroke-width="2.5" stroke-dasharray="7 6"') : "",
      loop(cities, tour, TOUR, 'stroke-width="3.5"'),
      dots(cities),
      labels(cities),
    ];
    const keys = [["tour", "the agent's tour"]];
    if (shortest) keys.push(["best", "a shortest tour"]);
    const real = details.length;
    return h(
      "div",
      { class: "map-card" },
      h("p", { class: "map-route" }, h("strong", { text: route(tour) })),
      h(
        "p",
        { class: "map-lengths muted" },
        real !== null && real !== undefined ? `Length ${real}` : "Not a complete tour",
        length !== real ? ` (claimed ${length})` : "",
        best ? ` · shortest ${best.length}` : "",
      ),
      cities.length ? picture(map, overlay) : h("p", { class: "muted", text: `No picture for ${map}.` }),
      legend(keys),
      details.constraints ? checks(details.constraints) : null,
    );
  },
};
