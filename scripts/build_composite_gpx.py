#!/usr/bin/env python3
"""
Stitch historical Band tracks into one GPX for the 2028 plan route.

Segment sources (best match per dag-for-dag-2028.md):
  Grövelsjön → Helags       Erik (95 pts G→Rogen, max gap 0.8 km; Mårten was
                                  39 pts max 2.5 km. Erik also passes 1.3 km
                                  west of Helags station — VGB-väster-om.)
  Helags → Storlien         Lotta & Björn (passes Blåhammaren +0.18 km AND
                                  Storlien +0.44 km. Mårten skipped both:
                                  Blåhammaren +9.5 km, Storlien +10.5 km.)
  Storlien → Gäddede        Lotta & Björn (Storlien +0.44 km vs Mårten +10.5
                                  km — keeps Storlien seam clean. Comparable
                                  density: 434 pts max 1.6 km vs Mårten 488/1.4.)
  Gäddede → Lapplandsleden  Ola (Mårten has 16.7 km hole at Klimpf — bad match)
  Lapplandsleden → Hemavan  lapland-trail-summer.gpx (marked trail via Klimpf)
  Hemavan → Jäckvik → Kvikkjokk  Mårten (Jäckvik W +0.9 km; Erik +0.1 km — tie)
  Kvikkjokk → Abisko        Paolo (Padjelanta-west corridor — Mårten goes KL,
                                    off Ritsem by 29 km, off plan)
  Abisko → Pältsa           Mårten (dense; Ola: 59 pts, max gap 9.9 km)

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
    "ROGEN": (62.3414, 12.4034),  # DNT Rogenstugan
    "HELAGS": (62.917359, 12.506156),
    "BLAHAMM": (63.187081, 12.174362),  # STF Blåhammaren
    "STORLIEN": (63.298, 12.101),
    "GADDEDE": (64.52, 14.14),
    "KLIMPF": (65.067, 14.770),
    "HEMAVAN": (65.83, 15.08),
    "JACKVIK": (66.383, 16.967),
    "KVIKK": (66.9513, 17.7285),
    "SALKA": (67.946376, 18.281701),
    "ABISKO": (68.35, 18.83),
    "TRERIK": (69.06, 20.55),
    "PALTSA": (69.045, 20.739),
}

# Camp stops per section — cum km from dag-for-dag-2028.md (placed on composite track)
# (section, [trkseg indices], start_cum_km, [(day, date, cum_km, place, acc, note, pin_milestone)])
# pin_milestone overrides interpolated position (used for resupply pins on milestone coords)
SECTION1_CAMPS = [
    (1, "2028-02-15", 8, "Långfjället approach", "T", "Camp N of STF Grövelsjön", None),
    (2, "2028-02-16", 20, "Långfjället", "T", "", None),
    (3, "2028-02-17", 34, "Tännäs", "T", "", None),
    (4, "2028-02-18", 50, "Ljusnedal", "T", "", None),
    (5, "2028-02-19", 67, "Vålådalen", "T", "", None),
    (6, "2028-02-20", 85, "Ottfjället", "T", "", None),
    (7, "2028-02-21", 104, "Sylarna W", "T", "Stations closed", None),
    (8, "2028-02-22", 124, "Håkafot W", "T", "VGB väster om", None),
    (9, "2028-02-23", 165, "Storlien", "D", "Coop · resupply", "STORLIEN"),
]

SECTION2_CAMPS = [
    (10, "2028-02-24", 183, "Skalstugan corridor", "T", "Carry 10–12 days food", None),
    (11, "2028-02-25", 202, "Anjan / Kolåsen approach", "T", "Depot optional", None),
    (12, "2028-02-26", 222, "Undersåker W", "T", "VGB väster om · bridge east", None),
    (13, "2028-02-27", 242, "Hotagen fringe", "T", "Remote · no scooter spår", None),
    (14, "2028-02-28", 262, "Olden / Valsjöbyn", "T", "Optional D Valsjöbyn", None),
    (15, "2028-02-29", 282, "Frostviken south", "T", "", None),
    (16, "2028-03-01", 302, "Hällingsåfallet", "T", "Steep valley sides", None),
    (17, "2028-03-02", 322, "Vilhelmina north", "T", "", None),
    (18, "2028-03-03", 342, "Storjuktan", "T", "Lake ice — verify locally", None),
    (19, "2028-03-04", 362, "Björkvattnet", "T", "", None),
    (20, "2028-03-05", 382, "Gäddede approach", "T", "Light day before D", None),
    (21, "2028-03-06", 400, "Gäddede fringe", "T", "Camp near village", None),
    (22, "2028-03-07", 415, "Gäddede", "D", "ICA · Frostvikens · 9–10 days food", "GADDEDE"),
]

# (camp list, list of trkseg indices that contain the section, cum km at start of section)
CAMP_SECTIONS = [
    ("Section 1", SECTION1_CAMPS, [0, 1], 0),
    ("Section 2", SECTION2_CAMPS, [2], 165),
]

SEGMENTS = [
    ("Grövelsjön → Helags", "eriks-band-track.json", "GROVEL", "HELAGS"),
    ("Helags → Blåhammaren → Storlien", "lottas-och-bjorns-band-track.json", "HELAGS", "STORLIEN"),
    ("Storlien → Gäddede", "lottas-och-bjorns-band-track.json", "STORLIEN", "GADDEDE"),
    ("Gäddede → Lapplandsleden", "olas-vita-band-2-track.json", "GADDEDE", "LAPLAND_JOIN"),
    (
        "Lapplandsleden → Hemavan",
        "lapland-trail-summer.gpx",
        "LAPLAND_JOIN",
        "HEMAVAN",
    ),
    ("Hemavan → Jäckvik → Kvikkjokk", "martens-band-track.json", "HEMAVAN", "KVIKK"),
    ("Kvikkjokk → Abisko", "paolo-peralta-s-band-track.json", "KVIKK", "ABISKO"),
    ("Abisko → Pältsa", "martens-band-track.json", "ABISKO", "PALTSA"),
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


def load_track(path: Path) -> list[dict]:
    if path.suffix.lower() == ".gpx":
        root = ET.parse(path).getroot()
        ns = {"gpx": GPX_NS}
        locs: list[dict] = []
        for trkpt in root.findall(".//gpx:trkpt", ns):
            locs.append({"lat": float(trkpt.get("lat")), "lng": float(trkpt.get("lon"))})
        if not locs:
            raise ValueError(f"No trkpt in {path}")
        return locs
    data = json.load(open(path, encoding="utf-8"))
    return data["locations"]


def write_track_gpx(path: Path, locs: list[dict], name: str, desc: str = "") -> None:
    gpx = Element(
        "gpx",
        attrib={"version": "1.1", "creator": "VitaBandet", "xmlns": GPX_NS},
    )
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = name
    if desc:
        SubElement(meta, "desc").text = desc
    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = name
    seg = SubElement(trk, "trkseg")
    for p in locs:
        SubElement(
            seg,
            "trkpt",
            attrib={"lat": f"{p['lat']:.6f}", "lon": f"{p['lng']:.6f}"},
        )
    rough = ET.tostring(gpx, encoding="unicode")
    parsed = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?>\n' + rough)
    path.write_text(parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8"), encoding="utf-8")


def ensure_lapland_s_to_n(path: Path) -> list[dict]:
    locs = load_track(path)
    hemavan = MILESTONES["HEMAVAN"]
    start_at_hemavan = haversine_m(
        locs[0]["lat"], locs[0]["lng"], hemavan[0], hemavan[1]
    ) < haversine_m(locs[-1]["lat"], locs[-1]["lng"], hemavan[0], hemavan[1])
    if start_at_hemavan:
        locs = list(reversed(locs))
        write_track_gpx(
            path,
            locs,
            "Lapplandsleden S→N",
            "Reordered south to north for Vita Bandet (was summer export Hemavan→south).",
        )
        print(f"  Reordered {path.name} to S→N ({len(locs)} points)")
    return locs


def lapland_join_idx_on_band(locs: list, from_idx: int, summer: list[dict]) -> int:
    """First Band point within 500 m of Lapplandsleden (Ola/Paolo west corridor)."""
    ig = nearest_idx(summer, MILESTONES["GADDEDE"])
    ih = nearest_idx(summer, MILESTONES["HEMAVAN"])
    for i in range(from_idx, len(locs)):
        j = min(
            range(ig, ih + 1),
            key=lambda k: haversine_m(
                locs[i]["lat"], locs[i]["lng"], summer[k]["lat"], summer[k]["lng"]
            ),
        )
        if haversine_m(locs[i]["lat"], locs[i]["lng"], summer[j]["lat"], summer[j]["lng"]) <= 500:
            return i
    for i in range(from_idx, len(locs)):
        j = min(
            range(ig, ih + 1),
            key=lambda k: haversine_m(
                locs[i]["lat"], locs[i]["lng"], summer[k]["lat"], summer[k]["lng"]
            ),
        )
        if haversine_m(locs[i]["lat"], locs[i]["lng"], summer[j]["lat"], summer[j]["lng"]) <= 2000:
            return i
    return from_idx


def lapland_join_idx_on_summer(locs: list, band_join: dict) -> int:
    """Summer GPX index at the Band join (Paolo/Jonathan corridor)."""
    ig = nearest_idx(locs, MILESTONES["GADDEDE"])
    ih = nearest_idx(locs, MILESTONES["HEMAVAN"])
    return min(
        range(ig, ih + 1),
        key=lambda i: haversine_m(
            locs[i]["lat"], locs[i]["lng"], band_join["lat"], band_join["lng"]
        ),
    )


def extract_segment(
    locs: list,
    start_key: str,
    end_key: str,
    *,
    summer: list[dict] | None = None,
    lapland_join: dict | None = None,
) -> list[dict]:
    if start_key == "LAPLAND_JOIN" and end_key == "HEMAVAN":
        return extract_lapland_to_hemavan(locs, lapland_join)

    i0 = nearest_idx(locs, MILESTONES[start_key])
    if end_key == "LAPLAND_JOIN":
        if summer is None:
            raise ValueError("summer track required for LAPLAND_JOIN")
        i1 = lapland_join_idx_on_band(locs, i0, summer)
    else:
        i1 = nearest_idx(locs, MILESTONES[end_key])
    if i0 <= i1:
        return [dict(p) for p in locs[i0 : i1 + 1]]
    return [dict(p) for p in locs[i1 : i0 + 1][::-1]]


def extract_lapland_to_hemavan(locs: list[dict], band_join: dict | None) -> list[dict]:
    """Marked Lapplandsleden from Band join (S→N) to Hemavan — full summer geometry."""
    ih = nearest_idx(locs, MILESTONES["HEMAVAN"])
    if band_join is not None:
        ik = lapland_join_idx_on_summer(locs, band_join)
    else:
        ik = nearest_idx(locs, MILESTONES["GADDEDE"])
    if ik >= ih:
        raise ValueError("Lapplandsleden join is not south of Hemavan on S→N GPX")
    return [dict(p) for p in locs[ik : ih + 1]]


def thin_points(points: list[dict], min_gap_m: float) -> list[dict]:
    """Drop points closer than min_gap_m (Band JSON only)."""
    if not points:
        return []
    out = [points[0]]
    for p in points[1:]:
        last = out[-1]
        if haversine_m(last["lat"], last["lng"], p["lat"], p["lng"]) >= min_gap_m:
            out.append(p)
    return out


def point_at_planned_km(points: list[dict], target_km: float) -> dict:
    """Interpolate a point along the track at planned cumulative km."""
    if not points:
        raise ValueError("empty track")
    if target_km <= 0:
        return dict(points[0])
    cum = 0.0
    for i in range(1, len(points)):
        leg = haversine_m(
            points[i - 1]["lat"],
            points[i - 1]["lng"],
            points[i]["lat"],
            points[i]["lng"],
        ) / 1000
        if cum + leg >= target_km:
            frac = (target_km - cum) / leg if leg > 0 else 0.0
            a, b = points[i - 1], points[i]
            return {
                "lat": a["lat"] + frac * (b["lat"] - a["lat"]),
                "lng": a["lng"] + frac * (b["lng"] - a["lng"]),
            }
        cum += leg
    return dict(points[-1])


def camp_waypoints(trksegs: list[tuple[str, list[dict]]]) -> list[dict]:
    """Camp / resupply waypoints for all defined sections on the stitched track."""
    wpts: list[dict] = []
    for section_label, camps, seg_indices, start_cum_km in CAMP_SECTIONS:
        track: list[dict] = []
        for i in seg_indices:
            if i < len(trksegs):
                track.extend(trksegs[i][1])
        for day, date, cum_km, place, acc, note, pin_milestone in camps:
            if pin_milestone and pin_milestone in MILESTONES:
                lat, lon = MILESTONES[pin_milestone]
            else:
                rel_km = cum_km - start_cum_km
                p = point_at_planned_km(track, rel_km)
                lat, lon = p["lat"], p["lng"]
            desc = f"{section_label} · {date} · cum {cum_km} km · {acc}"
            if note:
                desc += f" · {note}"
            sym = "Campground" if acc == "T" else "City"
            wpts.append(
                {
                    "name": f"D{day} · {place}",
                    "lat": lat,
                    "lon": lon,
                    "desc": desc,
                    "sym": sym,
                    "type": "camp" if acc == "T" else "resupply",
                }
            )
    return wpts


def assign_plan_times(points: list[dict], start: datetime, end: datetime) -> None:
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


def add_waypoint(
    gpx: Element,
    name: str,
    lat: float,
    lon: float,
    *,
    desc: str = "",
    sym: str | None = None,
    wpt_type: str | None = None,
) -> None:
    w = SubElement(gpx, "wpt", attrib={"lat": f"{lat:.6f}", "lon": f"{lon:.6f}"})
    SubElement(w, "name").text = name
    if desc:
        SubElement(w, "desc").text = desc
    if sym:
        SubElement(w, "sym").text = sym
    if wpt_type:
        SubElement(w, "type").text = wpt_type


def build_gpx(
    trksegs: list[tuple[str, list[dict]]],
    name: str,
    *,
    camp_wpts: list[dict] | None = None,
) -> str:
    gpx = Element(
        "gpx",
        attrib={"version": "1.1", "creator": "VitaBandet composite", "xmlns": GPX_NS},
    )
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = name
    desc = SubElement(meta, "desc")
    desc.text = (
        "Composite route for Vita Bandet 2028. "
        "Each leg is a separate trkseg (no straight lines across joins). "
        "Sources: Erik (Grövelsjön→Helags — dense Långfjället+Rogen, VGB-väster-om at Helags), "
        "Lotta & Björn (Helags→Storlien→Gäddede — passes Blåhammaren and Storlien village), "
        "Mårten (Hemavan→Kvikkjokk, Abisko→Pältsa), "
        "Ola (Gäddede→Lapplandsleden join), "
        "lapland-trail-summer.gpx (Lapplandsleden→Hemavan via Klimpfjäll), "
        "Paolo (Kvikkjokk→Abisko via Padjelanta-west corridor)."
    )

    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = name

    for label, points in trksegs:
        if not points:
            continue
        seg = SubElement(trk, "trkseg")
        for p in points:
            att = {
                "lat": f"{p['lat']:.8f}".rstrip("0").rstrip("."),
                "lon": f"{p['lng']:.8f}".rstrip("0").rstrip("."),
            }
            trkpt = SubElement(seg, "trkpt", attrib=att)
            if p.get("_iso"):
                SubElement(trkpt, "time").text = p["_iso"]

    for camp in camp_wpts or []:
        add_waypoint(
            gpx,
            camp["name"],
            camp["lat"],
            camp["lon"],
            desc=camp.get("desc", ""),
            sym=camp.get("sym"),
            wpt_type=camp.get("type"),
        )

    for label, pt in [
        ("Grövelsjön", MILESTONES["GROVEL"]),
        ("Rogenstugan (DNT)", MILESTONES["ROGEN"]),
        ("Helags fjällstation", MILESTONES["HELAGS"]),
        ("Blåhammaren fjällstation", MILESTONES["BLAHAMM"]),
        ("Storlien", MILESTONES["STORLIEN"]),
        ("Gäddede", MILESTONES["GADDEDE"]),
        ("Klimpfjäll", MILESTONES["KLIMPF"]),
        ("Hemavan", MILESTONES["HEMAVAN"]),
        ("Jäckvik", MILESTONES["JACKVIK"]),
        ("Kvikkjokk", MILESTONES["KVIKK"]),
        ("Sälka", MILESTONES["SALKA"]),
        ("Abisko", MILESTONES["ABISKO"]),
        ("Treriksröset", MILESTONES["TRERIK"]),
    ]:
        add_waypoint(gpx, label, pt[0], pt[1])

    rough = ET.tostring(gpx, encoding="unicode")
    parsed = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?>\n' + rough)
    return parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")


def main() -> None:
    trksegs: list[tuple[str, list[dict]]] = []
    log: list[str] = []
    lapland_path = PLAN_DIR / "lapland-trail-summer.gpx"
    summer_locs: list[dict] | None = None
    lapland_join: dict | None = None
    lapland_end: dict | None = None

    for label, fname, sk, ek in SEGMENTS:
        path = PLAN_DIR / fname
        is_lapland = path.resolve() == lapland_path.resolve()
        if is_lapland:
            summer_locs = ensure_lapland_s_to_n(path)
            locs = summer_locs
        else:
            locs = load_track(path)

        if is_lapland:
            seg = extract_lapland_to_hemavan(locs, lapland_join)
            # Keep full Gaia point density on marked trail (no thinning)
            lapland_end = seg[-1]
            write_track_gpx(
                PLAN_DIR / "lapland-klimpf-hemavan.gpx",
                seg,
                "Lapplandsleden → Hemavan",
                "lapland-trail-summer.gpx from Ola/Paolo join (S→N) — not the 18 km Hemavan spur only.",
            )
        elif sk == "HEMAVAN" and lapland_end is not None:
            # Pick up the Band track at the Lapplandsleden end (near Hemavan) so
            # there's no overlap with the marked summer trail we just inserted.
            i0 = nearest_idx(locs, (lapland_end["lat"], lapland_end["lng"]))
            i1 = nearest_idx(locs, MILESTONES["KVIKK"])
            if i0 <= i1:
                seg = [dict(p) for p in locs[i0 : i1 + 1]]
            else:
                seg = extract_segment(locs, sk, ek)
            seg = thin_points(seg, 300.0)
        elif ek == "LAPLAND_JOIN":
            if summer_locs is None:
                summer_locs = ensure_lapland_s_to_n(lapland_path)
            seg = extract_segment(locs, sk, ek, summer=summer_locs)
            lapland_join = seg[-1]
            seg = thin_points(seg, 300.0)
        else:
            seg = extract_segment(locs, sk, ek, summer=summer_locs, lapland_join=lapland_join)
            if not is_lapland and "paolo-peralta" not in fname:
                seg = thin_points(seg, 300.0)

        trksegs.append((label, seg))
        log.append(f"  {label}: {len(seg)} pts")

    flat = [p for _, seg in trksegs for p in seg]
    assign_plan_times(flat, datetime(2028, 2, 15, 10, 0), datetime(2028, 4, 19, 12, 0))

    camp_wpts = camp_waypoints(trksegs)

    out = PLAN_DIR / "vita-bandet-2028-composite.gpx"
    out.write_text(
        build_gpx(trksegs, "Vita Bandet 2028 (composite)", camp_wpts=camp_wpts),
        encoding="utf-8",
    )

    km = sum(
        haversine_m(flat[i - 1]["lat"], flat[i - 1]["lng"], flat[i]["lat"], flat[i]["lng"])
        for i in range(1, len(flat))
    ) / 1000

    print(f"Wrote {len(flat)} points, {km:.0f} km, {len(trksegs)} trksegs → {out}")
    print(f"Wrote lapland leg → {PLAN_DIR / 'lapland-klimpf-hemavan.gpx'}\n")
    print("Segments:")
    for line in log:
        print(line)


if __name__ == "__main__":
    main()
