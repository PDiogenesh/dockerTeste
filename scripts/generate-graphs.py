import csv
import html
import math
import re
from collections import defaultdict
from pathlib import Path


REPORTS_DIR = Path("reports")
GRAPHS_DIR = REPORTS_DIR / "graphs"

SCENARIO_LABELS = {
    "imagem_1mb": "Imagem 1 MB",
    "post_400kb": "Post 400 KB",
    "imagem_300kb": "Imagem 300 KB",
}

METRICS = {
    "Average Response Time": "Tempo medio de resposta (ms)",
    "Requests/s": "Requisicoes por segundo",
    "Failure Count": "Falhas",
    "95%": "Percentil 95 (ms)",
    "99%": "Percentil 99 (ms)",
}

COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c"]
FILENAME_RE = re.compile(r"^(?P<scenario>.+)_(?P<instances>[123])wp_(?P<users>\d+)users_stats\.csv$")


def as_float(value):
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def load_results():
    rows = []
    for path in REPORTS_DIR.glob("*_stats.csv"):
        match = FILENAME_RE.match(path.name)
        if not match:
            continue

        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            aggregate = None
            for row in reader:
                if row.get("Name") == "Aggregated":
                    aggregate = row
                    break

        if not aggregate:
            continue

        scenario = match.group("scenario")
        rows.append(
            {
                "scenario": scenario,
                "scenario_label": SCENARIO_LABELS.get(scenario, scenario),
                "instances": int(match.group("instances")),
                "users": int(match.group("users")),
                **{metric: as_float(aggregate.get(metric)) for metric in METRICS},
            }
        )

    return rows


def nice_max(value):
    if value <= 0:
        return 1
    power = 10 ** math.floor(math.log10(value))
    for multiplier in (1, 2, 5, 10):
        if value <= multiplier * power:
            return multiplier * power
    return value


def make_svg(title, x_label, y_label, series, output_path):
    width, height = 920, 560
    left, right, top, bottom = 88, 32, 58, 78
    plot_w = width - left - right
    plot_h = height - top - bottom

    xs = sorted({point[0] for points in series.values() for point in points})
    ys = [point[1] for points in series.values() for point in points]
    y_max = nice_max(max(ys) if ys else 1)

    def x_pos(x):
        if len(xs) == 1:
            return left + plot_w / 2
        return left + xs.index(x) * (plot_w / (len(xs) - 1))

    def y_pos(y):
        return top + plot_h - (y / y_max * plot_h)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="30" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{html.escape(title)}</text>',
        f'<text x="{width / 2}" y="{height - 22}" text-anchor="middle" font-family="Arial" font-size="15">{html.escape(x_label)}</text>',
        f'<text transform="translate(24 {height / 2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="15">{html.escape(y_label)}</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#111827" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#111827" stroke-width="1.4"/>',
    ]

    for step in range(6):
        y_value = y_max * step / 5
        y = y_pos(y_value)
        svg.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb"/>')
        svg.append(f'<text x="{left - 10}" y="{y + 5}" text-anchor="end" font-family="Arial" font-size="12">{y_value:.0f}</text>')

    for x in xs:
        xp = x_pos(x)
        svg.append(f'<line x1="{xp}" y1="{top + plot_h}" x2="{xp}" y2="{top + plot_h + 6}" stroke="#111827"/>')
        svg.append(f'<text x="{xp}" y="{top + plot_h + 24}" text-anchor="middle" font-family="Arial" font-size="12">{x}</text>')

    for index, (label, points) in enumerate(series.items()):
        color = COLORS[index % len(COLORS)]
        sorted_points = sorted(points)
        coords = " ".join(f'{x_pos(x):.1f},{y_pos(y):.1f}' for x, y in sorted_points)
        svg.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{coords}"/>')
        for x, y in sorted_points:
            svg.append(f'<circle cx="{x_pos(x):.1f}" cy="{y_pos(y):.1f}" r="4" fill="{color}"/>')
        legend_y = top + index * 24
        svg.append(f'<rect x="{left + plot_w - 170}" y="{legend_y - 12}" width="14" height="14" fill="{color}"/>')
        svg.append(f'<text x="{left + plot_w - 150}" y="{legend_y}" font-family="Arial" font-size="13">{html.escape(label)}</text>')

    svg.append("</svg>")
    output_path.write_text("\n".join(svg), encoding="utf-8")


def write_summary(rows):
    summary_path = REPORTS_DIR / "summary.csv"
    fieldnames = ["scenario", "instances", "users", *METRICS.keys()]
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["scenario"], item["instances"], item["users"])):
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main():
    rows = load_results()
    if not rows:
        raise SystemExit("Nenhum arquivo *_stats.csv encontrado em reports/. Rode os testes primeiro.")

    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    write_summary(rows)

    by_scenario = defaultdict(list)
    for row in rows:
        by_scenario[row["scenario"]].append(row)

    for scenario, scenario_rows in by_scenario.items():
        scenario_label = scenario_rows[0]["scenario_label"]
        for metric, metric_label in METRICS.items():
            by_instances = defaultdict(list)
            by_users = defaultdict(list)
            for row in scenario_rows:
                by_instances[f'{row["instances"]} WP'].append((row["users"], row[metric]))
                by_users[f'{row["users"]} usuarios'].append((row["instances"], row[metric]))

            safe_metric = metric.lower().replace("/", "s").replace("%", "pct").replace(" ", "_")
            make_svg(
                f"{scenario_label} - {metric_label} por usuarios",
                "Usuarios simultaneos",
                metric_label,
                dict(sorted(by_instances.items())),
                GRAPHS_DIR / f"{scenario}_{safe_metric}_por_usuarios.svg",
            )
            make_svg(
                f"{scenario_label} - {metric_label} por instancias",
                "Instancias WordPress",
                metric_label,
                dict(sorted(by_users.items())),
                GRAPHS_DIR / f"{scenario}_{safe_metric}_por_instancias.svg",
            )

    print(f"Graficos gerados em {GRAPHS_DIR}")
    print(f"Resumo gerado em {REPORTS_DIR / 'summary.csv'}")


if __name__ == "__main__":
    main()
