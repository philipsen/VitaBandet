#!/usr/bin/env python3
"""Scrape STF fjällstation/fjällstuga opening hours from svenskaturistforeningen.se.

Source: each accommodation page, Kontakt och öppettider → Öppettider block.
Re-run before the trip — STF publishes 2027 dates gradually (many fjällstugor still 2026-only).

Usage:
  python3 scripts/scrape_stf_openings.py
  python3 scripts/scrape_stf_openings.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from dataclasses import asdict, dataclass
from datetime import date
from typing import Optional

BASE = "https://www.svenskaturistforeningen.se/boende/"
TRIP_START = date(2027, 2, 15)

MONTHS = {
    "januari": 1,
    "februari": 2,
    "mars": 3,
    "april": 4,
    "maj": 5,
    "juni": 6,
    "juli": 7,
    "augusti": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

# name, slug, plan day numbers on Vita Bandet 2027
ROUTE_HUTS = [
    ("Grövelsjön", "stf-grovelsjon-fjallstation", [1]),
    ("Rogen", "stf-rogen-fjallstuga", [2]),
    ("Helags", "stf-helags-fjallstation", [7]),
    ("Sylarna", "stf-sylarna-fjallstation", [8]),
    ("Blåhammaren", "stf-blahammaren", [9]),
    ("Storulvån", "stf-storulvan-fjallstation", [10]),
    ("Kvikkjokk", "stf-kvikkjokk-fjallstation", [47]),
    ("Saltoluokta", "stf-saltoluokta-fjallstation", [51]),
    ("Ritsem", "stf-ritsem", [55]),
    ("Sitojaure", "stf-sitojaure-fjallstuga", [56]),
    ("Sälka", "stf-salka-fjallstuga", [58]),
    ("Tjäktja", "stf-tjaktja-fjallstuga", [59]),
    ("Alesjaure", "stf-alesjaure-fjallstuga", [60]),
    ("Abiskojaure", "stf-abiskojaure-fjallstuga", [61]),
    ("Abisko", "stf-abisko-turiststation", [62]),
    ("Pältsa", "stf-paltsa-fjallstuga", [69]),
    ("Vakkotavare", "stf-vakkotavare-fjallstuga", []),
    ("Kebnekaise", "stf-kebnekaise-fjallstation", []),
]

HOUR_PATTERNS = [
    # <p><strong>2027:</strong><br>25 februari - 18 april<br>...</p>
    re.compile(
        r"<p>\s*<strong>\s*(20\d{2}):\s*</strong>\s*(?:<br\s*/?>\s*)?"
        r"([^<]+(?:<br\s*/?>\s*[^<]+)*)(?:<br\s*/?>)?\s*</p>",
        re.I,
    ),
    # <p><strong>2027:<br></strong>26 februari - 18 april<br>...</p>
    re.compile(
        r"<p>\s*<strong>\s*(20\d{2}):\s*<br\s*/?>\s*</strong>\s*"
        r"([^<]+(?:<br\s*/?>\s*[^<]+)*)(?:<br\s*/?>)?\s*</p>",
        re.I,
    ),
    # fjällstuga: <p><strong>2026</strong>:<br>20 mars - 19 april<br>...</p>
    re.compile(
        r"<p>\s*<strong>\s*(20\d{2})\s*</strong>\s*:\s*<br\s*/?>\s*"
        r"([^<]+(?:<br\s*/?>\s*[^<]+)*)(?:<br\s*/?>)?\s*</p>",
        re.I,
    ),
]


@dataclass
class HutHours:
    name: str
    slug: str
    url: str
    plan_days: list[int]
    hours_2026: Optional[str]
    hours_2027: Optional[str]
    year_round: bool
    winter_open: Optional[str]
    winter_close: Optional[str]
    plan_notes: list[str]


def fetch(slug: str) -> str:
    url = BASE + slug + "/"
    req = urllib.request.Request(url, headers={"User-Agent": "VitaBandet-planning/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalize_periods(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", " · ", raw, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def parse_hours(html: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for pattern in HOUR_PATTERNS:
        for match in pattern.finditer(html):
            year, body = match.group(1), normalize_periods(match.group(2))
            if body and re.search(
                r"(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober)",
                body,
                re.I,
            ):
                found[year] = body
    return found


def parse_winter_window(periods: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    if not periods:
        return None, None
    winter = periods.split("·")[0].strip()
    m = re.match(r"(\d{1,2})\s+(\w+)\s*-\s*(\d{1,2})\s+(\w+)", winter)
    if not m:
        return None, None
    start = date(2027, MONTHS[m.group(2).lower()], int(m.group(1)))
    end = date(2027, MONTHS[m.group(4).lower()], int(m.group(3)))
    return start, end


def day_date(day: int) -> date:
    return date.fromordinal(TRIP_START.toordinal() + day - 1)


def plan_notes(
    plan_days: list[int],
    year_round: bool,
    open_start: Optional[date],
    open_end: Optional[date],
    hours_2027: Optional[str],
    hours_2026: Optional[str],
) -> list[str]:
    notes: list[str] = []
    for d in plan_days:
        when = day_date(d)
        if year_round:
            notes.append(f"D{d} ({when:%d %b}) — year-round")
            continue
        if open_start and open_end:
            if when < open_start:
                notes.append(
                    f"D{d} ({when:%d %b}) — **before** winter open ({open_start:%-d %b %Y})"
                )
            elif when > open_end:
                notes.append(
                    f"D{d} ({when:%d %b}) — **after** winter close ({open_end:%-d %b %Y})"
                )
            else:
                notes.append(f"D{d} ({when:%d %b}) — staffed OK")
        elif hours_2026 and not hours_2027:
            notes.append(
                f"D{d} ({when:%d %b}) — 2027 not published; 2026 proxy: {hours_2026.split('·')[0]}"
            )
        else:
            notes.append(f"D{d} ({when:%d %b}) — no öppettider on STF page; verify")
    return notes


def scrape_hut(name: str, slug: str, plan_days: list[int]) -> HutHours:
    html = fetch(slug)
    hours = parse_hours(html)
    year_round = bool(re.search(r"öppet året runt", html, re.I))
    h26, h27 = hours.get("2026"), hours.get("2027")
    periods = h27 or h26
    open_start, open_end = parse_winter_window(periods)
    return HutHours(
        name=name,
        slug=slug,
        url=BASE + slug + "/",
        plan_days=plan_days,
        hours_2026=h26,
        hours_2027=h27,
        year_round=year_round,
        winter_open=open_start.isoformat() if open_start else None,
        winter_close=open_end.isoformat() if open_end else None,
        plan_notes=plan_notes(plan_days, year_round, open_start, open_end, h27, h26),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON to stdout")
    args = parser.parse_args()

    results = [scrape_hut(name, slug, days) for name, slug, days in ROUTE_HUTS]
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
        return

    print(f"STF opening hours — scraped {date.today().isoformat()}\n")
    for hut in results:
        print(f"## {hut.name}")
        print(f"   {hut.url}")
        if hut.year_round:
            print("   Year-round")
        if hut.hours_2027:
            print(f"   2027: {hut.hours_2027}")
        if hut.hours_2026:
            print(f"   2026: {hut.hours_2026}")
        if not hut.hours_2027 and not hut.hours_2026 and not hut.year_round:
            print("   (no öppettider block)")
        for note in hut.plan_notes:
            print(f"   · {note}")
        print()


if __name__ == "__main__":
    main()
