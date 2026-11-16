
#!/usr/bin/env python3

import datetime as dt
import html
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contribution-heatmap.svg"

PALETTE = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
    "#69f0a0",
]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL = 30
TOP_LABEL = 20
TITLEBAR = 30

BG = "#0a0e14"
BG2 = "#0d1420"
FRAME = "#1f6feb"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"
BAR = "#26a641"
BAR_HIGHLIGHT = "#39d353"


def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def build_grid(days):
    first = dt.date.fromisoformat(days[0]["date"])

    # Sunday is the first row.
    leading = (first.weekday() + 1) % 7

    grid = []
    column = [None] * leading

    for item in days:
        date = dt.date.fromisoformat(item["date"])
        weekday = (date.weekday() + 1) % 7

        while len(column) < weekday:
            column.append(None)

        column.append((
            item["date"],
            item["count"],
            level_for(item["count"]),
        ))

        if len(column) == 7:
            grid.append(column)
            column = []

    if column:
        column.extend([None] * (7 - len(column)))
        grid.append(column)

    return grid


def build_monthly_data(days):
    """
    Include every month in the fetched date range,
    including months with zero contributions.
    """
    totals = defaultdict(int)

    for day in days:
        month = day["date"][:7]
        totals[month] += day["count"]

    first = dt.date.fromisoformat(days[0]["date"])
    last = dt.date.fromisoformat(days[-1]["date"])

    months = []
    current = first.replace(day=1)
    end = last.replace(day=1)

    while current <= end:
        key = current.strftime("%Y-%m")

        months.append({
            "label": current.strftime("%b"),
            "key": key,
            "total": totals[key],
        })

        if current.month == 12:
            current = current.replace(
                year=current.year + 1,
                month=1,
            )
        else:
            current = current.replace(
                month=current.month + 1,
            )

    return months


def build_yearly_data(days):
    totals = defaultdict(int)

    for day in days:
        year = dt.date.fromisoformat(day["date"]).year
        totals[year] += day["count"]

    return [
        {
            "year": year,
            "total": totals[year],
        }
        for year in sorted(totals)
    ]


def render_monthly_chart(months, width, top):
    """
    Render monthly contribution bars.
    """
    parts = []

    chart_width = width - PAD * 2
    chart_height = 105

    bar_gap = 12
    bar_width = (
        chart_width - bar_gap * (len(months) - 1)
    ) / max(len(months), 1)

    max_value = max(
        (month["total"] for month in months),
        default=0,
    )

    max_value = max(max_value, 1)

    baseline = top + chart_height

    parts.append(
        f'<text x="{PAD}" y="{top - 20}" '
        f'fill="{TEXT}" font-size="14" font-weight="700">'
        f'MONTHLY CONTRIBUTIONS</text>'
    )

    parts.append(
        f'<text x="{width - PAD}" y="{top - 20}" '
        f'text-anchor="end" fill="{MUTED}" font-size="10">'
        f'Last 12 months · Hover over bars for details'
        f'</text>'
    )

    parts.append(
        f'<line x1="{PAD}" y1="{baseline}" '
        f'x2="{width - PAD}" y2="{baseline}" '
        f'stroke="{FRAME}" stroke-opacity="0.4"/>'
    )

    for index, month in enumerate(months):
        x = PAD + index * (bar_width + bar_gap)

        bar_height = (
            month["total"] / max_value
        ) * chart_height

        bar_height = max(bar_height, 1) if month["total"] else 0

        y = baseline - bar_height

        color = (
            BAR_HIGHLIGHT
            if month["total"] == max_value
            else BAR
        )

        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" '
            f'width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}" '
            f'rx="3" fill="{color}">'
            f'<title>{month["key"]}: '
            f'{month["total"]:,} contributions</title>'
            f'</rect>'
        )

        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" '
            f'y="{baseline + 16}" '
            f'text-anchor="middle" '
            f'fill="{MUTED}" font-size="9">'
            f'{html.escape(month["label"])}</text>'
        )

    return parts


def render_yearly_chart(years, width, top):
    """
    Render calendar-year totals for the fetched date range.
    """
    parts = []

    chart_width = width - PAD * 2
    chart_height = 100

    max_value = max(
        (item["total"] for item in years),
        default=0,
    )
    max_value = max(max_value, 1)

    baseline = top + chart_height

    parts.append(
        f'<text x="{PAD}" y="{top - 20}" '
        f'fill="{TEXT}" font-size="14" font-weight="700">'
        f'YEARLY CONTRIBUTIONS</text>'
    )

    parts.append(
        f'<text x="{width - PAD}" y="{top - 20}" '
        f'text-anchor="end" fill="{MUTED}" font-size="10">'
        f'Calendar years · totals within fetched range'
        f'</text>'
    )

    parts.append(
        f'<line x1="{PAD}" y1="{baseline}" '
        f'x2="{width - PAD}" y2="{baseline}" '
        f'stroke="{FRAME}" stroke-opacity="0.4"/>'
    )

    count = len(years)

    if count == 0:
        return parts

    group_width = chart_width / count
    bar_width = min(75, group_width * 0.45)

    for index, item in enumerate(years):
        center = PAD + index * group_width + group_width / 2

        bar_height = (
            item["total"] / max_value
        ) * chart_height

        bar_height = max(bar_height, 1) if item["total"] else 0

        x = center - bar_width / 2
        y = baseline - bar_height

        color = (
            BAR_HIGHLIGHT
            if item["total"] == max_value
            else BAR
        )

        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" '
            f'width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}" '
            f'rx="4" fill="{color}">'
            f'<title>{item["year"]}: '
            f'{item["total"]:,} contributions '
            f'within fetched range</title>'
            f'</rect>'
        )

        parts.append(
            f'<text x="{center:.2f}" '
            f'y="{baseline + 17}" '
            f'text-anchor="middle" '
            f'fill="{MUTED}" font-size="11">'
            f'{item["year"]}</text>'
        )

    return parts


def render(data):
    days = data["days"]
    grid = build_grid(days)

    monthly = build_monthly_data(days)
    yearly = build_yearly_data(days)

    columns = len(grid)
    art_width = columns * STEP
    art_height = 7 * STEP

    width = PAD + LEFT_LABEL + art_width + PAD

    # Layout sections.
    heatmap_top = TITLEBAR + TOP_LABEL
    heatmap_bottom = heatmap_top + art_height

    legend_top = heatmap_bottom + 6
    monthly_top = legend_top + 55
    yearly_top = monthly_top + 160
    stats_top = yearly_top + 155

    height = stats_top + 85

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="auto" '
        f'viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="GitHub contribution heatmap, '
        f'monthly and yearly contribution charts" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',

        """
        <style>
          @keyframes cell-in {
            from {
              opacity: 0;
              transform: translateY(-6px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          .cell {
            opacity: 0;
            animation: cell-in 0.42s cubic-bezier(.2,.8,.2,1) both;
          }

          @media (prefers-reduced-motion: reduce) {
            .cell {
              animation: none !important;
              opacity: 1 !important;
            }
          }
        </style>
        """,

        f"""
        <defs>
          <linearGradient id="background" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{BG2}"/>
            <stop offset="100%" stop-color="{BG}"/>
          </linearGradient>
        </defs>

        <rect width="{width}" height="{height}"
              rx="12" fill="url(#background)"/>

        <rect x="0.5" y="0.5" width="{width-1}" height="{height-1}"
              rx="12" fill="none" stroke="{FRAME}"
              stroke-opacity="0.55"/>

        <line x1="0" y1="{TITLEBAR}" x2="{width}" y2="{TITLEBAR}"
              stroke="{FRAME}" stroke-opacity="0.35"/>
        """,
    ]

    # Terminal controls.
    for index, color in enumerate(
        ["#ff5f56", "#ffbd2e", "#27c93f"]
    ):
        parts.append(
            f'<circle cx="{PAD + index * 16}" '
            f'cy="{TITLEBAR / 2}" r="5" fill="{color}"/>'
        )

    username = html.escape(data["username"])

    parts.append(
        f'<text x="{width / 2}" y="{TITLEBAR / 2 + 4}" '
        f'fill="{MUTED}" font-size="12" text-anchor="middle">'
        f'{username}@github: ~/contributions --analytics</text>'
    )

    grid_left = PAD + LEFT_LABEL

    # Month labels on heatmap.
    seen_months = set()

    for column_index, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue

            date = dt.date.fromisoformat(cell[0])
            key = (date.year, date.month)

            if key not in seen_months and date.day <= 7:
                seen_months.add(key)

                parts.append(
                    f'<text x="{grid_left + column_index * STEP}" '
                    f'y="{TITLEBAR + 14}" fill="{MUTED}" '
                    f'font-size="10">{date.strftime("%b")}</text>'
                )
                break

    # Weekday labels.
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = heatmap_top + row * STEP + CELL * 0.78

        parts.append(
            f'<text x="{PAD}" y="{y:.1f}" '
            f'fill="{MUTED}" font-size="9">{label}</text>'
        )

    # Contribution heatmap cells.
    for column_index, column in enumerate(grid):
        for row_index, cell in enumerate(column):
            if cell is None:
                continue

            date, count, level = cell

            x = grid_left + column_index * STEP
            y = heatmap_top + row_index * STEP

            delay = column_index * 0.018 + row_index * 0.045
            plural = "s" if count != 1 else ""

            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" '
                f'width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[level]}" '
                f'style="animation-delay:{delay:.3f}s">'
                f'<title>{date}: {count} contribution{plural}</title>'
                f'</rect>'
            )

    # Heatmap legend.
    legend_y = legend_top
    legend_x = width - PAD - (
        len(PALETTE) * (CELL - 1) + 70
    )

    parts.append(
        f'<text x="{legend_x}" y="{legend_y + CELL * 0.8:.1f}" '
        f'fill="{MUTED}" font-size="10" text-anchor="end">Less</text>'
    )

    x = legend_x + 8

    for color in PALETTE:
        parts.append(
            f'<rect x="{x}" y="{legend_y}" '
            f'width="{CELL-1}" height="{CELL-1}" '
            f'rx="2.2" fill="{color}"/>'
        )
        x += CELL

    parts.append(
        f'<text x="{x + 4}" y="{legend_y + CELL * 0.8:.1f}" '
        f'fill="{MUTED}" font-size="10">More</text>'
    )

    # Monthly chart.
    parts.extend(
        render_monthly_chart(monthly, width, monthly_top)
    )

    # Yearly chart.
    parts.extend(
        render_yearly_chart(yearly, width, yearly_top)
    )

    # Statistics footer.
    separator_y = stats_top

    parts.append(
        f'<line x1="0" y1="{separator_y}" x2="{width}" '
        f'y2="{separator_y}" stroke="{FRAME}" stroke-opacity="0.25"/>'
    )

    line_y = separator_y + 24

    total = data["total_contributions"]
    current = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    best = data["best_day"]
    date_range = data["range"]

    parts.append(
        f'<text x="{PAD}" y="{line_y}" font-size="13" fill="{GREEN}">'
        f'<tspan font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year</tspan>'
        f'</text>'
    )

    parts.append(
        f'<text x="{width-PAD}" y="{line_y}" font-size="12" '
        f'fill="{MUTED}" text-anchor="end">'
        f'{date_range["start"]} &#8594; {date_range["end"]}'
        f'</text>'
    )

    line_y += 24

    parts.append(
        f'<text x="{PAD}" y="{line_y}" font-size="13" fill="{MUTED}">'
        f'current streak '
        f'<tspan fill="{ACCENT}" font-weight="700">{current} days</tspan>'
        f'<tspan fill="{MUTED}"> · longest </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{longest} days</tspan>'
        f'</text>'
    )

    parts.append(
        f'<text x="{width-PAD}" y="{line_y}" font-size="12" '
        f'fill="{MUTED}" text-anchor="end">'
        f'best day <tspan fill="{GOLD}" font-weight="700">'
        f'{best["count"]}</tspan> on {best["date"]}'
        f'</text>'
    )

    parts.append("</svg>")

    return "\n".join(parts)


def main():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"{INPUT} not found. Run fetch_contributions.py first."
        )

    data = json.loads(INPUT.read_text(encoding="utf-8"))

    if not data.get("days"):
        raise ValueError("Contribution dataset contains no days.")

    svg = render(data)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

    print(f"Generated: {OUTPUT}")
    print(f"SVG size: {len(svg):,} bytes")
    print(f"Monthly bars: {len(build_monthly_data(data['days']))}")
    print(f"Yearly bars: {len(build_yearly_data(data['days']))}")


if __name__ == "__main__":
    main()
