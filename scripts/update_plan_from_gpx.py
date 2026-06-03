#!/usr/bin/env python3
"""Sync dag-for-dag-2028.md day headers and distances from tracks/2028.GPX."""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
GPX = ROOT / "tracks" / "2028.GPX"
PLAN = ROOT / "plan" / "dag-for-dag-2028.md"
ELEV_CSV = ROOT / "plan" / "day-elevation-2028.csv"
NS = {"g": "http://www.topografix.com/GPX/1/1"}
TRACK_ORDER = ["Section1", "Section 2", "Section 3", "Section 4", "Section 5", "Section 6"]
START = (62.10, 12.31)
START_DATE = datetime(2028, 2, 15)
SIDE_PASS_DAYS = {44}  # Jäckvik — VGB väster om; pin off main track


def hav(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dlat = math.radians(b[0] - a[0])
    dlon = math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def load_track() -> tuple[list[tuple[float, float]], list[float]]:
    root = ET.parse(GPX).getroot()
    pts: list[tuple[float, float]] = []
    for name in TRACK_ORDER:
        for trk in root.findall("g:trk", NS):
            if trk.findtext("g:name", default="", namespaces=NS) != name:
                continue
            for seg in trk.findall("g:trkseg", NS):
                for p in seg.findall("g:trkpt", NS):
                    pts.append((float(p.get("lat")), float(p.get("lon"))))
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + hav(pts[i - 1], pts[i]))
    return pts, cum


def nearest_on_track(pts: list[tuple[float, float]], coord: tuple[float, float]) -> tuple[int, float]:
    best_i, best_d = 0, float("inf")
    step = max(1, len(pts) // 5000)
    for i in range(0, len(pts), step):
        d = hav(pts[i], coord)
        if d < best_d:
            best_i, best_d = i, d
    lo, hi = max(0, best_i - step), min(len(pts) - 1, best_i + step)
    for i in range(lo, hi + 1):
        d = hav(pts[i], coord)
        if d < best_d:
            best_i, best_d = i, d
    return best_i, best_d


def load_day_waypoints() -> tuple[dict[int, list[dict]], int]:
    root = ET.parse(GPX).getroot()
    by_day: dict[int, list[dict]] = defaultdict(list)
    max_day = 0
    for w in root.findall("g:wpt", NS):
        name = w.findtext("g:name", default="", namespaces=NS)
        m = re.match(r"^D(\d+)\s*[·\-]", name)
        if not m:
            continue
        day = int(m.group(1))
        max_day = max(max_day, day)
        coord = (float(w.get("lat")), float(w.get("lon")))
        by_day[day].append(
            {
                "name": name,
                "label": re.sub(r"^D\d+\s*[·\-]\s*", "", name).strip(),
                "coord": coord,
            }
        )
    return by_day, max_day


def day_tags(day: int, label: str) -> str:
    tags: list[str] = []
    low = label.lower()
    if day == 10 or ("storlien" in low and "approach" not in low):
        tags.append("**D**")
    if "gäddede" in low and "väster" not in low:
        tags.append("**D**")
    if "regnfallet" in low or "valsjöbua" in low:
        tags.extend(["**D**", "★ Bandet hero"])
    if "klimpfjäll" in low:
        tags.append("**D** (optional)")
    if "hemavan" in low:
        tags.extend(["**D**", "**R**?"])
    if "kvikkjokk" in low or "kvikjock" in low:
        tags.append("**D**")
    if label.strip().lower() == "ritsem":
        tags.append("**D**")
    if "abisko" in low and "north" not in low and "ojaure" not in low:
        tags.append("**D**")
    if "pältastugan" in low or "pältsa" in low:
        tags.append("**D**")
    if "sälka" in low:
        tags.append("**H**")
    if "lappjord" in low:
        tags.append("**H**")
    if "altevass" in low:
        tags.append("**H**")
    if "gaskashytta" in low or "vuomahytta" in low or "dividalshytta" in low or "daertahytta" in low:
        tags.append("**H**")
    if "treriksröset" in low:
        tags.append("**GOAL**")
    if day in {52, 57} or "w of saltoluokta" in low or "sarek w" in low:
        tags.append("**W**")
    if "jäckvik" in low:
        tags.append("**W**")
    if "ammarnäs" in low:
        tags.append("**D** (optional)")
    return (" · " + " · ".join(tags)) if tags else ""


def compute_days(pts, cum, by_day: dict, max_day: int) -> list[dict]:
    start_idx, _ = nearest_on_track(pts, START)
    prev_idx = start_idx
    rows: list[dict] = []

    for day in range(1, max_day + 1):
        if day not in by_day:
            raise SystemExit(f"Missing D{day} waypoint in GPX")
        wps = sorted(by_day[day], key=lambda w: nearest_on_track(pts, w["coord"])[0])
        label = wps[0]["label"] if len(wps) == 1 else " / ".join(w["label"] for w in wps)
        coord = wps[-1]["coord"]

        if day in SIDE_PASS_DAYS:
            rows.append(
                {
                    "day": day,
                    "label": label,
                    "coord": coord,
                    "day_km": 0.0,
                    "cum_km": (cum[prev_idx] - cum[start_idx]) / 1000,
                    "idx": prev_idx,
                }
            )
            continue

        gidx, _ = nearest_on_track(pts, coord)
        end_idx = max(gidx, prev_idx)
        day_km = (cum[end_idx] - cum[prev_idx]) / 1000
        cum_km = (cum[end_idx] - cum[start_idx]) / 1000
        rows.append(
            {
                "day": day,
                "label": label,
                "coord": coord,
                "day_km": day_km,
                "cum_km": cum_km,
                "idx": end_idx,
            }
        )
        prev_idx = end_idx

    running = 0
    for row in rows:
        row["day_km"] = max(0, round(row["day_km"]))
        running += row["day_km"]
        row["cum_km"] = running
    return rows


def fetch_elevation(pts, cum, boundaries: list[float]) -> list[tuple[int, int]]:
    sample_ds = set()
    step = 250.0
    d = 0.0
    while d <= cum[-1]:
        sample_ds.add(round(d, 3))
        d += step
    for b in boundaries:
        sample_ds.add(round(b * 1000.0, 3))
    sample_ds = sorted(sample_ds)

    def interp(meters: float) -> tuple[float, float]:
        if meters <= 0:
            return pts[0]
        if meters >= cum[-1]:
            return pts[-1]
        lo, hi = 0, len(cum) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < meters:
                lo = mid + 1
            else:
                hi = mid
        i = lo
        if i == 0:
            return pts[0]
        d0, d1 = cum[i - 1], cum[i]
        t = 0.0 if d1 == d0 else (meters - d0) / (d1 - d0)
        lat = pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0])
        lon = pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])
        return lat, lon

    sample_pts = [interp(m) for m in sample_ds]
    api = "https://api.opentopodata.org/v1/eudem25m?locations="
    batch = 90
    eles: list[float] = []
    for i in range(0, len(sample_pts), batch):
        batch_pts = sample_pts[i : i + batch]
        locs = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in batch_pts)
        req = Request(api + quote(locs, safe="|,."), headers={"User-Agent": "VitaBandetElevation/1.0"})
        for attempt in range(5):
            try:
                with urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                break
            except Exception as exc:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        for item in data["results"]:
            val = item.get("elevation")
            if val is None or not (-500 < float(val) < 5000):
                eles.append(eles[-1] if eles else 500.0)
            else:
                eles.append(float(val))
        time.sleep(1.0)

    per_day: list[tuple[int, int]] = []
    prev_m = 0.0
    for b in boundaries:
        i0 = bisect.bisect_left(sample_ds, round(prev_m * 1000, 3))
        i1 = bisect.bisect_right(sample_ds, round(b * 1000, 3)) - 1
        up = down = 0.0
        for j in range(i0 + 1, i1 + 1):
            de = eles[j] - eles[j - 1]
            if de > 0:
                up += de
            elif de < 0:
                down -= de
        per_day.append((round(up), round(down)))
        prev_m = b
    return per_day


def load_existing_elevation(text: str) -> dict[int, tuple[int, int]]:
    elev: dict[int, tuple[int, int]] = {}
    for m in re.finditer(r"^#### Day (\d+) · .* · ↑(\d+) m ↓(\d+) m ·", text, re.MULTILINE):
        elev[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
    if ELEV_CSV.exists():
        with ELEV_CSV.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["day"] == "TOTAL":
                    continue
                d = int(row["day"])
                if d not in elev:
                    elev[d] = (int(row["up_m"]), int(row["down_m"]))
    return elev


def format_date(day: int) -> str:
    dt = START_DATE + timedelta(days=day - 1)
    return dt.strftime("%a %d %b")


def parse_day_dates(text: str) -> dict[int, str]:
    dates: dict[int, str] = {}
    for m in re.finditer(r"^#### Day (\d+) · (.*? · \d+ \w+ \d+ \w+)", text, re.MULTILINE):
        dates[int(m.group(1))] = m.group(2)
    return dates


def day_header(row: dict, date: str, up: int, down: int) -> str:
    tags = day_tags(row["day"], row["label"])
    return (
        f"#### Day {row['day']} · {date} · {row['day_km']} km (cum {row['cum_km']}) "
        f"· ↑{up} m ↓{down} m · {row['label']}{tags}"
    )


def stub_body(day: int, label: str) -> str:
    return (
        f"\nCamp at **{label}** — on [`2028.gpx`](../tracks/2028.gpx) track.\n\n"
        f"| Acc | Notes |\n|-----|-------|\n| **T** / **H** | See GPX pin |\n"
    )


def update_plan(rows: list[dict], elev: list[tuple[int, int]]) -> None:
    text = PLAN.read_text(encoding="utf-8")
    dates = parse_day_dates(text)
    max_day = rows[-1]["day"]

    for row, (up, down) in zip(rows, elev):
        day = row["day"]
        date = dates.get(day, format_date(day))
        header = day_header(row, date, up, down)
        pattern = rf"^#### Day {day} · .*$"
        if re.search(pattern, text, re.MULTILINE):
            text = re.sub(pattern, header, text, count=1, flags=re.MULTILINE)
        else:
            # Append new day before storm section or at end of section 6
            insert_before = "\n---\n\n### Torneträsk östra spetsen **W**"
            block = header + stub_body(day, row["label"])
            if insert_before in text:
                text = text.replace(insert_before, block + insert_before, 1)
            else:
                text = text.rstrip() + "\n\n" + block

    total_km = rows[-1]["cum_km"]
    end_date = (START_DATE + timedelta(days=max_day - 1)).strftime("%d %b")
    text = re.sub(
        r"\*\*Season:\*\* \*\*15 Feb – .*?\*\* \(\d+ days",
        f"**Season:** **15 Feb – {end_date} 2028** ({max_day} days",
        text,
        count=1,
    )
    text = re.sub(
        r"\*\*Total:\*\* \*\*~[\d,]+ km\*\* \(table\)",
        f"**Total:** **~{total_km:,} km** (table)",
        text,
        count=1,
    )
    text = re.sub(
        r"GPS often \*\*[\d,–]+ km\*\*",
        f"GPS track **~{round(cum[-1]/1000 if (cum := None) else total_km)} km**",
        text,
        count=1,
    )

    # Fix GPS line properly
    track_km = load_track()[1][-1] / 1000
    text = re.sub(
        r"GPS track \*\*~[\d,]+ km\*\*|GPS often \*\*[\d,–]+ km\*\*",
        f"GPS track **~{round(track_km):,} km**",
        text,
        count=1,
    )

    sections = [
        (1, 1, 10, "Grövelsjön → Storlien"),
        (2, 11, 24, "Storlien → Gäddede"),
        (3, 25, 34, "Gäddede → Hemavan · Lapplandsleden"),
        (4, 35, 47, "Viterskalet → Kvikkjokk"),
        (5, 48, 58, "Kvikkjokk → Sälka · Padjelanta-west"),
        ("5b", 59, 62, "Sälka → Abisko · Kungsleden"),
        (6, 63, max_day, "Abisko → Treriksröset · Nordkalottleden"),
    ]
    for sec in sections:
        title = f"## Section {sec[0]} — {sec[3]}" if sec[0] != "5b" else f"## Section 5b — {sec[3]}"
        d0, d1 = sec[1], sec[2]
        sec_km = rows[d1 - 1]["cum_km"] - (rows[d0 - 2]["cum_km"] if d0 > 1 else 0)
        text = re.sub(
            rf"^{re.escape(title)} \([\d,]+ km · days {d0}–\d+\)",
            f"{title} ({sec_km} km · days {d0}–{d1})",
            text,
            count=1,
            flags=re.MULTILINE,
        )

    # Update milestones table rows for key dates
    milestone_dates = {
        "15 Feb": (0, "Grövelsjön", 0),
        "23 Feb": (9, None, None),
        "24 Feb": (10, None, None),
        "29 Feb": (15, None, None),
        "2 Mar": (17, None, None),
        "9 Mar": (24, None, None),
        "13 Mar": (28, "Klimpfjäll", None),
        "19 Mar": (33, None, None),
        "20 Mar": (34, "Hemavan · **D**", None),
        "1 Apr": (47, None, None),
        "9 Apr": (55, None, None),
        "12 Apr": (58, None, None),
        "16 Apr": (62, None, None),
        "24 Apr": (70, "Treriksröset · **GOAL**", None),
    }
    for date, (day_num, default_name, _) in milestone_dates.items():
        if day_num == 0:
            km, name = 0, default_name
        else:
            row = rows[day_num - 1]
            km, name = row["cum_km"], default_name or row["label"]
        text = re.sub(
            rf"(\| {re.escape(date)} \| )[^|]+( \| )[\d,]+( \|)",
            rf"\g<1>{name}\g<2>{km:,} \3",
            text,
            count=1,
        )

    # Remove obsolete Pältsa milestone if present
    text = re.sub(r"\| \*\*22 Apr\*\* \| \*\*Pältsa\*\*.*\n", "", text)

    PLAN.write_text(text, encoding="utf-8")

    with ELEV_CSV.open("w", encoding="utf-8") as f:
        f.write("day,km,up_m,down_m,net_m\n")
        tot_up = tot_down = 0
        for row, (up, down) in zip(rows, elev):
            f.write(f"{row['day']},{row['day_km']},{up},{down},{up-down}\n")
            tot_up += up
            tot_down += down
        f.write(f"TOTAL,{rows[-1]['cum_km']},{round(tot_up)},{round(tot_down)},{round(tot_up-tot_down)}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-elevation", action="store_true")
    args = parser.parse_args()

    pts, cum = load_track()
    by_day, max_day = load_day_waypoints()
    rows = compute_days(pts, cum, by_day, max_day)
    boundaries = [r["cum_km"] for r in rows]

    print(f"Track {cum[-1]/1000:.1f} km · plan total {rows[-1]['cum_km']} km · {max_day} days")
    for r in rows:
        print(f"  D{r['day']:02d}  {r['day_km']:3d} km  cum {r['cum_km']:4d}  {r['label']}")

    text = PLAN.read_text(encoding="utf-8")
    existing = load_existing_elevation(text)

    if args.skip_elevation:
        elev = [existing.get(r["day"], (0, 0)) for r in rows]
        print("Skipping elevation fetch — reusing existing values where available")
    else:
        try:
            print("Fetching elevation…")
            elev = fetch_elevation(pts, cum, boundaries)
        except Exception as exc:
            print(f"Elevation fetch failed ({exc}) — reusing existing values")
            elev = [existing.get(r["day"], (0, 0)) for r in rows]

    update_plan(rows, elev)
    print(f"Updated {PLAN} and {ELEV_CSV}")


if __name__ == "__main__":
    main()
