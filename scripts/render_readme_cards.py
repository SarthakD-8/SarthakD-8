
"""
Generate dynamic GitHub repository cards for the profile README.

Usage:
    python scripts/render_readme_cards.py

Optional:
    FEATURED_REPOS=SafeVision,FlowML,dataguard-cli python scripts/render_readme_cards.py
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "project-cards.svg"

USERNAME = "SarthakD-8"
CARD_WIDTH = 420
CARD_HEIGHT = 154
GAP = 18
PADDING = 20
COLUMNS = 2
MAX_CARDS = 6

BACKGROUND = "#0d1117"
CARD_BACKGROUND = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Jupyter Notebook": "#DA5B0B",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
}


def fetch_repositories() -> list[dict]:
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?type=owner&sort=updated&per_page=100"
    )

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-readme",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            repositories = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code}. "
            "Check the username or try again later."
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not connect to GitHub: {exc.reason}"
        ) from exc

    if not isinstance(repositories, list):
        raise RuntimeError("Unexpected response from GitHub API.")

    return [
        repo for repo in repositories
        if not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("disabled")
    ]


def select_repositories(repositories: list[dict]) -> list[dict]:
    featured_names = [
        name.strip()
        for name in os.getenv("FEATURED_REPOS", "").split(",")
        if name.strip()
    ]

    if featured_names:
        by_name = {
            repo["name"].lower(): repo
            for repo in repositories
        }

        selected = []

        for name in featured_names:
            repo = by_name.get(name.lower())
            if repo:
                selected.append(repo)
            else:
                print(f"Warning: repository not found: {name}")

        return selected[:MAX_CARDS]

    # Automatic selection: prioritize stars, then recent updates.
    repositories.sort(
        key=lambda repo: (
            repo.get("stargazers_count", 0),
            repo.get("updated_at", ""),
        ),
        reverse=True,
    )

    return repositories[:MAX_CARDS]


def wrap_text(value: str, max_chars: int = 48) -> list[str]:
    words = (value or "No description provided.").split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    if len(lines) > 2:
        lines = lines[:2]
        lines[-1] = lines[-1].rstrip("., ") + "..."

    return lines or ["No description provided."]


def render_card(repo: dict, x: int, y: int) -> str:
    name = escape(repo.get("name", "Untitled"))
    description = wrap_text(repo.get("description") or "")

    language = repo.get("language") or "Other"
    language_color = LANGUAGE_COLORS.get(language, "#8b949e")

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)

    description_svg = "".join(
        f'<text x="{x + 20}" y="{y + 68 + index * 17}" '
        f'fill="{MUTED}" font-size="12">{escape(line)}</text>'
        for index, line in enumerate(description)
    )

    return f"""
    <a href="{escape(repo.get("html_url", "#"), {'"': '&quot;'})}"
       target="_blank">
      <rect x="{x}" y="{y}" width="{CARD_WIDTH}"
            height="{CARD_HEIGHT}" rx="10"
            fill="{CARD_BACKGROUND}" stroke="{BORDER}"/>

      <text x="{x + 20}" y="{y + 33}"
            fill="{ACCENT}" font-size="16"
            font-weight="600">{name}</text>

      {description_svg}

      <circle cx="{x + 25}" cy="{y + 124}"
              r="5" fill="{language_color}"/>

      <text x="{x + 37}" y="{y + 128}"
            fill="{MUTED}" font-size="11">
        {escape(language)}
      </text>

      <text x="{x + 260}" y="{y + 128}"
            fill="{MUTED}" font-size="11">
        ★ {stars}   Forks {forks}
      </text>
    </a>
    """


def render_svg(repositories: list[dict]) -> str:
    count = len(repositories)

    if count == 0:
        raise RuntimeError(
            "No repositories were found to display."
        )

    rows = (count + COLUMNS - 1) // COLUMNS

    width = (
        PADDING * 2
        + COLUMNS * CARD_WIDTH
        + (COLUMNS - 1) * GAP
    )

    height = (
        PADDING * 2
        + rows * CARD_HEIGHT
        + (rows - 1) * GAP
        + 42
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="100%" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Featured GitHub repositories">',
        f'<rect width="{width}" height="{height}" '
        f'rx="12" fill="{BACKGROUND}"/>',
        f'<text x="{PADDING}" y="30" fill="{TEXT}" '
        f'font-size="16" font-weight="600">'
        f'FEATURED REPOSITORIES</text>',
        f'<text x="{width - PADDING}" y="30" '
        f'text-anchor="end" fill="{MUTED}" font-size="11">'
        f'{count} PROJECTS · {USERNAME}</text>',
    ]

    for index, repo in enumerate(repositories):
        column = index % COLUMNS
        row = index // COLUMNS

        x = PADDING + column * (CARD_WIDTH + GAP)
        y = 48 + PADDING + row * (CARD_HEIGHT + GAP)

        parts.append(render_card(repo, x, y))

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    print(f"Fetching repositories for {USERNAME}...")

    repositories = fetch_repositories()
    selected = select_repositories(repositories)

    if not selected:
        raise RuntimeError(
            "No matching repositories found. "
            "Check FEATURED_REPOS or your public repositories."
        )

    svg = render_svg(selected)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

    print(f"Found public repositories: {len(repositories)}")
    print("Selected projects:")

    for repo in selected:
        print(f"  - {repo['name']}")

    print(f"\nGenerated: {OUTPUT}")
    print(f"SVG size: {len(svg) / 1024:.2f} KB")


if __name__ == "__main__":
    main()
