"""Fetch a user's public contribution calendar and write data/contributions.json."""
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Aminsalah1"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (profile-art-bot)",
        "Accept": "text/html",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_count(text: str) -> int:
    text = (text or "").strip()
    if not text or text.lower().startswith("no contributions"):
        return 0
    m = re.match(r"([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    # Tooltips carry the counts: <tool-tip for="contribution-day-component-X-Y">5 contributions on ...</tool-tip>
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip") if t.get("for")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        d = cell["data-date"]
        level = int(cell.get("data-level", 0) or 0)
        text = tips.get(cell.get("id"), "") or cell.get_text(" ", strip=True)
        count = parse_count(text)
        if count == 0 and level > 0:
            count = level  # fallback if the tooltip text is missing
        days.append({"date": d, "count": count, "level": level})
    days.sort(key=lambda x: x["date"])
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)
    # current streak: walk back from the last day; a zero "today" doesn't break it
    current = 0
    idx = len(days) - 1
    if idx >= 0 and days[idx]["count"] == 0 and days[idx]["date"] >= date.today().isoformat():
        idx -= 1
    while idx >= 0 and days[idx]["count"] > 0:
        current += 1
        idx -= 1
    return current, longest


def monthly(days: list[dict]) -> dict:
    totals = OrderedDict()
    for day in days:
        key = day["date"][:7]
        totals[key] = totals.get(key, 0) + day["count"]
    return totals


def main() -> int:
    html = fetch_html(URL)
    days = parse_days(html)
    if not days:
        print("No contribution cells found - GitHub markup may have changed.", file=sys.stderr)
        return 1
    current, longest = streaks(days)
    data = {
        "username": USERNAME,
        "generated": date.today().isoformat(),
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "monthly_totals": monthly(days),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{len(days)} days, {data['total']} contributions, streak {current}/{longest} -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
