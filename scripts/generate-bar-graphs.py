import csv
import html
import math
from pathlib import Path


REPORTS_DIR = Path("reports")
SUMMARY_PATH = REPORTS_DIR / "summary.csv"
OUTPUT_DIR = REPORTS_DIR / "bar_graphs"

# Cenarios atuais
SCENARIOS = {
    "texto_300kb":  "Texto 300 KB",
    "texto_400kb":  "Texto 400 KB",
    "imagem_1mb":   "Imagem 1 MB",
    "hibrido_3pag": "Hibrido (3 paginas)",
}

# Usuarios dos testes
USERS = [152, 155, 159]

# --------------------------------------------------------------------------
# Metricas:  P95 (ms)  |  taxa de falha (%)  |  throughput (req/s)
# --------------------------------------------------------------------------
METRICS = {
    "95%": {
        "label": "P95 - Tempo de resposta (ms)",
        "suffix": "p95",
        "y_max": 1800,
    },
    "failure_rate": {
        "label": "Taxa de falha (%)",
        "suffix": "taxa_falha",
        "y_max": None,
    },
    "Requests/s": {
        "label": "Throughput (req/s)",
        "suffix": "throughput",
        "y_max": None,
    },
}

# Cores das barras por numero de instancias
INSTANCE_COLORS = ["#cfe0ef", "#f4dfc6", "#efc7c7"]


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_throughput_from_stats(scenario: str, instances: int, users: int) -> float:
    """Le o Requests/s da linha Aggregated do stats CSV individual."""
    filename = f"{scenario}_{instances}wp_{users}users_stats.csv"
    path = REPORTS_DIR / filename
    if not path.exists():
        return 0.0
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Name", "").strip().lower() == "aggregated":
                return as_float(row.get("Requests/s", 0))
    return 0.0


def load_rows():
    """Carrega summary.csv e enriquece com Requests/s dos stats individuais."""
    rows = {}
    with SUMMARY_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            scenario = row.get("scenario")
            if scenario not in SCENARIOS:
                continue
            instances = int(row["instances"])
            users = int(row["users"])
            if users not in USERS:
                continue
            total = as_float(row.get("Request Count", 0))
            failures = as_float(row.get("Failure Count", 0))
            rate = (failures / total * 100) if total > 0 else 0.0
            throughput = load_throughput_from_stats(scenario, instances, users)
            rows[(scenario, instances, users)] = {
                **row,
                "instances": instances,
                "users": users,
                "failure_rate": rate,
                "Requests/s": throughput,
            }
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
    if value >= 1000:
        return f"{value:.0f}"
    if value >= 100:
        return f"{value:.0f}"
    if value >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    if value >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.3f}".rstrip("0").rstrip(".")


def build_simple_bar_svg(title, x_label, y_label, labels, values, colors, output_path, fixed_y_max=None):
    """
    Grafico de barras simples (sem agrupamento).
    labels: lista de strings para o eixo X
    values: lista de floats correspondentes
    colors: lista de cores (uma por barra)
    """
    width = 720
    height = 500
    left = 90
    right = 60
    top = 70
    bottom = 80
    plot_width = width - left - right
    plot_height = height - top - bottom

    if fixed_y_max is not None:
        y_max = fixed_y_max
    else:
        y_max = nice_max(max(values) if any(v > 0 for v in values) else 1)

    n = len(labels)
    bar_gap = 40
    bar_width = (plot_width - bar_gap * (n + 1)) / n

    def y_pos(value):
        return top + plot_height - (min(value, y_max) / y_max * plot_height)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="34" text-anchor="middle" font-family="Arial" font-size="17" font-weight="700">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width + 10}" y2="{top + plot_height}" stroke="#111827" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left}" y2="{top - 14}" stroke="#111827" stroke-width="1.4"/>',
        f'<polygon points="{left + plot_width + 10},{top + plot_height} {left + plot_width + 3},{top + plot_height - 4} {left + plot_width + 3},{top + plot_height + 4}" fill="#111827"/>',
        f'<polygon points="{left},{top - 14} {left - 4},{top - 6} {left + 4},{top - 6}" fill="#111827"/>',
        f'<text x="{left + plot_width / 2}" y="{height - 22}" text-anchor="middle" font-family="Arial" font-size="14">{html.escape(x_label)}</text>',
        f'<text transform="translate(24 {top + plot_height / 2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="14">{html.escape(y_label)}</text>',
    ]

    # Linhas de grade e ticks do eixo Y
    for tick in range(1, 6):
        value = y_max * tick / 5
        y = y_pos(value)
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        svg.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial" font-size="12">{format_tick(value)}</text>')

    # Barras
    for i, (label, value, color) in enumerate(zip(labels, values, colors)):
        x = left + bar_gap * (i + 1) + bar_width * i
        y = y_pos(value)
        bar_h = top + plot_height - y

        svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_h:.1f}" fill="{color}" stroke="#333333" stroke-width="1.2"/>')

        # Valor acima da barra
        svg.append(f'<text x="{x + bar_width / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" font-family="Arial" font-size="13" font-weight="600" fill="#111827">{format_tick(value)}</text>')

        # Label no eixo X
        svg.append(f'<text x="{x + bar_width / 2:.1f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(label)}</text>')

    svg.append("</svg>")
    output_path.write_text("\n".join(svg), encoding="utf-8")


def get_metric_value(row, metric_key):
    if metric_key == "failure_rate":
        return row["failure_rate"]
    return as_float(row.get(metric_key, 0))


def main():
    rows = load_rows()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0

    # ======================================================================
    # 36 graficos: 4 cenarios × 3 usuarios × 3 metricas
    #
    #   Para cada combinacao (cenario, usuarios, metrica):
    #     X = numero de instancias (1, 2, 3)
    #     Y = valor da metrica
    #
    #   Pergunta respondida: "escalar instancias melhorou o desempenho?"
    # ======================================================================
    for scenario, scenario_label in SCENARIOS.items():
        for users in USERS:
            for metric_key, metric_info in METRICS.items():
                labels = []
                values = []
                colors = []

                for i, instances in enumerate((1, 2, 3)):
                    row = rows.get((scenario, instances, users))
                    inst_label = f"{instances} instancia" if instances == 1 else f"{instances} instancias"
                    labels.append(inst_label)
                    values.append(get_metric_value(row, metric_key) if row else 0.0)
                    colors.append(INSTANCE_COLORS[i])

                filename = f"{scenario}_{metric_info['suffix']}_{users}users.svg"
                build_simple_bar_svg(
                    title=f"{scenario_label} — {users} usuarios\n{metric_info['label']}",
                    x_label="Numero de instancias WordPress",
                    y_label=metric_info["label"],
                    labels=labels,
                    values=values,
                    colors=colors,
                    output_path=OUTPUT_DIR / filename,
                    fixed_y_max=metric_info["y_max"],
                )
                count += 1

    print(f"Graficos de barras gerados em {OUTPUT_DIR}")
    print(f"Total: {count} graficos")
    print()
    print("Estrutura: 4 cenarios x 3 usuarios x 3 metricas = 36")
    print("  Cada grafico: X = instancias (1, 2, 3), Y = metrica")
    print("  Metricas: P95 (ms) | Taxa de falha (%) | Throughput (req/s)")


if __name__ == "__main__":
    main()
