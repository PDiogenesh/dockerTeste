import csv
import html
import math
from collections import defaultdict
from pathlib import Path


SUMMARY_PATH = Path("reports") / "summary.csv"
OUTPUT_DIR = Path("reports") / "bar_graphs"

SCENARIOS = {
    "imagem_1mb": "Imagem 1 MB",
    "post_400kb": "Texto 400 KB",
    "imagem_300kb": "Imagem 300 KB",
}

METRICS = {
    "Average Response Time": {
        "label": "Tempo medio de resposta (s)",
        "suffix": "tempo_medio",
        "scale": 0.001,
    },
    "Requests/s": {
        "label": "Requisicoes por segundo",
        "suffix": "requisicoes_por_segundo",
        "scale": 1,
    },
    "Failure Count": {
        "label": "Quantidade de falhas",
        "suffix": "falhas",
        "scale": 1,
    },
    "95%": {
        "label": "Percentil 95 (s)",
        "suffix": "percentil_95",
        "scale": 0.001,
    },
    "99%": {
        "label": "Percentil 99 (s)",
        "suffix": "percentil_99",
        "scale": 0.001,
    },
}

INSTANCE_COLORS = {
    "1 instancia": "#cfe0ef",
    "2 instancias": "#f4dfc6",
    "3 instancias": "#efc7c7",
}

USER_COLORS = {
    "10 usuarios": "#d9ead3",
    "100 usuarios": "#d9e5e8",
    "1000 usuarios": "#fff0c6",
}


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_rows():
    with SUMMARY_PATH.open(newline="", encoding="utf-8") as handle:
        return [
            {
                **row,
                "instances": int(row["instances"]),
                "users": int(row["users"]),
            }
            for row in csv.DictReader(handle)
            if row.get("scenario") in SCENARIOS
        ]


def nice_max(value):
    if value <= 0:
        return 1
    power = 10 ** math.floor(math.log10(value))
    for multiplier in (1, 2, 5, 10):
        if value <= multiplier * power:
            return multiplier * power
    return value


def format_tick(value):
    if value == 0:
        return "0"
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    if value >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.3f}".rstrip("0").rstrip(".")


def build_grouped_bar_svg(title, x_label, y_label, groups, series, colors, output_path):
    width = 900
    height = 560
    left = 92
    right = 230
    top = 70
    bottom = 88
    plot_width = width - left - right
    plot_height = height - top - bottom

    values = [value for group in groups for value in series[group].values()]
    y_max = nice_max(max(values) if values else 1)

    group_count = len(groups)
    series_names = list(next(iter(series.values())).keys()) if series else []
    group_width = plot_width / group_count
    bar_gap = 8
    bar_width = min(44, (group_width - 34) / max(1, len(series_names)) - bar_gap)

    def y_pos(value):
        return top + plot_height - (value / y_max * plot_height)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width + 14}" y2="{top + plot_height}" stroke="#111827" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left}" y2="{top - 16}" stroke="#111827" stroke-width="1.4"/>',
        f'<polygon points="{left + plot_width + 14},{top + plot_height} {left + plot_width + 7},{top + plot_height - 4} {left + plot_width + 7},{top + plot_height + 4}" fill="#111827"/>',
        f'<polygon points="{left},{top - 16} {left - 4},{top - 8} {left + 4},{top - 8}" fill="#111827"/>',
        f'<text x="{left + plot_width / 2}" y="{height - 28}" text-anchor="middle" font-family="Arial" font-size="15">{html.escape(x_label)}</text>',
        f'<text transform="translate(28 {top + plot_height / 2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="15">{html.escape(y_label)}</text>',
    ]

    for tick in range(1, 6):
        value = y_max * tick / 5
        y = y_pos(value)
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        svg.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="12">{format_tick(value)}</text>')

    for group_index, group in enumerate(groups):
        center = left + group_width * group_index + group_width / 2
        bars_total_width = len(series_names) * bar_width + (len(series_names) - 1) * bar_gap
        first_x = center - bars_total_width / 2

        svg.append(f'<text x="{center:.1f}" y="{top + plot_height + 26}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(str(group))}</text>')

        for series_index, series_name in enumerate(series_names):
            value = series[group][series_name]
            x = first_x + series_index * (bar_width + bar_gap)
            y = y_pos(value)
            bar_height = top + plot_height - y
            svg.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" '
                f'fill="{colors[series_name]}" stroke="#333333" stroke-width="1"/>'
            )

    legend_x = left + plot_width + 36
    legend_y = top + 12
    for index, series_name in enumerate(series_names):
        y = legend_y + index * 28
        svg.append(f'<rect x="{legend_x}" y="{y - 13}" width="28" height="16" fill="{colors[series_name]}" stroke="#333333"/>')
        svg.append(f'<text x="{legend_x + 36}" y="{y}" font-family="Arial" font-size="14">{html.escape(series_name)}</text>')

    svg.append("</svg>")
    output_path.write_text("\n".join(svg), encoding="utf-8")


def rows_by_scenario(rows):
    scenarios = defaultdict(list)
    for row in rows:
        scenarios[row["scenario"]].append(row)
    return scenarios


def main():
    rows = load_rows()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for scenario, scenario_rows in rows_by_scenario(rows).items():
        scenario_label = SCENARIOS[scenario]
        lookup = {
            (row["instances"], row["users"]): row
            for row in scenario_rows
        }

        for metric_name, metric_info in METRICS.items():
            metric_label = metric_info["label"]
            scale = metric_info["scale"]

            by_users = {}
            for users in (10, 100, 1000):
                by_users[users] = {}
                for instances in (1, 2, 3):
                    value = as_float(lookup[(instances, users)][metric_name]) * scale
                    label = f"{instances} instancia" if instances == 1 else f"{instances} instancias"
                    by_users[users][label] = value

            build_grouped_bar_svg(
                title=f"{scenario_label} - {metric_label}",
                x_label="Numero de usuarios",
                y_label=metric_label,
                groups=[10, 100, 1000],
                series=by_users,
                colors=INSTANCE_COLORS,
                output_path=OUTPUT_DIR / f"{scenario}_{metric_info['suffix']}_usuarios_x_instancias.svg",
            )

            by_instances = {}
            for instances in (1, 2, 3):
                by_instances[instances] = {}
                for users in (10, 100, 1000):
                    value = as_float(lookup[(instances, users)][metric_name]) * scale
                    by_instances[instances][f"{users} usuarios"] = value

            build_grouped_bar_svg(
                title=f"{scenario_label} - {metric_label}",
                x_label="Numero de instancias",
                y_label=metric_label,
                groups=[1, 2, 3],
                series=by_instances,
                colors=USER_COLORS,
                output_path=OUTPUT_DIR / f"{scenario}_{metric_info['suffix']}_instancias_x_usuarios.svg",
            )

    print(f"Graficos de barras gerados em {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
