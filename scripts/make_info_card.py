"""Neofetch-style animated info card -> info-card.svg."""
import os
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
USERNAME = os.environ.get("GH_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Aminsalah1"

NOW = "AI Engineer | Senior CS Student @ MSA University"
STACK = [
    "Python", "C++", "C#", "SQL", "Machine Learning", "Deep Learning",
    "Computer Vision", "HCI", "OpenCV", "TensorFlow", "PyTorch", "Git", "GitHub",
]
HIGHLIGHTS = [
    "🎓 Senior CS student at MSA University, specializing in AI and intelligent systems.",
    "🤖 Graduation project: handwritten math reasoning, error detection & step-by-step understanding.",
    "🧠 Becoming an AI Engineer - Machine Learning, Deep Learning, Computer Vision.",
    "📚 Training & certifications in AI, Data Analysis and Full-Stack Development.",
]

W = 490
PAD = 18
LINE = 17
KEY_W = 62
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
COLORS = {"Now": "#39d353", "Stack": "#58a6ff", "Highlights": "#d2a8ff"}


def main():
    lines = []  # (key_or_None, key_color, text, indent_px)
    host = f"{USERNAME.lower()}@github"
    lines.append(("__host__", None, host, 0))
    lines.append(("__rule__", None, "-" * len(host), 0))
    lines.append(("Now", COLORS["Now"], NOW, KEY_W))
    for i, chunk in enumerate(textwrap.wrap(" · ".join(x.replace(" ", "\u00a0") for x in STACK), 50, break_on_hyphens=False)):
        lines.append(("Stack" if i == 0 else None, COLORS["Stack"], chunk, KEY_W))
    lines.append(("Highlights", COLORS["Highlights"], "", 0))
    for h in HIGHLIGHTS:
        for i, chunk in enumerate(textwrap.wrap(h, 58, break_on_hyphens=False)):
            lines.append((None, None, chunk, 12 if i == 0 else 30))

    top = 46
    height = top + len(lines) * LINE + 46
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" aria-label="{escape(USERNAME)} info card">',
        "<style>",
        f"text{{font-family:{FONT};font-size:12px;fill:#c9d1d9}}",
        # Visible by default; the fade-in only plays on top (fill-mode backwards).
        ".l{animation:in .4s ease-out backwards}",
        "@keyframes in{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
        ".cur{animation:blink 1s steps(1) infinite}",
        "@keyframes blink{50%{opacity:0}}",
        "@media (prefers-reduced-motion:reduce){.l,.cur{animation:none}}",
        "</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{height - 1}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M.5 10.5a10 10 0 0 1 10-10h{W - 21}a10 10 0 0 1 10 10v18H.5z" fill="#161b22"/>',
        '<circle cx="18" cy="15" r="5.5" fill="#ff5f56"/>',
        '<circle cx="36" cy="15" r="5.5" fill="#ffbd2e"/>',
        '<circle cx="54" cy="15" r="5.5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="19" text-anchor="middle" style="font-size:11px;fill:#8b949e">'
        f"{escape(host)}: ~/neofetch</text>",
    ]

    for i, (key, color, text, indent) in enumerate(lines):
        y = top + 12 + i * LINE
        delay = 0.25 + i * 0.12
        attrs = f'class="l" style="animation-delay:{delay:.2f}s"'
        if key == "__host__":
            user, _, rest = text.partition("@")
            out.append(
                f'<text x="{PAD}" y="{y}" {attrs}><tspan fill="#39d353" font-weight="bold">{escape(user)}</tspan>'
                f'<tspan fill="#8b949e">@</tspan><tspan fill="#58a6ff" font-weight="bold">{escape(rest)}</tspan></text>'
            )
        elif key == "__rule__":
            out.append(f'<text x="{PAD}" y="{y}" fill="#30363d" {attrs}>{escape(text)}</text>')
        else:
            seg = ""
            if key:
                seg += f'<tspan fill="{color}" font-weight="bold">{escape(key)}:</tspan>'
            seg += f'<tspan x="{PAD + indent}">{escape(text)}</tspan>' if text else ""
            out.append(f'<text x="{PAD}" y="{y}" {attrs}>{seg}</text>')

    # neofetch colour strip + prompt
    sy = top + len(lines) * LINE + 6
    strip = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0", "#58a6ff", "#d2a8ff"]
    sdelay = 0.25 + len(lines) * 0.12
    out.append(f'<g class="l" style="animation-delay:{sdelay:.2f}s">')
    for i, c in enumerate(strip):
        out.append(f'<rect x="{PAD + i * 22}" y="{sy}" width="20" height="10" rx="2" fill="{c}"/>')
    out.append(
        f'<text x="{PAD}" y="{sy + 28}"><tspan fill="#39d353">$</tspan> <tspan class="cur" fill="#c9d1d9">_</tspan></text></g>'
    )
    out.append("</svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
