#!/usr/bin/env python3
"""Build an alternative Vita Bandet day plan on tracks/2027.GPX.

Pacing: day 1 = 11 km, day 2 = 17 km, then ~25 km/day.
Hard land on major ★ resupply towns (4 h shop time; camp there).
Prefer lower-elevation camps within a search window of the target distance.

Outputs:
  plan/dag-for-dag-alt-25km-2027.md
  tracks/2027-alt-25km-camps.gpx

Usage:
  python3 scripts/build_alt_day_plan.py
  python3 scripts/build_alt_day_plan.py --no-elev   # skip OpenTopoData
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.dom import minidom

ROOT = Path(__file__).resolve().parent.parent
GPX_IN = ROOT / "tracks" / "2027.GPX"
MD_OUT = ROOT / "plan" / "dag-for-dag-alt-25km-2027.md"
GPX_OUT = ROOT / "tracks" / "2027-alt-25km-camps.gpx"

NS = {"g": "http://www.topografix.com/GPX/1/1"}
TRACK_ORDER = ["Section1", "Section 2", "Section 3", "Section 4", "Section 5", "Section 6"]
START_DATE = date(2027, 2, 15)
START_COORD = (62.10, 12.31)

# Cruise after ramp
DAY1_KM = 11.0
DAY2_KM = 17.0
CRUISE_KM = 25.0
SEARCH_WINDOW_KM = 4.0  # look ± this for lower elev / named snap
NAMED_SNAP_KM = 1.8

# Major ★ shops — matched by substring on GPX waypoint labels; land overnight; 4 h
RESUPPLY_MATCH = [
    ("Storlien", ["storlien"]),
    ("Valsjöbua", ["valsjöbua", "valsjobua", "regnfallet"]),  # lanthandel / D20 area
    ("Gäddede", ["gäddede", "gaddede"]),
    ("Hemavan", ["hemavan"]),
    ("Kvikkjokk", ["kvikkjokk", "kvikjock"]),
    ("Ritsem", ["ritsem"]),
    ("Abisko", ["abisko"]),
]
# Prefer these exact waypoint names when several match
RESUPPLY_PREFER = {
    "Valsjöbua": ["valsjöbua lanthandel", "valsjöbua"],
    "Gäddede": ["d24 - gäddede", "gäddede"],
    "Hemavan": ["d34 · hemavan", "hemavan"],
    "Ritsem": ["d55 · ritsem", "ritsem"],
    "Abisko": ["d62 · abisko", "abisko"],
}
FINISH_LABEL = "Treriksröset"


def hav_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dlat = math.radians(b[0] - a[0])
    dlon = math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def load_track() -> tuple[list[tuple[float, float]], list[float]]:
    root = ET.parse(GPX_IN).getroot()
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
        cum.append(cum[-1] + hav_m(pts[i - 1], pts[i]))
    return pts, cum


def nearest_idx(pts: list[tuple[float, float]], coord: tuple[float, float]) -> int:
    best_i, best_d = 0, float("inf")
    step = max(1, len(pts) // 5000)
    for i in range(0, len(pts), step):
        d = hav_m(pts[i], coord)
        if d < best_d:
            best_i, best_d = i, d
    lo, hi = max(0, best_i - step), min(len(pts) - 1, best_i + step)
    for i in range(lo, hi + 1):
        d = hav_m(pts[i], coord)
        if d < best_d:
            best_i, best_d = i, d
    return best_i


def idx_at_km(cum: list[float], km: float) -> int:
    target = km * 1000.0
    return min(bisect.bisect_left(cum, target), len(cum) - 1)


def load_named_pins(pts, cum) -> list[tuple[float, str, tuple[float, float]]]:
    """Track-km, label, coord for useful named waypoints."""
    root = ET.parse(GPX_IN).getroot()
    pins: list[tuple[float, str, tuple[float, float]]] = []
    for w in root.findall("g:wpt", NS):
        name = (w.findtext("g:name", default="", namespaces=NS) or "").strip()
        if not name:
            continue
        label = re.sub(r"^D\d+\s*[·\-]\s*", "", name).strip()
        # Skip pure day numbers with no useful label noise
        low = label.lower()
        if low in {"", "approach"}:
            continue
        coord = (float(w.get("lat")), float(w.get("lon")))
        i = nearest_idx(pts, coord)
        # Ignore pins far off track (>3 km)
        if hav_m(pts[i], coord) > 3000:
            continue
        pins.append((cum[i] / 1000.0, label, coord))
    pins.sort(key=lambda x: x[0])
    return pins


def fetch_elev_profile(pts, cum, step_m: float = 1000.0) -> tuple[list[float], list[float]]:
    """Return (sample_km list, elev_m list) along track."""
    sample_m = []
    d = 0.0
    while d <= cum[-1]:
        sample_m.append(d)
        d += step_m
    if sample_m[-1] < cum[-1]:
        sample_m.append(cum[-1])

    def interp(meters: float) -> tuple[float, float]:
        i = min(bisect.bisect_left(cum, meters), len(cum) - 1)
        if i == 0:
            return pts[0]
        d0, d1 = cum[i - 1], cum[i]
        t = 0.0 if d1 == d0 else (meters - d0) / (d1 - d0)
        return (
            pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0]),
            pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1]),
        )

    sample_pts = [interp(m) for m in sample_m]
    api = "https://api.opentopodata.org/v1/eudem25m?locations="
    batch = 90
    eles: list[float] = []
    for i in range(0, len(sample_pts), batch):
        batch_pts = sample_pts[i : i + batch]
        locs = "|".join(f"{lat:.6f},{lon:.6f}" for lat, lon in batch_pts)
        req = Request(api + quote(locs, safe="|,."), headers={"User-Agent": "VitaBandetAltPlan/1.0"})
        for attempt in range(5):
            try:
                with urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2**attempt)
        for item in data["results"]:
            val = item.get("elevation")
            if val is None or not (-500 < float(val) < 5000):
                eles.append(eles[-1] if eles else 500.0)
            else:
                eles.append(float(val))
        time.sleep(1.05)
        print(f"  elev {min(i + batch, len(sample_pts))}/{len(sample_pts)}")
    return [m / 1000.0 for m in sample_m], eles


def elev_at(sample_km: list[float], eles: list[float], km: float) -> float:
    if not sample_km:
        return 0.0
    i = bisect.bisect_left(sample_km, km)
    if i <= 0:
        return eles[0]
    if i >= len(sample_km):
        return eles[-1]
    k0, k1 = sample_km[i - 1], sample_km[i]
    t = 0.0 if k1 == k0 else (km - k0) / (k1 - k0)
    return eles[i - 1] + t * (eles[i] - eles[i - 1])


@dataclass
class Camp:
    day: int
    km_from_prev: float
    cum_km: float
    lat: float
    lon: float
    elev_m: float | None
    up_m: int | None
    down_m: int | None
    label: str
    is_resupply: bool
    note: str


def day_gain_loss(
    sample_km: list[float], eles: list[float], start_km: float, end_km: float
) -> tuple[int, int]:
    """Sum ascent/descent along elev samples between start_km and end_km."""
    if not sample_km or end_km <= start_km:
        return 0, 0
    i0 = bisect.bisect_left(sample_km, start_km)
    i1 = bisect.bisect_right(sample_km, end_km) - 1
    if i1 <= i0:
        # fall back to endpoints only
        de = elev_at(sample_km, eles, end_km) - elev_at(sample_km, eles, start_km)
        return (round(de), 0) if de > 0 else (0, round(-de))
    up = down = 0.0
    # include start elev interpolated
    prev_e = elev_at(sample_km, eles, start_km)
    for j in range(max(i0, 0), i1 + 1):
        e = eles[j]
        de = e - prev_e
        if de > 0:
            up += de
        elif de < 0:
            down -= de
        prev_e = e
    end_e = elev_at(sample_km, eles, end_km)
    de = end_e - prev_e
    if de > 0:
        up += de
    elif de < 0:
        down -= de
    return round(up), round(down)


def resolve_resupply(
    pts, cum, named: list[tuple[float, str, tuple[float, float]]]
) -> list[tuple[str, float]]:
    """Return [(shop_name, track_km), ...] in route order."""
    found: list[tuple[str, float]] = []
    for shop, needles in RESUPPLY_MATCH:
        prefer = RESUPPLY_PREFER.get(shop, [])
        candidates: list[tuple[int, float, str]] = []  # rank, km, label
        for nkm, label, _coord in named:
            low = label.lower()
            # Skip Abiskojaure / approaches for Abisko village
            if shop == "Abisko" and ("ojaure" in low or "north" in low):
                continue
            if shop == "Gäddede" and "väster" in low:
                continue
            if shop == "Ritsem" and "approach" in low:
                continue
            if shop == "Kvikkjokk" and "approach" in low:
                continue
            if shop == "Valsjöbua" and "north of" in low:
                continue
            if not any(n in low for n in needles):
                continue
            rank = 50
            for i, pref in enumerate(prefer):
                if pref in low:
                    rank = i
                    break
            # Prefer main village / D-pin labels
            if re.search(r"\bd(10|24|34|47|55|62)\b", low):
                rank = min(rank, 1)
            if low.strip() in {shop.lower(), f"stf {shop.lower()}"}:
                rank = min(rank, 0)
            if "lanthandel" in low:
                rank = min(rank, 0)
            if low == "kvikkjokk":
                rank = 0
            candidates.append((rank, nkm, label))
        if not candidates:
            print(f"  WARNING: no pin for {shop}")
            continue
        candidates.sort()
        found.append((shop, candidates[0][1]))
        print(f"  ★ {shop}: {candidates[0][1]:.1f} km ({candidates[0][2]})")
    found.sort(key=lambda x: x[1])
    return found


def pick_camp_km(
    target_km: float,
    *,
    hard_end: float | None,
    hard_name: str | None,
    sample_km: list[float],
    eles: list[float],
    named: list[tuple[float, str, tuple[float, float]]],
    prev_km: float,
) -> tuple[float, str, bool, str]:
    """Choose camp distance; return (cum_km, label, is_resupply, note)."""
    # Hard land on next resupply if within reach of this day's target window
    if hard_end is not None and hard_name and hard_end > prev_km + 0.5:
        remaining = hard_end - prev_km
        # If shop is within cruise + window, land on shop
        if remaining <= CRUISE_KM + SEARCH_WINDOW_KM:
            return hard_end, hard_name, True, "★ resupply · 4 h shop · overnight"

    lo = max(prev_km + 6.0, target_km - SEARCH_WINDOW_KM)
    hi = min(target_km + SEARCH_WINDOW_KM, hard_end - 0.5 if hard_end else 1e9)
    if hi <= lo:
        hi = target_km
        lo = max(prev_km + 3.0, target_km - 2.0)

    # Prefer named pin in window
    best_named = None
    for nkm, label, _coord in named:
        if lo <= nkm <= hi and nkm > prev_km + 3.0:
            # score: closer to target + slight preference
            score = abs(nkm - target_km)
            if best_named is None or score < best_named[0]:
                best_named = (score, nkm, label)

    if best_named and best_named[0] <= NAMED_SNAP_KM:
        return best_named[1], best_named[2], False, "snap to named pin"

    # Lowest elev in window (1 km steps)
    if sample_km:
        candidates = []
        step = 0.5
        k = lo
        while k <= hi:
            e = elev_at(sample_km, eles, k)
            # Prefer lower elev; strong preference to stay near target (~25 km days)
            score = e + 25.0 * abs(k - target_km)
            candidates.append((score, k, e))
            k += step
        candidates.sort()
        k_pick = candidates[0][1]
        e_pick = candidates[0][2]
        return k_pick, f"Camp · {k_pick:.0f} km", False, f"low elev ~{e_pick:.0f} m"

    return target_km, f"Camp · {target_km:.0f} km", False, "target distance"


def build_camps(
    pts, cum, sample_km, eles, named, shops: list[tuple[str, float]]
) -> list[Camp]:
    start_i = nearest_idx(pts, START_COORD)
    start_km = cum[start_i] / 1000.0
    total_km = cum[-1] / 1000.0
    finish_km = total_km

    shop_idx = 0
    camps: list[Camp] = []
    prev_km = start_km
    day = 1

    while prev_km < finish_km - 0.8:
        next_shop = shops[shop_idx] if shop_idx < len(shops) else None
        next_shop_km = next_shop[1] if next_shop else None
        next_shop_name = next_shop[0] if next_shop else None
        if day == 1:
            target = prev_km + DAY1_KM
        elif day == 2:
            target = prev_km + DAY2_KM
        else:
            target = prev_km + CRUISE_KM

        # Don't overshoot finish
        if target >= finish_km - 1.0 and (next_shop_km is None or next_shop_km >= finish_km):
            k_pick = finish_km
            label = FINISH_LABEL
            is_r = False
            note = "GOAL"
        else:
            k_pick, label, is_r, note = pick_camp_km(
                target,
                hard_end=next_shop_km,
                hard_name=next_shop_name,
                sample_km=sample_km,
                eles=eles,
                named=named,
                prev_km=prev_km,
            )
            # Cap at finish
            if k_pick >= finish_km - 0.5:
                k_pick = finish_km
                label = FINISH_LABEL
                is_r = False
                note = "GOAL"

        i = idx_at_km(cum, k_pick)
        lat, lon = pts[i]
        elev = elev_at(sample_km, eles, k_pick) if sample_km else None
        up, down = day_gain_loss(sample_km, eles, prev_km, k_pick) if sample_km else (None, None)
        day_km = k_pick - prev_km
        camps.append(
            Camp(
                day=day,
                km_from_prev=day_km,
                cum_km=k_pick - start_km,
                lat=lat,
                lon=lon,
                elev_m=elev,
                up_m=up,
                down_m=down,
                label=label,
                is_resupply=is_r,
                note=note,
            )
        )
        if is_r and shop_idx < len(shops) and abs(k_pick - shops[shop_idx][1]) < 1.5:
            shop_idx += 1
        prev_km = k_pick
        day += 1
        if label == FINISH_LABEL:
            break
        if day > 90:
            raise SystemExit("Too many days — check anchors")

    # Ensure finish if last wasn't
    if camps[-1].label != FINISH_LABEL:
        i = len(pts) - 1
        end_km = cum[-1] / 1000.0
        up, down = day_gain_loss(sample_km, eles, prev_km, end_km) if sample_km else (None, None)
        camps.append(
            Camp(
                day=day,
                km_from_prev=end_km - prev_km,
                cum_km=total_km - start_km,
                lat=pts[i][0],
                lon=pts[i][1],
                elev_m=elev_at(sample_km, eles, total_km) if sample_km else None,
                up_m=up,
                down_m=down,
                label=FINISH_LABEL,
                is_resupply=False,
                note="GOAL",
            )
        )
    return camps


GPX_NS = "http://www.topografix.com/GPX/1/1"
GPXX_NS = "http://www.garmin.com/xmlschemas/GpxExtensions/v3"
WPTX_NS = "http://www.garmin.com/xmlschemas/WaypointExtension/v1"


def write_gpx(camps: list[Camp], pts, cum) -> None:
    """Write BaseCamp-compatible GPX (Garmin namespaces · GPX wpt child order)."""
    ET.register_namespace("", GPX_NS)
    ET.register_namespace("gpxx", GPXX_NS)
    ET.register_namespace("wptx1", WPTX_NS)

    gpx = ET.Element(
        f"{{{GPX_NS}}}gpx",
        {
            "version": "1.1",
            "creator": "VitaBandet alt day plan",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": (
                f"{GPX_NS} http://www.topografix.com/GPX/1/1/gpx.xsd "
                f"{GPXX_NS} http://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd "
                f"{WPTX_NS} http://www8.garmin.com/xmlschemas/WaypointExtensionv1.xsd"
            ),
        },
    )
    meta = ET.SubElement(gpx, f"{{{GPX_NS}}}metadata")
    ET.SubElement(meta, f"{{{GPX_NS}}}name").text = "Vita Bandet 2027 - alt 25 km camps"
    ET.SubElement(meta, f"{{{GPX_NS}}}desc").text = (
        "Alternative pacing: 11 / 17 / then ~25 km/day; resupply = 4 h + overnight. "
        "Track from 2027.GPX. Import into Garmin BaseCamp."
    )
    ET.SubElement(meta, f"{{{GPX_NS}}}time").text = f"{date.today().isoformat()}T12:00:00Z"

    for c in camps:
        w = ET.SubElement(
            gpx, f"{{{GPX_NS}}}wpt", {"lat": f"{c.lat:.8f}", "lon": f"{c.lon:.8f}"}
        )
        # GPX 1.1 / BaseCamp require: ele before name/desc/sym
        if c.elev_m is not None:
            ET.SubElement(w, f"{{{GPX_NS}}}ele").text = f"{c.elev_m:.1f}"
        tag = " D" if c.is_resupply else ""
        elev = f" · camp {c.elev_m:.0f} m" if c.elev_m is not None else ""
        ud = ""
        if c.up_m is not None and c.down_m is not None:
            ud = f" · +{c.up_m} m -{c.down_m} m"
        note = c.note.replace("★ ", "").replace("★", "")
        ET.SubElement(w, f"{{{GPX_NS}}}name").text = f"A{c.day:02d}{tag} · {c.label}"
        ET.SubElement(w, f"{{{GPX_NS}}}cmt").text = (
            f"Day {c.day} · {c.km_from_prev:.0f} km (cum {c.cum_km:.0f})"
            f"{ud}{elev} · {note}"
        )
        ET.SubElement(w, f"{{{GPX_NS}}}desc").text = (
            f"Day {c.day} · {c.km_from_prev:.0f} km (cum {c.cum_km:.0f})"
            f"{ud}{elev} · {note}"
        )
        ET.SubElement(w, f"{{{GPX_NS}}}sym").text = (
            "Flag, Blue" if c.is_resupply else "Campground"
        )
        ET.SubElement(w, f"{{{GPX_NS}}}type").text = "user"
        ext = ET.SubElement(w, f"{{{GPX_NS}}}extensions")
        gpxx = ET.SubElement(ext, f"{{{GPXX_NS}}}WaypointExtension")
        ET.SubElement(gpxx, f"{{{GPXX_NS}}}DisplayMode").text = "SymbolAndName"
        cats = ET.SubElement(gpxx, f"{{{GPXX_NS}}}Categories")
        ET.SubElement(cats, f"{{{GPXX_NS}}}Category").text = (
            "Food" if c.is_resupply else ("Lodging" if c.label == FINISH_LABEL else "Camping")
        )
        wptx = ET.SubElement(ext, f"{{{WPTX_NS}}}WaypointExtension")
        ET.SubElement(wptx, f"{{{WPTX_NS}}}DisplayMode").text = "SymbolAndName"

    # Full route track (simplified every ~200 m for file size)
    trk = ET.SubElement(gpx, f"{{{GPX_NS}}}trk")
    ET.SubElement(trk, f"{{{GPX_NS}}}name").text = "2027 plan track (alt 25 km)"
    seg = ET.SubElement(trk, f"{{{GPX_NS}}}trkseg")
    last_m = -1e9
    for i, (lat, lon) in enumerate(pts):
        if cum[i] - last_m < 200 and i not in (0, len(pts) - 1):
            continue
        ET.SubElement(seg, f"{{{GPX_NS}}}trkpt", {"lat": f"{lat:.8f}", "lon": f"{lon:.8f}"})
        last_m = cum[i]

    rough = ET.tostring(gpx, encoding="utf-8", xml_declaration=True)
    pretty = minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")
    # Drop blank text-only lines minidom sometimes inserts
    lines = [ln for ln in pretty.splitlines() if ln.strip()]
    GPX_OUT.write_bytes(b"\n".join(lines) + b"\n")
    print(f"Wrote {GPX_OUT} (BaseCamp)")


def write_markdown(camps: list[Camp]) -> None:
    n = len(camps)
    total = camps[-1].cum_km
    end = START_DATE + timedelta(days=n - 1)
    lines = [
        "# Vita Bandet 2027 — alternative day plan (~25 km cruise)",
        "",
        f"**Pacing:** Day 1 **{DAY1_KM:.0f} km** · Day 2 **{DAY2_KM:.0f} km** · then **~{CRUISE_KM:.0f} km/day**.  ",
        f"**Route:** [`2027.GPX`](../tracks/2027.GPX) · camps GPX: [`2027-alt-25km-camps.gpx`](../tracks/2027-alt-25km-camps.gpx).  ",
        f"**Season:** {START_DATE.strftime('%d %b %Y').lstrip('0')} → {end.strftime('%d %b %Y').lstrip('0')} (**{n} days** · **~{total:.0f} km**).  ",
        f"**Baseline plan:** [dag-for-dag-2027.md](./dag-for-dag-2027.md) (~70 days · ~18–22 km).  ",
        "",
        "**Camps:** snapped to named pins when nearby; otherwise lowest elevation within "
        f"±{SEARCH_WINDOW_KM:.0f} km of target.  ",
        "**★ Resupply:** land overnight at shop; budget **4 hours** for food/fuel/repack "
        "(Storlien · Valsjöbua · Gäddede · Hemavan · Kvikkjokk · Ritsem · Abisko).",
        "",
        "> Alternative pacing only — VGB väster om waypoints and fuel strategy still follow "
        "the main plan / [resupply-2027.md](./resupply-2027.md).",
        "",
        "## Summary",
        "",
        "| | |",
        "|--|--|",
        f"| Days | **{n}** |",
        f"| Distance | **~{total:.0f} km** |",
        f"| Mean day (D3+) | **~{sum(c.km_from_prev for c in camps[2:]) / max(1, n - 2):.1f} km** |",
        f"| ★ Resupply nights | **{sum(1 for c in camps if c.is_resupply)}** × 4 h |",
    ]
    if camps[0].up_m is not None:
        tot_up = sum(c.up_m or 0 for c in camps)
        tot_down = sum(c.down_m or 0 for c in camps)
        lines += [
            f"| Total ↑ / ↓ | **↑{tot_up:,} m** · **↓{tot_down:,} m** (EU-DEM 25 m) |",
        ]
    lines += [
        "",
        "*Elevation:* camp height + day ↑/↓ from OpenTopoData **EU-DEM 25 m** along the track "
        "(same source as the baseline plan — rough guide; DEM noise on flat ice).",
        "",
        "## Milestones",
        "",
        "| Date | Place | Cum. km | Camp elev |",
        "|------|-------|---------|----------:|",
    ]
    for c in camps:
        if c.is_resupply or c.label == FINISH_LABEL or c.day in (1,):
            dt = START_DATE + timedelta(days=c.day - 1)
            star = " · **D** ★" if c.is_resupply else (" · **GOAL**" if c.label == FINISH_LABEL else "")
            elev = f"{c.elev_m:.0f} m" if c.elev_m is not None else "—"
            lines.append(
                f"| {dt.strftime('%d %b').lstrip('0')} | {c.label}{star} | {c.cum_km:.0f} | {elev} |"
            )

    lines += [
        "",
        "## Day-by-day",
        "",
        "| Day | Date | km | Cum | ↑ m | ↓ m | Camp m | Camp | Notes |",
        "|----:|------|---:|----:|----:|----:|-------:|------|-------|",
    ]
    for c in camps:
        dt = START_DATE + timedelta(days=c.day - 1)
        elev = f"{c.elev_m:.0f}" if c.elev_m is not None else "—"
        up = f"{c.up_m}" if c.up_m is not None else "—"
        down = f"{c.down_m}" if c.down_m is not None else "—"
        notes = c.note
        if c.is_resupply:
            notes = "**D** ★ · 4 h resupply · overnight"
        lines.append(
            f"| {c.day} | {dt.strftime('%a %d %b').replace(' 0', ' ')} | {c.km_from_prev:.0f} | {c.cum_km:.0f} | "
            f"{up} | {down} | {elev} | {c.label} | {notes} |"
        )

    lines += [
        "",
        "## Resupply days (4 h)",
        "",
        "Arrive with enough daylight (or overnight + morning shop). Typical block:",
        "",
        "1. Pitch / check in (**H** or **T**).  ",
        "2. **~4 h:** food + alkylate + laundry/charge + repack pulk boxes.  ",
        "3. No further ski that calendar day (camp at shop).",
        "",
        "| Day | Shop | Cum km |",
        "|----:|------|-------:|",
    ]
    for c in camps:
        if c.is_resupply:
            lines.append(f"| {c.day} | {c.label} | {c.cum_km:.0f} |")

    lines += [
        "",
        "---",
        "",
        f"*Generated by `scripts/build_alt_day_plan.py` · {date.today().isoformat()}*",
        "",
    ]
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {MD_OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-elev", action="store_true", help="Skip elevation fetch")
    args = ap.parse_args()

    print("Loading track…")
    pts, cum = load_track()
    print(f"  {len(pts)} pts · {cum[-1]/1000:.1f} km")
    named = load_named_pins(pts, cum)
    print(f"  {len(named)} named pins on track")
    print("Resolving ★ resupply…")
    shops = resolve_resupply(pts, cum, named)

    sample_km: list[float] = []
    eles: list[float] = []
    if not args.no_elev:
        print("Fetching elevation profile (1 km)…")
        sample_km, eles = fetch_elev_profile(pts, cum, step_m=1000.0)
    else:
        print("Skipping elevation (--no-elev)")

    camps = build_camps(pts, cum, sample_km, eles, named, shops)
    print(f"Built {len(camps)} days · finish {camps[-1].cum_km:.0f} km")
    for c in camps:
        if c.is_resupply or c.day <= 3 or c.label == FINISH_LABEL:
            print(
                f"  D{c.day:02d} {c.km_from_prev:5.1f} km → {c.label} "
                f"(cum {c.cum_km:.0f})" + (" ★" if c.is_resupply else "")
            )

    write_markdown(camps)
    write_gpx(camps, pts, cum)


if __name__ == "__main__":
    main()
