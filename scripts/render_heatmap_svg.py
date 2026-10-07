"""Render data/contributions.json as an animated terminal-style heatmap -> contrib-heatmap.svg."""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
WEEKS, DAYS = 53, 7
BOX, GAP = 13, 3
STEP = BOX + GAP
LEFT, TOP = 36, 30
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def levels_for(counts):
    """Map counts to 0..5 using percentiles of the non-zero days."""
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return lambda c: 0

    def pct(p):
        return nz[min(len(nz) - 1, int(p * (len(nz) - 1)))]

    cuts = [pct(0.25), pct(0.5), pct(0.75), pct(0.9)]

    def level(c):
        if c <= 0:
            return 0
        return 1 + sum(c > t for t in cuts)

    return level


def build_grid(days):
    """Return 53x7 grid of (date, count) ending at the last day, Sunday-first rows."""
    by_date = {d["date"]: d["count"] for d in days}
    last = date.fromisoformat(days[-1]["date"]) if days else date.today()
    last_col_start = last - timedelta(days=(last.weekday() + 1) % 7)  # Sunday of last week
    start = last_col_start - timedelta(weeks=WEEKS - 1)
    grid = []
    for w in range(WEEKS):
        col = []
        for r in range(DAYS):
            d = start + timedelta(weeks=w, days=r)
            col.append((d, by_date.get(d.isoformat(), 0) if d <= last else None))
        grid.append(col)
    return grid


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]
    grid = build_grid(days)
    level = levels_for([c for col in grid for _, c in col if c])

    width = LEFT + WEEKS * STEP + 14
    height = TOP + DAYS * STEP + 52
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Contribution heatmap">',
        "<style>",
        f"text{{font-family:{FONT};fill:#8b949e;font-size:10px}}",
        # Visible by default; the animation only plays on top (fill-mode backwards).
        ".c{transform-box:fill-box;transform-origin:center;"
        "animation:slide .45s cubic-bezier(.2,.8,.2,1) backwards}",
        "@keyframes slide{from{opacity:0;transform:translate(-10px,-10px) scale(.4)}"
        "to{opacity:1;transform:translate(0,0) scale(1)}}",
        ".f{animation:fade .6s ease-out 1.4s backwards}",
        "@keyframes fade{from{opacity:0}to{opacity:1}}",
        "@media (prefers-reduced-motion:reduce){.c,.f{animation:none}}",
        "</style>",
        f'<rect width="{width}" height="{height}" rx="10" fill="#0d1117"/>',
    ]

    # month labels
    prev_month = None
    for w, col in enumerate(grid):
        m = col[0][0].month
        if m != prev_month and w < WEEKS - 2:
            parts.append(f'<text x="{LEFT + w * STEP}" y="{TOP - 9}">{col[0][0].strftime("%b")}</text>')
        prev_month = m
    # weekday labels
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text x="6" y="{TOP + r * STEP + 10}">{name}</text>')

    for w, col in enumerate(grid):
        for r, (d, c) in enumerate(col):
            if c is None:
                continue
            delay = (w + r) * 0.018
            x, y = LEFT + w * STEP, TOP + r * STEP
            parts.append(
                f'<rect class="c" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="3" '
                f'fill="{PALETTE[level(c)]}" style="animation-delay:{delay:.3f}s">'
                f"<title>{c} contribution{'s' if c != 1 else ''} on {d.isoformat()}</title></rect>"
            )

    # legend + footer
    fy = TOP + DAYS * STEP + 22
    lx = width - 14 - len(PALETTE) * STEP - 34
    parts.append(f'<g class="f"><text x="{lx - 30}" y="{fy + 10}">Less</text>')
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx + i * STEP}" y="{fy}" width="{BOX}" height="{BOX}" rx="3" fill="{color}"/>')
    parts.append(f'<text x="{lx + len(PALETTE) * STEP + 4}" y="{fy + 10}">More</text>')
    total = data.get("total", 0)
    parts.append(
        f'<text x="{LEFT}" y="{fy + 10}" style="font-size:11px"><tspan fill="#39d353">$</tspan> '
        f'<tspan fill="#c9d1d9">{total:,} contributions in the last year</tspan>'
        f'  <tspan fill="#6e7681">| streak {data.get("current_streak", 0)}d '
        f'| longest {data.get("longest_streak", 0)}d</tspan></text></g>'
    )
    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
