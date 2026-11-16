
#!/usr/bin/env python3
"""
Generate an animated GitHub profile hero SVG.

Layout:
- Left: personal introduction and portfolio link.
- Right: existing ASCII portrait, revealed row by row.
- Animations: staggered entrance, gradient name,
  pulsing status indicator and portrait reveal.

Input:
    assets/ascii-portrait.svg

Output:
    assets/hero.svg

Run:
    uv run python scripts/render_hero_svg.py
"""

from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parent.parent

PORTRAIT_PATH = ROOT / "assets" / "ascii-portrait.svg"
OUTPUT_PATH = ROOT / "assets" / "hero.svg"


# =========================================================
# PERSONAL INFORMATION
# =========================================================

NAME = "Sarthak"
SURNAME = "Dongare"

ROLE = "AI & DATA SCIENCE ENGINEER"

INTRO = [
    "I build intelligent systems,",
    "data-driven applications and",
    "useful software experiences.",
]

INTERESTS = "AI / ML   ·   DATA   ·   FULLSTACK"

PORTFOLIO = "Sarthak's Website"
GITHUB = "github.com/SarthakD-8"


# =========================================================
# DESIGN TOKENS
# =========================================================

WIDTH = 880
HEIGHT = 360

BG = "#0d1117"
PANEL = "#111923"
BORDER = "#263342"

TEXT = "#e6edf3"
MUTED = "#8b9aaa"
ACCENT = "#58a6ff"
GREEN = "#3fb950"

FONT = "Arial, Helvetica, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Consolas, monospace"
SERIF = "Georgia, serif"


# =========================================================
# XML HELPERS
# =========================================================

def xml_text(value: object) -> str:
    """Escape text so it is safe inside SVG/XML elements."""
    return escape(str(value), quote=True)


def xml_number(value: float) -> str:
    """Format numeric SVG attributes consistently."""
    return f"{value:.4f}".rstrip("0").rstrip(".")


# =========================================================
# PORTRAIT EXTRACTION
# =========================================================

def extract_portrait():
    """
    Extract text rows from the existing ASCII portrait SVG.

    Each text row is rendered separately so that CSS can
    animate the portrait progressively.
    """

    if not PORTRAIT_PATH.exists():
        raise FileNotFoundError(
            f"Portrait not found: {PORTRAIT_PATH}\n"
            "Run your ASCII portrait generator first."
        )

    try:
        tree = ET.parse(PORTRAIT_PATH)
    except ET.ParseError as exc:
        raise ValueError(
            f"The source portrait SVG is invalid XML: {exc}"
        ) from exc

    root = tree.getroot()

    viewbox = root.attrib.get("viewBox")

    if not viewbox:
        raise ValueError(
            "The portrait SVG must contain a valid viewBox."
        )

    try:
        values = [float(value) for value in viewbox.replace(",", " ").split()]
    except ValueError as exc:
        raise ValueError(
            f"Invalid portrait viewBox: {viewbox}"
        ) from exc

    if len(values) != 4:
        raise ValueError(
            f"Expected four viewBox values, received: {viewbox}"
        )

    _, _, source_width, source_height = values

    if source_width <= 0 or source_height <= 0:
        raise ValueError("Portrait viewBox dimensions must be positive.")

    rows = []

    for element in root.iter():

        # Handle SVG elements with or without XML namespaces.
        if element.tag.split("}")[-1] != "text":
            continue

        content = "".join(element.itertext())

        if not content.strip():
            continue

        attrs = element.attrib

        try:
            x = float(attrs.get("x", 0))
            y = float(attrs.get("y", 0))
            font_size = float(attrs.get("font-size", 7))
        except ValueError as exc:
            raise ValueError(
                "Invalid x, y or font-size attribute "
                "in the source portrait SVG."
            ) from exc

        rows.append({
            "x": x,
            "y": y,
            "font_size": font_size,
            "content": content,
        })

    if not rows:
        raise ValueError(
            "No text rows found in the ASCII portrait SVG."
        )

    return rows, source_width, source_height


# =========================================================
# PORTRAIT RENDERER
# =========================================================

def render_portrait():
    """Render the ASCII portrait with staggered row animations."""

    rows, source_width, source_height = extract_portrait()

    target_width = 315
    target_height = 275

    scale = min(
        target_width / source_width,
        target_height / source_height,
    )

    offset_x = (
        540 + (target_width - source_width * scale) / 2
    )

    offset_y = (
        38 + (target_height - source_height * scale) / 2
    )

    elements = []

    for index, row in enumerate(rows):

        delay = 0.5 + index * 0.025

        elements.append(
            f"""
            <text
                class="portrait-row"
                x="{xml_number(row['x'])}"
                y="{xml_number(row['y'])}"
                font-size="{xml_number(row['font_size'])}"
                fill="{ACCENT}"
                style="animation-delay:{delay:.3f}s"
                xml:space="preserve"
            >{xml_text(row['content'])}</text>
            """
        )

    return f"""
    <g transform="translate({offset_x:.2f} {offset_y:.2f}) scale({scale:.4f})">
        <g font-family="{MONO}">
            {''.join(elements)}
        </g>
    </g>
    """


# =========================================================
# HERO GENERATOR
# =========================================================

def generate_hero():

    portrait = render_portrait()

    # Escape every dynamic text value before inserting it into XML.
    name = xml_text(NAME)
    surname = xml_text(SURNAME)
    role = xml_text(ROLE)

    intro_1 = xml_text(INTRO[0])
    intro_2 = xml_text(INTRO[1])
    intro_3 = xml_text(INTRO[2])

    interests = xml_text(INTERESTS)
    portfolio = xml_text(PORTFOLIO)

    aria_label = xml_text(
        f"{NAME} {SURNAME}, {ROLE}"
    )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="{aria_label}"
>

<title>{name} {surname} — Developer Profile</title>

<style>

    @keyframes fadeUp {{
        from {{
            opacity: 0;
            transform: translateY(18px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes portraitIn {{
        from {{
            opacity: 0;
            transform: translateY(5px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes pulse {{
        0%, 100% {{
            opacity: 1;
        }}
        50% {{
            opacity: .35;
        }}
    }}

    .intro {{
        opacity: 0;
        animation: fadeUp .75s ease-out forwards;
    }}

    .portrait-row {{
        opacity: 0;
        animation: portraitIn .35s ease-out forwards;
    }}

    .status {{
        animation: pulse 1.8s ease-in-out infinite;
    }}

    .name {{
        font-family: {SERIF};
        font-size: 66px;
        letter-spacing: -2px;
        font-weight: 400;
        fill: url(#nameGradient);
    }}

    .body {{
        font-family: {FONT};
        font-size: 17px;
        fill: {MUTED};
    }}

    .mono {{
        font-family: {MONO};
        font-size: 11px;
        letter-spacing: 1px;
    }}

    @media (prefers-reduced-motion: reduce) {{
        .intro,
        .portrait-row,
        .status {{
            animation: none !important;
            opacity: 1 !important;
            transform: none !important;
        }}
    }}

</style>

<defs>

    <linearGradient
        id="background"
        x1="0"
        y1="0"
        x2="1"
        y2="1"
    >
        <stop offset="0%" stop-color="{BG}"/>
        <stop offset="100%" stop-color="{PANEL}"/>
    </linearGradient>

    <linearGradient
        id="nameGradient"
        x1="0"
        y1="0"
        x2="1"
        y2="0"
    >
        <stop offset="0%" stop-color="{TEXT}"/>
        <stop offset="50%" stop-color="{ACCENT}"/>
        <stop offset="100%" stop-color="{TEXT}"/>

        <animate
            attributeName="x1"
            values="0;1;0"
            dur="6s"
            repeatCount="indefinite"
        />
    </linearGradient>

    <radialGradient id="glow">
        <stop
            offset="0%"
            stop-color="{ACCENT}"
            stop-opacity=".17"
        />
        <stop
            offset="100%"
            stop-color="{ACCENT}"
            stop-opacity="0"
        />
    </radialGradient>

</defs>


<!-- BACKGROUND -->

<rect
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="15"
    fill="url(#background)"
    stroke="{BORDER}"
    stroke-width="1"
/>

<circle
    cx="720"
    cy="165"
    r="190"
    fill="url(#glow)"
/>


<!-- LEFT INTRODUCTION -->

<g class="intro" style="animation-delay:.1s">

    <circle
        class="status"
        cx="51"
        cy="47"
        r="5"
        fill="{GREEN}"
    />

    <text
        x="66"
        y="51"
        class="mono"
        fill="{MUTED}"
    >BUILDING / LEARNING / EXPERIMENTING</text>

</g>


<!-- NAME -->

<g class="intro" style="animation-delay:.25s">

    <text
        x="46"
        y="139"
        class="name"
    >{name}</text>

    <text
        x="48"
        y="178"
        font-family="{FONT}"
        font-size="16"
        font-weight="600"
        fill="{TEXT}"
    >{surname}</text>

</g>


<!-- ROLE -->

<g class="intro" style="animation-delay:.4s">

    <text
        x="49"
        y="215"
        class="mono"
        fill="{ACCENT}"
    >{role}</text>

</g>


<!-- INTRODUCTION TEXT -->

<g class="intro" style="animation-delay:.55s">

    <text
        x="49"
        y="252"
        class="body"
    >{intro_1}</text>

    <text
        x="49"
        y="277"
        class="body"
    >{intro_2}</text>

    <text
        x="49"
        y="302"
        class="body"
    >{intro_3}</text>

</g>


<!-- INTERESTS -->

<g class="intro" style="animation-delay:.75s">

    <text
        x="49"
        y="329"
        class="mono"
        font-size="9"
        fill="{ACCENT}"
    >{interests}</text>

</g>


<!-- DIVIDER -->

<line
    x1="510"
    y1="35"
    x2="510"
    y2="325"
    stroke="{BORDER}"
    stroke-width="1"
/>


<!-- RIGHT ASCII PORTRAIT -->

{portrait}


<!-- PORTFOLIO LINK -->

<g class="intro" style="animation-delay:.9s">

    <a href="https://portfolio-website-kappa-one-98.vercel.app/" target="_blank">
        <text
            x="49"
            y="348"
            class="mono"
            font-size="9"
            fill="{ACCENT}"
            style="text-decoration: underline;"
        >{portfolio}</text>
    </a>

</g>

</svg>
"""

    # Ensure the output directory exists.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Validate XML before writing the final file.
    try:
        ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError(
            f"Generated SVG is invalid XML: {exc}"
        ) from exc

    OUTPUT_PATH.write_text(svg, encoding="utf-8")

    rows, _, _ = extract_portrait()

    print(f"Generated: {OUTPUT_PATH}")
    print(f"Portrait rows animated: {len(rows)}")
    print("SVG validation successful!")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    generate_hero()
