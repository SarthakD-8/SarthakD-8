
#!/usr/bin/env python3

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_PATH = DATA_DIR / "contributions.json"

USERNAME = os.getenv("GH_PROFILE_USER", "SarthakD-8")
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch_days():
    response = requests.get(
        URL,
        headers={"User-Agent": "sarthak-profile-readme/1.0"},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")

    if not cells:
        raise RuntimeError(
            "GitHub contribution calendar was not found. "
            "GitHub may have changed its HTML structure."
        )

    days = []

    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue

        cell_id = cell.get("id")
        tooltip = (
            soup.find("tool-tip", attrs={"for": cell_id})
            if cell_id
            else None
        )

        tooltip_text = tooltip.get_text(" ", strip=True) if tooltip else ""

        if re.search(r"no contributions", tooltip_text, re.I):
            count = 0
        else:
            match = re.search(r"(\d+)", tooltip_text)
            count = int(match.group(1)) if match else 0

        days.append({
            "date": date,
            "count": count,
            "level": int(cell.get("data-level") or 0),
        })

    days.sort(key=lambda item: item["date"])

    if not days:
        raise RuntimeError("GitHub returned no valid contribution dates.")

    return days


def current_streak(days):
    today = dt.date.today().isoformat()
    index = len(days) - 1

    # Today's contribution count can still change.
    if days[index]["date"] == today and days[index]["count"] == 0:
        index -= 1

    streak = 0
    end_index = index

    while index >= 0 and days[index]["count"] > 0:
        streak += 1
        index -= 1

    if streak == 0:
        return {"length": 0, "start": None, "end": None}

    return {
        "length": streak,
        "start": days[index + 1]["date"],
        "end": days[end_index]["date"],
    }


def longest_streak(days):
    longest = 0
    current = 0
    start_index = 0
    best_start = None
    best_end = None

    for index, day in enumerate(days):
        if day["count"] > 0:
            if current == 0:
                start_index = index

            current += 1

            if current > longest:
                longest = current
                best_start = days[start_index]["date"]
                best_end = day["date"]
        else:
            current = 0

    return {
        "length": longest,
        "start": best_start,
        "end": best_end,
    }


def build_data(days):
    total = sum(day["count"] for day in days)
    active_days = sum(day["count"] > 0 for day in days)

    best_day = max(days, key=lambda day: day["count"])

    monthly = {}

    for day in days:
        month = day["date"][:7]
        monthly[month] = monthly.get(month, 0) + day["count"]

    return {
        "username": USERNAME,
        "generated_at": dt.datetime.now(
            dt.timezone.utc
        ).isoformat(timespec="seconds"),
        "range": {
            "start": days[0]["date"],
            "end": days[-1]["date"],
        },
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1)
        if active_days else 0,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {
            "date": best_day["date"],
            "count": best_day["count"],
        },
        "monthly": [
            {"month": month, "total": count}
            for month, count in sorted(monthly.items())
        ],
        "days": days,
    }


def main():
    print(f"Fetching contributions for {USERNAME}...")

    days = fetch_days()
    data = build_data(days)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print(f"Saved: {OUT_PATH}")
    print(f"Total contributions: {data['total_contributions']}")
    print(f"Active days: {data['active_days']}")
    print(f"Current streak: {data['current_streak']['length']} days")
    print(f"Longest streak: {data['longest_streak']['length']} days")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"GitHub request failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Contribution fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
