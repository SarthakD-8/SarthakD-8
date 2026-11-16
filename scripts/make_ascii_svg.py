
"""
Generate an animated terminal-style ASCII portrait as SVG.

Usage:
    python scripts/make_ascii_svg.py

Optional:
    COLS=180 python scripts/make_ascii_svg.py
    STATIC=1 python scripts/make_ascii_svg.py
"""

from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
import html
import os
import sys


ROOT = Path(__file__).resolve().parent.parent

SOURCE = (
    Path(sys.argv[1]).resolve()
    if len(sys.argv) > 1
    else ROOT / "source-prepped.png"
)

OUTPUT = (
    Path(sys.argv[2]).resolve()
    if len(sys.argv) > 2
    else ROOT / "assets" / "ascii-portrait.svg"
)

# Configuration
COLS = max(60, int(os.getenv("COLS", "180")))

ART_WIDTH = 800
CELL_WIDTH = ART_WIDTH / COLS
CELL_HEIGHT = CELL_WIDTH * 15 / 8
ROWS = round(COLS * 8 / 15)

RAMP = " .`:-=+*cs#%@"

CONTRAST = 1.35
BRIGHTNESS = 0.95
GAMMA = 0.85

PADDING = 20
TITLEBAR_HEIGHT = 34
STATUS_HEIGHT = 38

ART_HEIGHT = ROWS * CELL_HEIGHT
CANVAS_WIDTH = ART_WIDTH + PADDING * 2
CANVAS_HEIGHT = (
    TITLEBAR_HEIGHT + ART_HEIGHT + STATUS_HEIGHT + PADDING
)

BACKGROUND = "#0d1117"
BACKGROUND_TOP = "#161f2b"
FRAME = "#30363d"
TEXT_MUTED = "#7d8590"
TEXT_COLOR = "#c9d1d9"
ACCENT = "#58a6ff"

USERNAME = "sarthak@github"
DISPLAY_NAME = "Sarthak Dongare"

STATIC = os.getenv("STATIC", "").lower() in {
    "1", "true", "yes"
}


def convert_to_ascii(image_path: Path) -> list[str]:
    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}\n"
            "Run your image preprocessing script first."
        )

    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    if image.width < 10 or image.height < 10:
        raise ValueError(
            f"Input image is unexpectedly small: {image.size}"
        )

    # Convert to grayscale and improve tonal separation.
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image, cutoff=1)

    image = ImageEnhance.Brightness(image).enhance(BRIGHTNESS)
    image = ImageEnhance.Contrast(image).enhance(CONTRAST)

    image = image.resize(
        (COLS, ROWS),
        Image.Resampling.LANCZOS,
    )

    pixels = image.load()
    rows = []

    for y in range(ROWS):
        characters = []

        for x in range(COLS):
            luminance = pixels[x, y] / 255.0
            luminance = pow(luminance, GAMMA)

            index = round(
                (1.0 - luminance) * (len(RAMP) - 1)
            )

            index = max(0, min(len(RAMP) - 1, index))
            characters.append(RAMP[index])

        rows.append("".join(characters))

    visible = sum(
        character != " "
        for line in rows
        for character in line
    )

    if visible == 0:
        raise ValueError(
            "ASCII conversion produced an empty portrait. "
            "Check source-prepped.png."
        )

    print(f"Visible ASCII characters: {visible}")
    return rows


def render_svg(rows: list[str]) -> str:
    parts = []

    art_top = TITLEBAR_HEIGHT + PADDING * 0.35
    font_size = CELL_HEIGHT * 0.86

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="auto" '
        f'viewBox="0 0 {CANVAS_WIDTH:.1f} {CANVAS_HEIGHT:.1f}" '
        f'role="img" aria-label="Animated ASCII portrait of '
        f'{html.escape(DISPLAY_NAME)}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )

    parts.append("""
    <defs>
        <linearGradient id="terminal-bg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#161f2b"/>
            <stop offset="100%" stop-color="#0d1117"/>
        </linearGradient>

        <style>
            .portrait-row {
                animation: reveal 0.7s ease-out both;
            }

            @keyframes reveal {
                from { opacity: 0.15; }
                to { opacity: 1; }
            }

            .terminal-cursor {
                animation: blink 1s steps(2, start) infinite;
            }

            @keyframes blink {
                to { opacity: 0; }
            }
        </style>
    </defs>
    """)

    # Terminal background.
    parts.append(
        f'<rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" '
        f'rx="12" fill="url(#terminal-bg)"/>'
    )

    parts.append(
        f'<rect x="0.5" y="0.5" '
        f'width="{CANVAS_WIDTH - 1}" height="{CANVAS_HEIGHT - 1}" '
        f'rx="12" fill="none" stroke="{FRAME}"/>'
    )

    # Title bar.
    parts.append(
        f'<line x1="0" y1="{TITLEBAR_HEIGHT}" '
        f'x2="{CANVAS_WIDTH}" y2="{TITLEBAR_HEIGHT}" '
        f'stroke="{FRAME}"/>'
    )

    for i, color in enumerate([
        "#ff5f56", "#ffbd2e", "#27c93f"
    ]):
        parts.append(
            f'<circle cx="{PADDING + i * 16}" '
            f'cy="{TITLEBAR_HEIGHT / 2}" r="5" fill="{color}"/>'
        )

    parts.append(
        f'<text x="{CANVAS_WIDTH / 2}" '
        f'y="{TITLEBAR_HEIGHT / 2 + 4}" '
        f'fill="{TEXT_MUTED}" font-size="12" '
        f'text-anchor="middle">./sarthak/portrait.sh</text>'
    )

    # Portrait: text is always rendered.
    # Animation is only an enhancement, never a visibility dependency.
    for index, line in enumerate(rows):
        y = (
            art_top
            + index * CELL_HEIGHT
            + CELL_HEIGHT * 0.74
        )

        delay = 0 if STATIC else index * 0.012

        parts.append(
            f'<text class="portrait-row" '
            f'xml:space="preserve" '
            f'x="{PADDING}" y="{y:.2f}" '
            f'fill="{TEXT_COLOR}" '
            f'font-size="{font_size:.2f}" '
            f'textLength="{ART_WIDTH}" '
            f'lengthAdjust="spacing" '
            f'style="animation-delay:{delay:.3f}s">'
            f'{html.escape(line)}</text>'
        )

    # Status bar.
    status_line_y = TITLEBAR_HEIGHT + ART_HEIGHT + PADDING * 0.35
    status_y = status_line_y + 22

    parts.append(
        f'<line x1="0" y1="{status_line_y:.2f}" '
        f'x2="{CANVAS_WIDTH}" y2="{status_line_y:.2f}" '
        f'stroke="{FRAME}"/>'
    )

    parts.append(
        f'<text x="{PADDING}" y="{status_y:.2f}" '
        f'fill="{TEXT_MUTED}" font-size="13">'
        f'{html.escape(USERNAME)}:~$ whoami '
        f'<tspan fill="{ACCENT}">'
        f'{html.escape(DISPLAY_NAME)}'
        f'</tspan></text>'
    )

    cursor_x = (
        PADDING
        + len(f"{USERNAME}:~$ whoami {DISPLAY_NAME} ") * 7.8
    )

    parts.append(
        f'<rect class="terminal-cursor" '
        f'x="{cursor_x:.2f}" y="{status_y - 12:.2f}" '
        f'width="8" height="14" fill="{TEXT_COLOR}"/>'
    )

    parts.append("</svg>")

    return "\n".join(parts)


def main():
    print("Generating ASCII portrait...")
    print(f"Source: {SOURCE}")
    print(f"Output: {OUTPUT}")

    rows = convert_to_ascii(SOURCE)
    svg = render_svg(rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

    print("\nPortrait generated successfully.")
    print(f"Output: {OUTPUT}")
    print(f"Grid: {COLS} x {ROWS}")
    print(f"SVG size: {len(svg) / 1024:.2f} KB")
    print(f"Static mode: {STATIC}")


if __name__ == "__main__":
    main()
