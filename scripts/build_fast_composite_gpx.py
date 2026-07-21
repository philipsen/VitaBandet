#!/usr/bin/env python3
"""Build a shortest/fastest Band composite from dense scraped tracks + ~27 km camps.

Selection (avg gap ≤800 m, hit milestones ≤3 km):
  S1–S2  Emil Johansson          — shortest dense Grövel→Gäddede
  S3–S5  Christian Kämmer 2023   — short+fast Gäddede→Abisko (one continuous tour)
  S6     Noah Bovin              — shortest dense traditional Abisko→Trerik

Outputs:
  tracks/generated/vita-bandet-fast-27km.gpx
  plan/dag-for-dag-fast-27km-2027.md

Usage:
  python3 scripts/build_fast_composite_gpx.py
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from xml.dom import minidom

ROOT = Path(__file__).resolve().parent.parent
SCRAPE = ROOT / "tracks" / "scrape"
OUT_GPX = ROOT / "tracks" / "generated" / "vita-bandet-fast-27km.gpx"
OUT_MD = ROOT / "plan" / "dag-for-dag-fast-27km-2027.md"

NS = {"g": "http://www.topografix.com/GPX/1/1"}
START_DATE = date(2027, 2, 15)
DAY_KM = 27.0

MILES = {
    "GROVEL": (62.10, 12.31),
    "STORLIEN": (63.298, 12.101),
    "GADDEDE": (64.52, 14.14),
    "HEMAVAN": (65.83, 15.08),
    "KVIKK": (66.9513, 17.7285),
    "ABISKO": (68.35, 18.83),
    "TRERIK": (69.06, 20.55),
}

# (leg, file, start_key, end_key, note)
SEGMENTS = [
    ("S1", "emils-vita-band.gpx", "GROVEL", "STORLIEN", "Emil · dense short Grövel→Storlien"),
    ("S2", "emils-vita-band.gpx", "STORLIEN", "GADDEDE", "Emil · continuation Storlien→Gäddede"),
    ("S3", "christian-kammer-s-band.gpx", "GADDEDE", "HEMAVAN", "Kämmer 2023 · short+fast east corridor"),
    ("S4", "christian-kammer-s-band.gpx", "HEMAVAN", "KVIKK", "Kämmer 2023 · väster om Jäckvik"),
    ("S5", "christian-kammer-s-band.gpx", "KVIKK", "ABISKO", "Kämmer 2023 · Kungsleden / Saltoluokta"),
    ("S6", "noah-bovin-s-band.gpx", "ABISKO", "TRERIK", "Noah · traditional SE finish (skip Norway DNT)"),
]

# Soft snap camps to these when within window of a 27 km target
SNAP_PINS = [
    ("Storlien", MILES["STORLIEN"]),
    ("Gäddede", MILES["GADDEDE"]),
    ("Hemavan", MILES["HEMAVAN"]),
    ("Kvikkjokk", MILES["KVIKK"]),
    ("Abisko", MILES["ABISKO"]),
    ("Treriksröset", MILES["TRERIK"]),
]


def hav(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371.0
    p1, p2 = map(math.radians, [a[0], b[0]])
    dlat, dlon = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def load_trk(path: Path) -> list[tuple[float, float]]:
    root = ET.parse(path).getroot()
    pts: list[tuple[float, float]] = []
    for trk in root.findall("g:trk", NS):
        for seg in trk.findall("g:trkseg", NS):
            for p in seg.findall("g:trkpt", NS):
                pts.append((float(p.get("lat")), float(p.get("lon"))))
    return pts


def cumdist(pts: list[tuple[float, float]]) -> list[float]:
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + hav(pts[i - 1], pts[i]))
    return c


def nearest(pts: list[tuple[float, float]], coord: tuple[float, float], lo: int = 0) -> tuple[int, float]:
    best_i, best_d = lo, 1e18
    step = max(1, (len(pts) - lo) // 3000)
    for i in range(lo, len(pts), step):
        d = hav(pts[i], coord)
        if d < best_d:
            best_i, best_d = i, d
    for i in range(max(lo, best_i - step), min(len(pts), best_i + step + 1)):
        d = hav(pts[i], coord)
        if d < best_d:
            best_i, best_d = i, d
    return best_i, best_d


def extract_leg(pts: list[tuple[float, float]], start: tuple[float, float], end: tuple[float, float]):
    ia, da = nearest(pts, start)
    ib, db = nearest(pts, end, lo=ia)
    if ib <= ia:
        raise SystemExit(f"bad order start/end off={da:.2f}/{db:.2f}")
    return pts[ia : ib + 1], da, db


def stitch() -> tuple[list[tuple[float, float]], list[dict]]:
    route: list[tuple[float, float]] = []
    meta: list[dict] = []
    for leg, fname, sk, ek, note in SEGMENTS:
        pts = load_trk(SCRAPE / fname)
        seg, da, db = extract_leg(pts, MILES[sk], MILES[ek])
        # Seam: drop first point if continuing (avoid duplicate)
        if route:
            # skip points until we move away from last point
            last = route[-1]
            j = 0
            while j < len(seg) and hav(seg[j], last) < 0.05:
                j += 1
            seg = seg[j:]
        km = 0.0
        for i in range(1, len(seg)):
            km += hav(seg[i - 1], seg[i])
        meta.append(
            {
                "leg": leg,
                "file": fname,
                "note": note,
                "km": km,
                "pts": len(seg),
                "start_off_km": da,
                "end_off_km": db,
            }
        )
        print(f"{leg}: {fname}  {km:.1f} km  {len(seg)} pts  (hit {da:.2f}/{db:.2f} km)")
        route.extend(seg)
    return route, meta


@dataclass
class Camp:
    day: int
    km: float
    cum: float
    lat: float
    lon: float
    label: str
    is_shop: bool


def place_camps(route: list[tuple[float, float]]) -> list[Camp]:
    c = cumdist(route)
    total = c[-1]
    camps: list[Camp] = []
    prev_m = 0.0
    day = 1
    shop_names = {n for n, _ in SNAP_PINS if n != "Treriksröset"}

    while prev_m < total - 0.5:
        target = min(prev_m + DAY_KM, total)
        # Soft snap to shop if within ±4 km of target and ahead of prev
        snapped = None
        for name, coord in SNAP_PINS:
            i, d = nearest(route, coord)
            if d > 2.5:
                continue
            km = c[i]
            if prev_m + 3 < km <= target + 4.0:
                # prefer if closer to target than current
                if snapped is None or abs(km - target) < abs(snapped[0] - target):
                    snapped = (km, i, name, name in shop_names or name == "Treriksröset")

        if snapped and (snapped[3] or abs(snapped[0] - target) < 2.0):
            km, i, label, is_shop = snapped
        else:
            # index at target km
            i = min(range(len(c)), key=lambda j: abs(c[j] - target))
            km = c[i]
            label = f"Camp · {km:.0f} km"
            is_shop = False
            # named snap within 1.5 km of camp point
            for name, coord in SNAP_PINS:
                if hav(route[i], coord) < 1.5:
                    label = name
                    is_shop = name in shop_names
                    break

        day_km = km - prev_m
        if day_km < 1.0 and label != "Treriksröset":
            prev_m = km
            continue
        camps.append(
            Camp(
                day=day,
                km=day_km,
                cum=km,
                lat=route[i][0],
                lon=route[i][1],
                label=label,
                is_shop=is_shop and label != "Treriksröset",
            )
        )
        prev_m = km
        day += 1
        if label == "Treriksröset" or km >= total - 0.3:
            break
        if day > 80:
            raise SystemExit("too many days")

    if camps[-1].label != "Treriksröset":
        i = len(route) - 1
        camps.append(
            Camp(
                day=day,
                km=c[-1] - prev_m,
                cum=c[-1],
                lat=route[i][0],
                lon=route[i][1],
                label="Treriksröset",
                is_shop=False,
            )
        )
    return camps


def write_gpx(route: list[tuple[float, float]], camps: list[Camp], meta: list[dict]) -> None:
    OUT_GPX.parent.mkdir(parents=True, exist_ok=True)
    gpx = ET.Element(
        "gpx",
        {
            "version": "1.1",
            "creator": "VitaBandet fast composite",
            "xmlns": "http://www.topografix.com/GPX/1/1",
        },
    )
    meta_el = ET.SubElement(gpx, "metadata")
    ET.SubElement(meta_el, "name").text = "Vita Bandet — fast dense composite · 27 km days"
    desc = (
        "Shortest/fastest corridor from dense scraped Band tracks. "
        + " · ".join(f"{m['leg']}:{m['file'].replace('.gpx','')}" for m in meta)
    )
    ET.SubElement(meta_el, "desc").text = desc

    for c in camps:
        w = ET.SubElement(gpx, "wpt", {"lat": f"{c.lat:.8f}", "lon": f"{c.lon:.8f}"})
        tag = " D" if c.is_shop else ""
        ET.SubElement(w, "name").text = f"F{c.day:02d}{tag} · {c.label}"
        ET.SubElement(w, "desc").text = f"Day {c.day} · {c.km:.0f} km (cum {c.cum:.0f})"
        ET.SubElement(w, "sym").text = "Flag, Blue" if c.is_shop else "Campground"

    # Full track (decimate to ~150 m for size)
    trk = ET.SubElement(gpx, "trk")
    ET.SubElement(trk, "name").text = "Fast dense Band composite"
    seg = ET.SubElement(trk, "trkseg")
    last = None
    for lat, lon in route:
        if last is not None and hav(last, (lat, lon)) < 0.15:
            continue
        ET.SubElement(seg, "trkpt", {"lat": f"{lat:.8f}", "lon": f"{lon:.8f}"})
        last = (lat, lon)
    # always include end
    et = route[-1]
    ET.SubElement(seg, "trkpt", {"lat": f"{et[0]:.8f}", "lon": f"{et[1]:.8f}"})

    # One trkseg per source section for inspection
    for m in meta:
        pass  # single continuous track is clearer for BaseCamp day planning

    pretty = minidom.parseString(ET.tostring(gpx, encoding="utf-8")).toprettyxml(
        indent="  ", encoding="utf-8"
    )
    OUT_GPX.write_bytes(pretty)
    print(f"Wrote {OUT_GPX}")


def write_md(camps: list[Camp], meta: list[dict], total_km: float) -> None:
    n = len(camps)
    end = START_DATE + timedelta(days=n - 1)
    lines = [
        "# Vita Bandet 2027 — fast dense composite (~27 km/day)",
        "",
        f"**Pacing:** ~**{DAY_KM:.0f} km/day** · **{n} days** · **~{total_km:.0f} km** · "
        f"{START_DATE.isoformat()} → {end.isoformat()}.  ",
        f"**GPX:** [`vita-bandet-fast-27km.gpx`](../tracks/generated/vita-bandet-fast-27km.gpx).  ",
        "**Method:** stitch densest short/fast scraped Band legs (avg gap ≤800 m).  ",
        "",
        "> Not the BaseCamp master ([`2027.GPX`](../tracks/2027.GPX)). Uses **normal Band** "
        "corridors (east of Lapplandsleden · Kungsleden/Saltoluokta · traditional SE finish) — "
        "not Padjelanta-west / Norway DNT.",
        "",
        "## Source legs",
        "",
        "| Leg | Span | Source | km | Notes |",
        "|-----|------|--------|---:|-------|",
    ]
    spans = {
        "S1": "Grövelsjön → Storlien",
        "S2": "Storlien → Gäddede",
        "S3": "Gäddede → Hemavan",
        "S4": "Hemavan → Kvikkjokk",
        "S5": "Kvikkjokk → Abisko",
        "S6": "Abisko → Treriksröset",
    }
    for m in meta:
        lines.append(
            f"| {m['leg']} | {spans[m['leg']]} | `{m['file']}` | {m['km']:.0f} | {m['note']} |"
        )
    lines += [
        "",
        f"**Stitched length:** ~{total_km:.0f} km · mean day **~{total_km / n:.1f} km**.",
        "",
        "## Day-by-day",
        "",
        "| Day | Date | km | Cum | Camp |",
        "|----:|------|---:|----:|------|",
    ]
    for c in camps:
        dt = START_DATE + timedelta(days=c.day - 1)
        tag = " ★" if c.is_shop else (" **GOAL**" if c.label == "Treriksröset" else "")
        lines.append(
            f"| {c.day} | {dt.strftime('%a %d %b')} | {c.km:.0f} | {c.cum:.0f} | {c.label}{tag} |"
        )
    lines += [
        "",
        "---",
        "",
        f"*Generated by `scripts/build_fast_composite_gpx.py` · {date.today().isoformat()}*",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


def main() -> None:
    print("Stitching…")
    route, meta = stitch()
    c = cumdist(route)
    print(f"Route: {len(route)} pts · {c[-1]:.1f} km")
    camps = place_camps(route)
    print(f"Camps: {len(camps)} days · mean {c[-1]/len(camps):.1f} km")
    for camp in camps:
        if camp.is_shop or camp.label == "Treriksröset" or camp.day <= 2:
            print(f"  D{camp.day:02d} {camp.km:5.1f} → {camp.label} (cum {camp.cum:.0f})")
    write_gpx(route, camps, meta)
    write_md(camps, meta, c[-1])


if __name__ == "__main__":
    main()
