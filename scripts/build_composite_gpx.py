#!/usr/bin/env python3
"""
Stitch historical Band tracks into one GPX for the 2028 plan route.

Segment sources (best match per dag-for-dag-2028.md):
  Grövelsjön → Storlien     Ola (Storlien variant)
  Storlien → Gäddede        Ola
  Gäddede → Hemavan         Ola (Lapplandsleden)
  Hemavan → Jäckvik → Kvikkjokk  Erik (Jäckvik W detour + dense)
  Kvikkjokk → Sälka         Erik (Paolo corridor / KL)
  Sälka → Abisko            Ola
  Abisko → Treriksröset     Ola

VGB: 2028 plan passes all six places väster om only (S→N: east of track).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement

PLAN_DIR = Path(__file__).resolve().parent.parent / "plan"
GPX_NS = "http://www.topografix.com/GPX/1/1"

MILESTONES = {
    "GROVEL": (62.10, 12.31),
    "STORLIEN": (63.298, 12.101),
    "GADDEDE": (64.52, 14.14),
    "HEMAVAN": (65.83, 15.08),
    # Jäkkvik village (Silvervägen / ICA) — not used for segment cuts; map label only
    "JACKVIK": (66.383, 16.967),
    "KVIKK": (66.9513, 17.7285),
    "SALKA": (67.366, 18.283),
    "ABISKO": (68.35, 18.83),
    "TRERIK": (69.06, 20.55),
    "PALTSA": (69.045, 20.739),
}

# (label, json file, start key, end key) — indices resolved along track order
SEGMENTS = [
    ("Grövelsjön → Storlien", "olas-vita-band-2-track.json", "GROVEL", "STORLIEN"),
    ("Storlien → Gäddede", "olas-vita-band-2-track.json", "STORLIEN", "GADDEDE"),
    ("Gäddede → Hemavan", "olas-vita-band-2-track.json", "GADDEDE", "HEMAVAN"),
    ("Hemavan → Jäckvik → Kvikkjokk", "eriks-band-track.json", "HEMAVAN", "KVIKK"),
    ("Kvikkjokk → Sälka", "eriks-band-track.json", "KVIKK", "SALKA"),
    ("Sälka → Abisko", "olas-vita-band-2-track.json", "SALKA", "ABISKO"),
    ("Abisko → Pältsa", "olas-vita-band-2-track.json", "ABISKO", "PALTSA"),
]


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_idx(locs: list, pt: tuple[float, float]) -> int:
    return min(
        range(len(locs)),
        key=lambda i: haversine_m(locs[i]["lat"], locs[i]["lng"], pt[0], pt[1]),
    )


def extract_segment(locs: list, start_key: str, end_key: str) -> list[dict]:
    """Extract points along track order from nearest start to nearest end."""
    i0 = nearest_idx(locs, MILESTONES[start_key])
    i1 = nearest_idx(locs, MILESTONES[end_key])
    if i0 <= i1:
        return locs[i0 : i1 + 1]
    return locs[i1 : i0 + 1][::-1]


def dedupe_join(acc: list[dict], new: list[dict], min_gap_m: float = 300) -> list[dict]:
    if not acc:
        return list(new)
    out = list(acc)
    for p in new:
        last = out[-1]
        if haversine_m(last["lat"], last["lng"], p["lat"], p["lng"]) < min_gap_m:
            continue
        out.append(p)
    return out


def assign_plan_times(points: list[dict], start: datetime, end: datetime) -> None:
    """Spread ISO timestamps by distance along the merged track."""
    if len(points) < 2:
        if points:
            points[0]["_iso"] = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        return
    cum = [0.0]
    for i in range(1, len(points)):
        cum.append(
            cum[-1]
            + haversine_m(
                points[i - 1]["lat"],
                points[i - 1]["lng"],
                points[i]["lat"],
                points[i]["lng"],
            )
        )
    total = cum[-1] or 1.0
    span = (end - start).total_seconds()
    for i, p in enumerate(points):
        t = start + timedelta(seconds=span * cum[i] / total)
        p["_iso"] = t.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_gpx(points: list[dict], name: str) -> str:
    gpx = Element(
        "gpx",
        attrib={"version": "1.1", "creator": "VitaBandet composite", "xmlns": GPX_NS},
    )
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = name
    desc = SubElement(meta, "desc")
    desc.text = (
        "Composite route for Vita Bandet 2028 plan: "
        "Ola (Storlien, Lapplandsleden, Norway leg) + Erik (Hemavan–Sälka). "
        "VGB six waypoints: väster om only (S→N, east of track). "
        "Not a recorded single hike — stitched from vitagronabandet.se tracks."
    )

    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = name
    seg = SubElement(trk, "trkseg")

    for p in points:
        att = {
            "lat": f"{p['lat']:.8f}".rstrip("0").rstrip("."),
            "lon": f"{p['lng']:.8f}".rstrip("0").rstrip("."),
        }
        trkpt = SubElement(seg, "trkpt", attrib=att)
        if p.get("_iso"):
            SubElement(trkpt, "time").text = p["_iso"]

    # Milestone waypoints (town centres / goals — VGB side-pass is on the track, not the pin)
    for label, pt in [
        ("Grövelsjön", MILESTONES["GROVEL"]),
        ("Storlien", MILESTONES["STORLIEN"]),
        ("Gäddede", MILESTONES["GADDEDE"]),
        ("Hemavan", MILESTONES["HEMAVAN"]),
        ("Jäckvik", MILESTONES["JACKVIK"]),
        ("Kvikkjokk", MILESTONES["KVIKK"]),
        ("Sälka", MILESTONES["SALKA"]),
        ("Abisko", MILESTONES["ABISKO"]),
        ("Treriksröset", MILESTONES["TRERIK"]),
    ]:
        w = SubElement(gpx, "wpt", attrib={"lat": f"{pt[0]:.6f}", "lon": f"{pt[1]:.6f}"})
        SubElement(w, "name").text = label

    rough = ET.tostring(gpx, encoding="unicode")
    parsed = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?>\n' + rough)
    return parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")


def main() -> None:
    merged: list[dict] = []
    log: list[str] = []

    for label, fname, sk, ek in SEGMENTS:
        path = PLAN_DIR / fname
        locs = json.load(open(path, encoding="utf-8"))["locations"]
        seg = extract_segment(locs, sk, ek)
        before = len(merged)
        merged = dedupe_join(merged, seg)
        added = len(merged) - before
        log.append(f"  {label}: {fname} [{sk}→{ek}] +{added} pts (raw {len(seg)})")

    # Plan window: 15 Feb – 19 Apr 2028
    assign_plan_times(merged, datetime(2028, 2, 15, 10, 0), datetime(2028, 4, 19, 12, 0))

    out = PLAN_DIR / "vita-bandet-2028-composite.gpx"
    xml = build_gpx(merged, "Vita Bandet 2028 (composite)")
    out.write_text(xml, encoding="utf-8")

    # Cumulative km
    km = sum(
        haversine_m(merged[i - 1]["lat"], merged[i - 1]["lng"], merged[i]["lat"], merged[i]["lng"])
        for i in range(1, len(merged))
    ) / 1000

    print(f"Wrote {len(merged)} points, {km:.0f} km track → {out}\n")
    print("Segments:")
    for line in log:
        print(line)


if __name__ == "__main__":
    main()
