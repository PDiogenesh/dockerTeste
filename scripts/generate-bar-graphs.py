import csv
import html
import math
from collections import defaultdict
from pathlib import Path


SUMMARY_PATH = Path("reports") / "summary.csv"
OUTPUT_DIR = Path("reports") / "bar_graphs"

# Cenarios atuais (hibrido renomeado para hibrido_3gets)
SCENARIOS = {
    "texto_300kb":  "Texto 300 KB",
    "texto_400kb":  "Texto 400 KB",
    "imagem_1mb":   "Imagem 1 MB",
    "hibrido_3pag": "Hibrido (3 paginas)",
}

# Quantidades de usuarios usadas nos testes
USERS = [152, 155, 159]

# --------------------------------------------------------------------------
# Metricas solicitadas pelo professor:
#   Y = P95  OU  taxa de falha (%)
# --------------------------------------------------------------------------
METRICS = {
    "95%": {
        "label": "P95 - Tempo de resposta (ms)",
        "suffix": "p95",
        "scale": 1,         # ja esta em ms no CSV
        "y_max": 1800,      # eixo Y fixo em 1800 ms para comparar graficos
    },
    "failure_rate": {
        "label": "Taxa de falha (%)",
        "suffix": "taxa_falha",
        "scale": 1,
        "y_max": None,      # escala automatica
    },
}

INSTANCE_COLORS = {
    "1 instancia":  "#cfe0ef",
    "2 instancias": "#f4dfc6",
    "3 instancias": "#efc7c7",
}

USER_COLORS = {
    f"{u} usuarios": color
    for u, color in zip(USERS, ["#d9ead3", "#d9e5e8", "#fff0c6"])
}


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_rows():
    rows = []
    with SUMMARY_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("scenario") not in SCENARIOS:
                continue
            total = as_float(row.get("Request Count", 0))
            failures = as_float(row.get("Failure Count", 0))
            rate = (failures / total * 100) if total > 0 else 0.0
            rows.append({
                **row,
                "instances": int(row["instances"]),
                "users": int(row["users"]),
                "failure_rate": rate,
            })
    return rows


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


def build_grouped_bar_svg(title, x_label, y_label, groups, series, colors, output_path, fixed_y_max=None):
    width = 900
    height = 560
    left = 92
    right = 230
    top = 70
    bottom = 88
    plot_width = width - left - right
    plot_height = height - top - bottom

    values = [value for group in groups for value in series[group].values()]
    if fixed_y_max is not None:
        y_max = fixed_y_max
    else:
        y_max = nice_max(max(values) if values else 1)

    group_count = len(groups)
    series_names = list(next(iter(series.values())).keys()) if series else []
    group_width = plot_width / group_count
    bar_gap = 8
    bar_width = min(44, (group_width - 34) / max(1, len(series_names)) - bar_gap)

    def y_pos(value):
        return top + plot_height - (min(value, y_max) / y_max * plot_height)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-family="Arial" font-size="20" font-weight="700">{html.escape(title)}</text>',
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
            # Valor acima da barra
            label_y = y - 5
            svg.append(
                f'<text x="{x + bar_width / 2:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                f'font-family="Arial" font-size="10" fill="#333333">{format_tick(value)}</text>'
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

        for metric_key, metric_info in METRICS.items():
            metric_label = metric_info["label"]
            fixed_y_max = metric_info["y_max"]

            # --- Grafico 1: X = usuarios, barras por instancias ---
            by_users = {}
            for users in USERS:
                by_users[users] = {}
                for instances in (1, 2, 3):
                    row = lookup.get((instances, users))
                    if row is None:
                        continue
                    if metric_key == "failure_rate":
                        value = row["failure_rate"]
                    else:
                        value = as_float(row.get(metric_key, 0))
                    label = f"{instances} instancia" if instances == 1 else f"{instances} instancias"
                    by_users[users][label] = value

            build_grouped_bar_svg(
                title=f"{scenario_label} - {metric_label}",
                x_label="Numero de usuarios",
                y_label=metric_label,
                groups=USERS,
                series=by_users,
                colors=INSTANCE_COLORS,
                output_path=OUTPUT_DIR / f"{scenario}_{metric_info['suffix']}_usuarios_x_instancias.svg",
                fixed_y_max=fixed_y_max,
            )

            # --- Grafico 2: X = instancias, barras por usuarios ---
            user_colors_keys = [f"{u} usuarios" for u in USERS]
            user_colors = {k: c for k, c in zip(user_colors_keys, ["#d9ead3", "#d9e5e8", "#fff0c6"])}

            by_instances = {}
            for instances in (1, 2, 3):
                by_instances[instances] = {}
                for users in USERS:
                    row = lookup.get((instances, users))
                    if row is None:
                        continue
                    if metric_key == "failure_rate":
                        value = row["failure_rate"]
                    else:
                        value = as_float(row.get(metric_key, 0))
                    by_instances[instances][f"{users} usuarios"] = value

            build_grouped_bar_svg(
                title=f"{scenario_label} - {metric_label}",
                x_label="Numero de instancias",
                y_label=metric_label,
                groups=[1, 2, 3],
                series=by_instances,
                colors=user_colors,
                output_path=OUTPUT_DIR / f"{scenario}_{metric_info['suffix']}_instancias_x_usuarios.svg",
                fixed_y_max=fixed_y_max,
            )

    print(f"Graficos de barras gerados em {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
