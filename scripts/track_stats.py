#!/usr/bin/env python3
"""Print per-hiker stats for the band-tracks-comparison doc."""
from __future__ import annotations
import json, math
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "tracks" / "source"

HIKERS = [
    ("Erik",          2384, "eriks-band-track.json"),
    ("Jonathan",      2360, "jonathans-band-track.json"),
    ("Bernhard",       528, "bernhard-gervide-eckel-s-band-track.json"),
    ("Mårten",        2371, "martens-band-track.json"),
    ("Ola",            419, "olas-vita-band-2-track.json"),
    ("Paolo",         2102, "paolo-peralta-s-band-track.json"),
    ("Noah",           451, "noah-bovin-s-band-track.json"),
    ("Kalle",         2369, "kalles-band-track.json"),
    ("Lotta & Björn", 2278, "lottas-och-bjorns-band-track.json"),
]

MS = {
    "Grövelsjön":  (62.10, 12.31),
    "Helags":      (62.917359, 12.506156),
    "Blåhammaren": (63.187081, 12.174362),
    "Storlien":    (63.298, 12.101),
    "Gäddede":     (64.52, 14.14),
    "Klimpfjäll":  (65.067, 14.770),
    "Hemavan":     (65.83, 15.08),
    "Ammarnäs":    (65.965, 16.207),
    "Jäckvik":     (66.383, 16.967),
    "Kvikkjokk":   (66.9513, 17.7285),
    "Ritsem":      (67.7327, 17.4711),
    "Saltoluokta": (67.395, 18.508),
    "Sälka":       (67.946376, 18.281701),
    "Abisko":      (68.35, 18.83),
    "Pältsa":      (69.045, 20.739),
}


def hav(a, b):
    r = 6_371_000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dlat = math.radians(b[0] - a[0]); dlon = math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def parse_time(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


for name, hid, fname in HIKERS:
    d = json.load(open(SRC / fname))
    locs = d["locations"]
    pts = [(l["lat"], l["lng"]) for l in locs]
    times = [parse_time(l["Time"]) for l in locs if l.get("Time")]
    total = sum(hav(pts[i - 1], pts[i]) for i in range(1, len(pts))) / 1000
    gaps_m = [hav(pts[i - 1], pts[i]) for i in range(1, len(pts))]
    avg_gap = sum(gaps_m) / len(gaps_m) if gaps_m else 0
    max_gap = max(gaps_m) / 1000 if gaps_m else 0
    days = ((times[-1] - times[0]).total_seconds() / 86400) if len(times) >= 2 else 0
    # Median time-gap between consecutive points
    t_gaps = [(times[i] - times[i - 1]).total_seconds() / 60
              for i in range(1, len(times)) if (times[i] - times[i - 1]).total_seconds() > 0]
    t_gaps.sort()
    med_min = t_gaps[len(t_gaps) // 2] if t_gaps else 0
    # Milestone offsets
    offsets = {}
    for ms_name, ms_coord in MS.items():
        i = min(range(len(pts)), key=lambda j: hav(pts[j], ms_coord))
        offsets[ms_name] = (hav(pts[i], ms_coord) / 1000, locs[i].get("Time", "?")[:10])
    print(f'\n=== {name} (id={hid}) ===')
    print(f'  file: {fname}')
    print(f'  points: {len(pts)}  km: {total:.0f}  days: {days:.1f}  km/day: {total/days if days else 0:.1f}')
    print(f'  avgGap: {avg_gap:.0f}m  maxGap: {max_gap:.1f}km  median-time-gap: {med_min:.0f} min')
    print(f'  start: {locs[0]["Time"]}  end: {locs[-1]["Time"]}')
    print(f'  start point: ({pts[0][0]:.4f}, {pts[0][1]:.4f})  end point: ({pts[-1][0]:.4f}, {pts[-1][1]:.4f})')
    print(f'  milestone offsets (km) [date]:')
    for ms_name, (off, dt) in offsets.items():
        print(f'    {ms_name:12s} {off:6.2f}  [{dt}]')
