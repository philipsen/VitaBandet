#!/usr/bin/env python3
"""
Stitch historical Band tracks into a composite GPX for the 2028 plan route.

Output (all under tracks/generated/):
  - vita-bandet-2028-composite.gpx    Full route as 6 trksegs (one per Section)
  - section-1-grovelsjon-storlien.gpx Per-section GPX, with waypoints + camps
  - section-2-storlien-gaddede.gpx
  - section-3-gaddede-hemavan.gpx
  - section-4-hemavan-kvikkjokk.gpx
  - section-5-kvikkjokk-abisko.gpx
  - section-6-abisko-paltsa.gpx
  - lapland-klimpf-hemavan.gpx        Section 3 lapland-leg only (debug)

Section source mix (best match per dag-for-dag-2028.md):
  1 Grövelsjön → Storlien    Lotta & Björn (single dense track end-to-end:
                             Grövelsjön +0.33, Helags +0.04, Blåhammaren +0.18,
                             Storlien village +0.44 km — best match for plan)
  2 Storlien → Gäddede       Lotta & Björn (continuation — clean 0 km seam)
  3 Gäddede → Hemavan        Kalle (G→Klimpfjäll, 139 pts max 1.4 km — Ola was
                             17 pts max 13.8 km on this leg),
                             lapland-trail-summer.gpx (Klimpfjäll → Hemavan)
  4 Hemavan → Kvikkjokk      Mårten (Jäckvik W +0.9 km)
  5 Kvikkjokk → Abisko       2028 plan GPX (Garmin Desktop, 6 902 dense pts,
                             avg 38 m): §5 K→Sälka via Padjelanta-west / Ritsem
                             + §5b Sälka→Abisko via Kungsleden
  6 Abisko → Pältsa          2028-plan-abisko-paltsa.gpx (2028 nord.GPX from Downloads)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "tracks" / "source"
OUT_DIR = ROOT / "tracks" / "generated"
GPX_NS = "http://www.topografix.com/GPX/1/1"

MILESTONES = {
    "GROVEL": (62.10, 12.31),
    "HAVLINGEN": (62.216, 12.354),       # Länsstyrelsen Hävlingestugorna (Lake Hävlingen)
    "ROGEN": (62.316879, 12.450456),     # STF Rogen fjällstuga (Rogenstugan)
    "DALSTENHAN": (62.420, 12.286),      # Dalstenshån — north shore camp (Day 3)
    "HAMRA": (62.57427, 12.22619),       # Hamra Livs · Hamravägen 73, Hamra/Tännäs (Day 4 D)
    "SKARVRUET": (62.539318, 12.408265), # STF Skarvruet vandrarhem (separate area ~10 km E of Hamra Livs)
    "HELAGS": (62.917359, 12.506156),    # STF Helags fjällstation
    "SYLARNA": (63.045833, 12.259167),   # STF Sylarna fjällstation
    "BLAHAMM": (63.187081, 12.174362),   # STF Blåhammaren
    "STORLIEN": (63.298, 12.101),
    "NORDER_RENSJON": (63.416652, 12.225886),  # Norder-Rensjön — track leaves lake N end
    "KOLASEN": (63.713, 12.930),         # Kolåsens Fjällhotell area (on Band track)
    "OLDEN": (63.707, 13.107),           # Olden corridor (not Valsjöbua)
    "VALSJO": (64.068, 14.139),         # Valsjöbua Lanthandel
    "BLASJOFJALL": (64.836, 14.083),     # ICA Nära Blåsjöfjäll — ~35 km off Band track
    "GADDEDE": (64.52, 14.14),
    "KLIMPF": (65.067, 14.770),          # Klimpfjäll village
    "HEMAVAN": (65.83, 15.08),
    "JACKVIK": (66.383, 16.967),
    "KVIKK": (66.9513, 17.7285),
    "RITSEM": (67.7327, 17.4711),        # STF Ritsem (gateway to Padjelanta-west)
    "SALKA": (67.946376, 18.281701),     # STF Sälka
    "ABISKO": (68.35, 18.83),
    "TRERIK": (69.06, 20.55),
    "PALTSA": (69.045, 20.739),
    # Section 3 — Vildmarksvägen / Lapplandsleden
    "BORGAFJALL": (64.83, 15.07),
    "SAXNAS": (65.05, 15.32),
    # Section 4 — KL west
    "AMMARNAS": (65.9566, 16.2014),       # Ammarnäs Fritidscenter / STF Wärdshus area
    "ADOLFSTROM": (66.27749, 16.665675), # Adolfström Camping (Handelsbod ~66.10°N — call ahead)
    "VUOGGATJALME": (66.49, 16.55),
    # Section 5 — Padjelanta-west + KL
    "SALTOLUOKTA": (67.394089, 18.520761),  # STF Saltoluokta (optional east detour)
    "NIKKALUOKTA": (67.850827, 19.012983),  # Nikkaluokta Sarri camping
    # Section 6 — Nordkalottleden
    "LAPPJORD": (68.5539, 19.3364),       # DNT Lappjordhytta
    "ALTEVASS": (68.6723, 19.6981),       # DNT Altevasshytta (on nord GPX corridor)
    "BJORKLIDEN": (68.437, 18.279),       # Björkliden Camping (~10 km from Abisko; no RV in park)
}

# Camp stops per section — cum km from dag-for-dag-2028.md (placed along the
# section track by interpolated planned km). pin_milestone overrides position
# with literal milestone coords (resupply pins).
SECTION1_CAMPS = [
    (1, "2028-02-15",  14, "Hävlingestugorna", "T", "Länsstyrelsen stugor · ~13 km N of Grövelsjön", "HAVLINGEN"),
    (2, "2028-02-16",  29, "STF Rogen area", "T", "Tent sites ~100 m from hut · H optional if open (27 Feb–19 Apr)", "ROGEN"),
    (3, "2028-02-17",  44, "Dalstenshån N",          "T", "North shore · Rogen nature reserve", "DALSTENHAN"),
    (4, "2028-02-18",  60, "Tänndalen",            "D", "Hamra Livs resup · ~6 km detour west", "HAMRA"),
    (5, "2028-02-19",  72, "Band line west",       "T", "On track — STF Vålådalen is E detour only", None),
    (6, "2028-02-20",  90, "Helags approach",      "T", "Mot Helags / Långfjällen", None),
    (7, "2028-02-21", 109, "Helags väster om",     "T", "STF Helags · Sylarna/Blåhammaren ahead", "HELAGS"),
    (8, "2028-02-22", 129, "Sylarna väster om",    "T", "STF Sylarna · Blåhammaren tomorrow", "SYLARNA"),
    (9, "2028-02-23", 147, "Blåhammaren väster om", "T", "STF Blåhammaren · butik/self-catering", "BLAHAMM"),
    (10, "2028-02-24", 161, "Storlien",             "D", "Coop · resupply",           "STORLIEN"),
]

SECTION2_CAMPS = [
    (11, "2028-02-25", 183, "Norder Rensjön",        "T", "Track leaves north end of lake · carry 10–12 days food", None),
    (12, "2028-02-26", 201, "Anjan", "T", "Depot optional", None),
    (13, "2028-02-27", 219, "Hotagen väster om", "T", "Remote · toward Kolåsen", None),
    (14, "2028-02-28", 239, "Mot Kolåsen", "T", "Remote · no scooter spår", None),
    (15, "2028-02-29", 257, "Kolåsen", "T", "H optional · depot · restaurant prebook", "KOLASEN"),
    (16, "2028-03-01", 267, "Olden", "T", "On track — not Valsjöbua (that is D21)", "OLDEN"),
    (17, "2028-03-02", 285, "Frostviken", "T", "Undersåker väster om corridor (bridge ~55 km E)", None),
    (18, "2028-03-03", 303, "Ansättfjällen approach", "T", "", None),
    (19, "2028-03-04", 321, "Ansättfjällen väster om", "T", "", None),
    (20, "2028-03-05", 339, "Regnfallet", "T", "", None),
    (21, "2028-03-06", 357, "Valsjöbua", "D", "Valsjöbua ★ · Bandare vandrarhem", "VALSJO"),
    (22, "2028-03-07", 380, "Björkvattnet", "T", "After Valsjöbua resupply", None),
    (23, "2028-03-08", 402, "Gäddede väster om", "T", "Optional Blåsjö detour (~35 km off track)", None),
    (24, "2028-03-09", 423, "Gäddede", "D", "ICA · Frostvikens", "GADDEDE"),
]

SECTION3_CAMPS = [
    (25, "2028-03-10", 442, "Vilhelmina fjäll", "T", "Wild camp · ~10 days food to Hemavan", None),
    (26, "2028-03-11", 465, "Borgafjäll", "T", "Optional H Borgafjäll Hotell", "BORGAFJALL"),
    (27, "2028-03-12", 487, "Saxnäs", "T", "Optional D Marsfjällshandlarn", "SAXNAS"),
    (28, "2028-03-13", 509, "Pauträsk / Vitveden", "T", "", None),
    (29, "2028-03-14", 531, "Klimpfjäll", "T", "Optional D Handlar'n", "KLIMPF"),
    (30, "2028-03-15", 554, "Virisen", "T", "Lapplandsleden · cabins often closed Mar", None),
    (31, "2028-03-16", 576, "Tärnaby west", "T", "", None),
    (32, "2028-03-17", 598, "Atoklimpen approach", "T", "Exposed", None),
    (33, "2028-03-18", 615, "Hemavan", "D", "ICA Fjällboden · STF · Hemavan Fjällcenter camping", "HEMAVAN"),
    (34, "2028-03-19", 645, "Jäckvik W", "T", "W detour · optional ICA", "JACKVIK"),
]

SECTION4_CAMPS = [
    (35, "2028-03-20", 667, "Syterstuga west", "T", "Steep · KL west", None),
    (36, "2028-03-21", 689, "Tärnasjön", "T", "Ice travel · wind funnel", None),
    (37, "2028-03-22", 710, "Ammarnäs", "T", "Optional D Handlar'n · Fritidscenter camping", "AMMARNAS"),
    (38, "2028-03-23", 732, "Adolfström", "T", "Optional D/camping · Adolfström Camping", "ADOLFSTROM"),
    (39, "2028-03-24", 753, "Hornavan ice", "T", "Ice check AM only", None),
    (40, "2028-03-25", 775, "Vuoggatjålme", "H", "Optional middag · stuga/caravan site", "VUOGGATJALME"),
    (41, "2028-03-26", 797, "Aktse", "T", "", None),
    (42, "2028-03-27", 819, "Rapadalen west", "T", "Sarek views", None),
    (43, "2028-03-28", 841, "Sitojaure", "T", "STF tält + serviceavgift if hut open", None),
    (44, "2028-03-29", 863, "Kaitumjaure", "T", "", None),
    (45, "2028-03-30", 885, "Toward Kvikkjokk", "T", "", None),
    (46, "2028-03-31", 905, "Kvikkjokk", "D", "STF max stock · wild T + paid shower", "KVIKK"),
]

SECTION5_CAMPS = [
    (47, "2028-04-01", 922, "Kvikkjokk north", "T", "6–7 days food + all alkylate to Ritsem", None),
    (48, "2028-04-02", 940, "Padjelanta west", "T", "GPS essential", None),
    (49, "2028-04-03", 958, "Stora Sjøfallet", "T", "Laponia · no shops", None),
    (50, "2028-04-04", 976, "Saltoluokta side", "T", "W corridor · STF tent if east detour", None),
    (51, "2028-04-05", 993, "W of Saltoluokta", "T", "W Saltoluokta", None),
    (52, "2028-04-06", 1011, "Áhkká / Ritsem fjäll", "T", "", None),
    (53, "2028-04-07", 1029, "Ritsem approach", "T", "", None),
    (54, "2028-04-08", 1045, "Ritsem", "D", "Power Fuel alkylate · STF H", "RITSEM"),
    (55, "2028-04-09", 1063, "Sitojaure", "H", "KL · optional hut top-up", None),
    (56, "2028-04-10", 1081, "Hukejaure", "T", "W Nikkaluokta · Sarri camping optional", None),
    (57, "2028-04-11", 1098, "Sälka", "H", "STF Sälka · tent if full", "SALKA"),
    (58, "2028-04-12", 1116, "Tjäktja", "T", "Steep pass", None),
    (59, "2028-04-13", 1134, "Alesjaure", "T", "STF tält at hut", None),
    (60, "2028-04-14", 1152, "Abiskojaure", "T", "Last hut before Abisko village", None),
    (61, "2028-04-15", 1170, "Abisko", "D", "Fjällboden · STF tent site · Björkliden RV ~10 km", "ABISKO"),
]

SECTION6_CAMPS = [
    (62, "2028-04-16", 1192, "Abisko north", "T", "7–8 days food + ~2 L alkylate", None),
    (63, "2028-04-17", 1214, "Nikkaluokta W", "T", "W corridor · Sarri camping optional", "NIKKALUOKTA"),
    (64, "2028-04-18", 1234, "Lappjordhytta", "H", "DNT · no pantry", "LAPPJORD"),
    (65, "2028-04-19", 1256, "Altevasshytta", "H", "DNT · no pantry", "ALTEVASS"),
    (66, "2028-04-20", 1273, "Treriksröset", "GOAL", "W goal · wide corridor OK", "TRERIK"),
    (67, "2028-04-21", 1283, "Pältsa", "D", "STF shop · trip end", "PALTSA"),
]


@dataclass
class SubSegment:
    label: str
    source: str              # filename under SRC_DIR
    start: str               # milestone key
    end: str                 # milestone key (or "LAPLAND_JOIN")


@dataclass
class Section:
    id: int
    title: str
    filename: str
    subsegments: list[SubSegment]
    waypoints: list[str]                 # milestone keys to pin in the per-section GPX
    camps: list[tuple] = field(default_factory=list)
    start_cum_km: int = 0


SECTIONS: list[Section] = [
    Section(
        id=1,
        title="Grövelsjön → Storlien",
        filename="section-1-grovelsjon-storlien.gpx",
        subsegments=[
            SubSegment("Grövelsjön → Helags → Blåhammaren → Storlien",
                       "lottas-och-bjorns-band-track.json", "GROVEL", "STORLIEN"),
        ],
        waypoints=["GROVEL", "HAVLINGEN", "ROGEN", "DALSTENHAN", "HAMRA", "SKARVRUET",
                   "HELAGS", "SYLARNA", "BLAHAMM", "STORLIEN"],
        camps=SECTION1_CAMPS,
        start_cum_km=0,
    ),
    Section(
        id=2,
        title="Storlien → Gäddede",
        filename="section-2-storlien-gaddede.gpx",
        subsegments=[
            SubSegment("Storlien → Gäddede",
                       "lottas-och-bjorns-band-track.json", "STORLIEN", "GADDEDE"),
        ],
        waypoints=["STORLIEN", "NORDER_RENSJON", "KOLASEN", "OLDEN", "VALSJO", "BLASJOFJALL", "GADDEDE"],
        camps=SECTION2_CAMPS,
        start_cum_km=161,
    ),
    Section(
        id=3,
        title="Gäddede → Hemavan",
        filename="section-3-gaddede-hemavan.gpx",
        subsegments=[
            SubSegment("Gäddede → Klimpfjäll (Kalle)",
                       "kalles-band-track.json", "GADDEDE", "KLIMPF"),
            SubSegment("Klimpfjäll → Hemavan (Lapplandsleden)",
                       "lapland-trail-summer.gpx", "KLIMPF", "HEMAVAN"),
        ],
        waypoints=["GADDEDE", "BORGAFJALL", "SAXNAS", "KLIMPF", "HEMAVAN", "JACKVIK"],
        camps=SECTION3_CAMPS,
        start_cum_km=423,
    ),
    Section(
        id=4,
        title="Hemavan → Kvikkjokk",
        filename="section-4-hemavan-kvikkjokk.gpx",
        subsegments=[
            SubSegment("Hemavan → Jäckvik → Kvikkjokk",
                       "martens-band-track.json", "HEMAVAN", "KVIKK"),
        ],
        waypoints=["HEMAVAN", "JACKVIK", "AMMARNAS", "ADOLFSTROM", "VUOGGATJALME", "KVIKK"],
        camps=SECTION4_CAMPS,
        start_cum_km=645,
    ),
    Section(
        id=5,
        title="Kvikkjokk → Abisko",
        filename="section-5-kvikkjokk-abisko.gpx",
        subsegments=[
            SubSegment("§5  Kvikkjokk → Sälka (Padjelanta-west / Ritsem)",
                       "2028-plan-kvikkjokk-abisko.gpx", "KVIKK", "SALKA"),
            SubSegment("§5b Sälka → Abisko (Kungsleden)",
                       "2028-plan-kvikkjokk-abisko.gpx", "SALKA", "ABISKO"),
        ],
        waypoints=["KVIKK", "RITSEM", "SALTOLUOKTA", "SALKA", "NIKKALUOKTA", "ABISKO", "BJORKLIDEN"],
        camps=SECTION5_CAMPS,
        start_cum_km=905,
    ),
    Section(
        id=6,
        title="Abisko → Pältsa",
        filename="section-6-abisko-paltsa.gpx",
        subsegments=[
            SubSegment("Abisko → Pältsa (2028 plan)",
                       "2028-plan-abisko-paltsa.gpx", "ABISKO", "PALTSA"),
        ],
        waypoints=["ABISKO", "NIKKALUOKTA", "LAPPJORD", "ALTEVASS", "TRERIK", "PALTSA"],
        camps=SECTION6_CAMPS,
        start_cum_km=1170,
    ),
]


# ----------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_idx(locs: list[dict], pt: tuple[float, float]) -> int:
    return min(
        range(len(locs)),
        key=lambda i: haversine_m(locs[i]["lat"], locs[i]["lng"], pt[0], pt[1]),
    )


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
    """Interpolate a point along the track at planned cumulative km from start."""
    if not points:
        raise ValueError("empty track")
    if target_km <= 0:
        return dict(points[0])
    cum = 0.0
    for i in range(1, len(points)):
        leg = haversine_m(
            points[i - 1]["lat"], points[i - 1]["lng"],
            points[i]["lat"], points[i]["lng"],
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


# ----------------------------------------------------------------------------
# source loading
# ----------------------------------------------------------------------------

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


def ensure_lapland_s_to_n(path: Path) -> list[dict]:
    locs = load_track(path)
    hemavan = MILESTONES["HEMAVAN"]
    start_at_hemavan = haversine_m(
        locs[0]["lat"], locs[0]["lng"], hemavan[0], hemavan[1]
    ) < haversine_m(locs[-1]["lat"], locs[-1]["lng"], hemavan[0], hemavan[1])
    if start_at_hemavan:
        locs = list(reversed(locs))
        write_track_gpx(
            path, locs,
            "Lapplandsleden S→N",
            "Reordered south to north for Vita Bandet (was summer export Hemavan→south).",
        )
        print(f"  Reordered {path.name} to S→N ({len(locs)} points)")
    return locs


# ----------------------------------------------------------------------------
# segment extraction
# ----------------------------------------------------------------------------

def lapland_join_idx_on_band(locs: list, from_idx: int, summer: list[dict]) -> int:
    """First Band point within 500 m of Lapplandsleden between Gäddede and Hemavan."""
    ig = nearest_idx(summer, MILESTONES["GADDEDE"])
    ih = nearest_idx(summer, MILESTONES["HEMAVAN"])
    for threshold in (500, 2000):
        for i in range(from_idx, len(locs)):
            j = min(
                range(ig, ih + 1),
                key=lambda k: haversine_m(
                    locs[i]["lat"], locs[i]["lng"], summer[k]["lat"], summer[k]["lng"]
                ),
            )
            if haversine_m(locs[i]["lat"], locs[i]["lng"], summer[j]["lat"], summer[j]["lng"]) <= threshold:
                return i
    return from_idx


def lapland_join_idx_on_summer(locs: list, band_join: dict) -> int:
    ig = nearest_idx(locs, MILESTONES["GADDEDE"])
    ih = nearest_idx(locs, MILESTONES["HEMAVAN"])
    return min(
        range(ig, ih + 1),
        key=lambda i: haversine_m(
            locs[i]["lat"], locs[i]["lng"], band_join["lat"], band_join["lng"]
        ),
    )


def extract_band_segment(locs: list, start_key: str, end_key: str) -> list[dict]:
    i0 = nearest_idx(locs, MILESTONES[start_key])
    i1 = nearest_idx(locs, MILESTONES[end_key])
    if i0 <= i1:
        return [dict(p) for p in locs[i0 : i1 + 1]]
    return [dict(p) for p in locs[i1 : i0 + 1][::-1]]


# ----------------------------------------------------------------------------
# build per-section tracks
# ----------------------------------------------------------------------------

def build_section_track(
    section: Section,
    state: dict,
) -> list[tuple[str, list[dict]]]:
    """Return list of (sublabel, points) so the per-section GPX can show each
    sub-source as its own trkseg if desired. For the composite they get
    concatenated into one trkseg per section."""
    out: list[tuple[str, list[dict]]] = []
    subs = section.subsegments
    for idx, sub in enumerate(subs):
        path = SRC_DIR / sub.source
        is_lapland_summer = sub.source == "lapland-trail-summer.gpx"
        next_is_lapland = (
            idx + 1 < len(subs)
            and subs[idx + 1].source == "lapland-trail-summer.gpx"
        )

        if is_lapland_summer:
            summer_locs = state["summer_locs"]
            if summer_locs is None:
                summer_locs = ensure_lapland_s_to_n(path)
                state["summer_locs"] = summer_locs
            ih = nearest_idx(summer_locs, MILESTONES[sub.end])
            band_join = state["lapland_join"]
            if band_join is not None:
                # Pick up summer trail at the previous Band subseg's endpoint
                # (gives a clean seam, e.g. Kalle's Klimpfjäll → Lapplandsleden).
                ik = lapland_join_idx_on_summer(summer_locs, band_join)
            else:
                ik = nearest_idx(summer_locs, MILESTONES[sub.start])
            if ik >= ih:
                raise ValueError(
                    f"Lapplandsleden start ({sub.start}) not south of {sub.end}"
                )
            seg = [dict(p) for p in summer_locs[ik : ih + 1]]
            state["lapland_end"] = seg[-1]
            state["lapland_join"] = None  # consumed
            write_track_gpx(
                OUT_DIR / "lapland-klimpf-hemavan.gpx",
                seg,
                f"Lapplandsleden {sub.start.title()} → {sub.end.title()}",
                f"lapland-trail-summer.gpx slice from {sub.start} pickup to {sub.end} (S→N).",
            )
        else:
            locs = load_track(path)
            if sub.end == "LAPLAND_JOIN":
                summer_locs = state["summer_locs"]
                if summer_locs is None:
                    summer_locs = ensure_lapland_s_to_n(SRC_DIR / "lapland-trail-summer.gpx")
                    state["summer_locs"] = summer_locs
                i0 = nearest_idx(locs, MILESTONES[sub.start])
                i1 = lapland_join_idx_on_band(locs, i0, summer_locs)
                seg = [dict(p) for p in locs[i0 : i1 + 1]] if i0 <= i1 else \
                      [dict(p) for p in locs[i1 : i0 + 1][::-1]]
                seg = thin_points(seg, 300.0)
                state["lapland_join"] = seg[-1] if seg else None
            elif sub.start == "HEMAVAN" and state.get("lapland_end") is not None:
                lend = state["lapland_end"]
                i0 = nearest_idx(locs, (lend["lat"], lend["lng"]))
                i1 = nearest_idx(locs, MILESTONES[sub.end])
                seg = [dict(p) for p in locs[i0 : i1 + 1]] if i0 <= i1 else \
                      extract_band_segment(locs, sub.start, sub.end)
                seg = thin_points(seg, 300.0)
                state["lapland_end"] = None  # consumed
            else:
                seg = extract_band_segment(locs, sub.start, sub.end)
                # Band JSON tracks: thin to 300 m (except Paolo who's already
                # sparse). GPX sources are pre-curated — keep full density.
                if sub.source.lower().endswith(".json") and "paolo-peralta" not in sub.source:
                    seg = thin_points(seg, 300.0)
                # If the next subseg is the Lapplandsleden summer GPX, hand off
                # this subseg's endpoint as the pickup point (clean seam).
                if next_is_lapland and seg:
                    state["lapland_join"] = seg[-1]

        out.append((sub.label, seg))
    return out


# ----------------------------------------------------------------------------
# waypoints
# ----------------------------------------------------------------------------

WPT_LABELS = {
    "GROVEL":   "Grövelsjön",
    "HAVLINGEN": "Hävlingestugorna",
    "ROGEN":    "STF Rogen fjällstuga",
    "DALSTENHAN": "Dalstenshån (north shore)",
    "HAMRA":      "Hamra Livs (Tänndalen)",
    "SKARVRUET":  "STF Skarvruet vandrarhem",
    "HELAGS":   "Helags fjällstation",
    "SYLARNA":  "Sylarna fjällstation",
    "BLAHAMM":  "Blåhammaren fjällstation",
    "STORLIEN": "Storlien",
    "NORDER_RENSJON": "Norder-Rensjön (track leaves lake)",
    "KOLASEN":  "Kolåsens Fjällhotell",
    "OLDEN":    "Olden (corridor)",
    "VALSJO":   "Valsjöbua Lanthandel",
    "BLASJOFJALL": "ICA Nära Blåsjöfjäll (detour)",
    "GADDEDE":  "Gäddede",
    "KLIMPF":   "Klimpfjäll",
    "HEMAVAN":  "Hemavan",
    "JACKVIK":  "Jäckvik",
    "KVIKK":    "Kvikkjokk",
    "RITSEM":   "Ritsem (STF)",
    "SALKA":    "Sälka fjällstation",
    "ABISKO":   "Abisko",
    "TRERIK":   "Treriksröset",
    "PALTSA":   "Pältsa",
    "BORGAFJALL": "Borgafjäll Hotell",
    "SAXNAS":   "Saxnäs / Marsfjäll",
    "AMMARNAS": "Ammarnäs (Fritidscenter / STF)",
    "ADOLFSTROM": "Adolfström Camping",
    "VUOGGATJALME": "Vuoggatjålme Fjällhotell",
    "SALTOLUOKTA": "STF Saltoluokta",
    "NIKKALUOKTA": "Nikkaluokta Sarri",
    "LAPPJORD": "Lappjordhytta (DNT)",
    "ALTEVASS": "Altevasshytta (DNT)",
    "BJORKLIDEN": "Björkliden Camping",
}


def camp_waypoints_for_section(section: Section, section_track: list[dict]) -> list[dict]:
    wpts: list[dict] = []
    for day, date, cum_km, place, acc, note, pin_milestone in section.camps:
        if pin_milestone and pin_milestone in MILESTONES:
            lat, lon = MILESTONES[pin_milestone]
        else:
            rel_km = cum_km - section.start_cum_km
            p = point_at_planned_km(section_track, rel_km)
            lat, lon = p["lat"], p["lng"]
        desc = f"Section {section.id} · {date} · cum {cum_km} km · {acc}"
        if note:
            desc += f" · {note}"
        if acc == "T":
            sym, wpt_type = "Campground", "camp"
        elif acc == "GOAL":
            sym, wpt_type = "Flag, Red", "goal"
        elif acc == "H":
            sym, wpt_type = "Lodging", "hut"
        else:
            sym, wpt_type = "City", "resupply"
        wpts.append(
            {
                "name": f"D{day} · {place}",
                "lat": lat, "lon": lon,
                "desc": desc, "sym": sym,
                "type": wpt_type,
            }
        )
    return wpts


# ----------------------------------------------------------------------------
# GPX writing
# ----------------------------------------------------------------------------

def add_waypoint(
    gpx: Element, name: str, lat: float, lon: float,
    *, desc: str = "", sym: str | None = None, wpt_type: str | None = None,
) -> None:
    w = SubElement(gpx, "wpt", attrib={"lat": f"{lat:.6f}", "lon": f"{lon:.6f}"})
    SubElement(w, "name").text = name
    if desc:
        SubElement(w, "desc").text = desc
    if sym:
        SubElement(w, "sym").text = sym
    if wpt_type:
        SubElement(w, "type").text = wpt_type


def write_track_gpx(path: Path, locs: list[dict], name: str, desc: str = "") -> None:
    """Plain single-trkseg GPX (used for the Lapland debug dump)."""
    gpx = Element("gpx", attrib={"version": "1.1", "creator": "VitaBandet", "xmlns": GPX_NS})
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = name
    if desc:
        SubElement(meta, "desc").text = desc
    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = name
    seg = SubElement(trk, "trkseg")
    for p in locs:
        SubElement(seg, "trkpt", attrib={
            "lat": f"{p['lat']:.6f}", "lon": f"{p['lng']:.6f}",
        })
    rough = ET.tostring(gpx, encoding="unicode")
    parsed = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?>\n' + rough)
    path.write_text(parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8"), encoding="utf-8")


def _emit_trkpt(parent: Element, p: dict) -> None:
    att = {
        "lat": f"{p['lat']:.8f}".rstrip("0").rstrip("."),
        "lon": f"{p['lng']:.8f}".rstrip("0").rstrip("."),
    }
    trkpt = SubElement(parent, "trkpt", attrib=att)
    if p.get("_iso"):
        SubElement(trkpt, "time").text = p["_iso"]


def write_section_gpx(
    section: Section,
    subsegs: list[tuple[str, list[dict]]],
    flat_track: list[dict],
) -> Path:
    gpx = Element("gpx", attrib={
        "version": "1.1", "creator": "VitaBandet section", "xmlns": GPX_NS,
    })
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = f"Section {section.id} — {section.title}"
    sources = ", ".join(sub.source for sub in section.subsegments)
    SubElement(meta, "desc").text = (
        f"Section {section.id} of Vita Bandet 2028 — {section.title}. "
        f"Sources: {sources}."
    )
    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = f"Section {section.id}"
    # One trkseg per source within this section (so the join is visible).
    for label, points in subsegs:
        if not points:
            continue
        seg = SubElement(trk, "trkseg")
        SubElement(seg, "name").text = label
        for p in points:
            _emit_trkpt(seg, p)

    for camp in camp_waypoints_for_section(section, flat_track):
        add_waypoint(gpx, camp["name"], camp["lat"], camp["lon"],
                     desc=camp["desc"], sym=camp["sym"], wpt_type=camp["type"])
    for key in section.waypoints:
        lat, lon = MILESTONES[key]
        add_waypoint(gpx, WPT_LABELS[key], lat, lon)

    out = OUT_DIR / section.filename
    rough = ET.tostring(gpx, encoding="unicode")
    parsed = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?>\n' + rough)
    out.write_text(parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8"), encoding="utf-8")
    return out


def write_composite_gpx(
    section_tracks: list[tuple[Section, list[dict]]],
    name: str = "Vita Bandet 2028 (composite)",
) -> Path:
    gpx = Element("gpx", attrib={
        "version": "1.1", "creator": "VitaBandet composite", "xmlns": GPX_NS,
    })
    meta = SubElement(gpx, "metadata")
    SubElement(meta, "name").text = name
    SubElement(meta, "desc").text = (
        "Composite route for Vita Bandet 2028 — six trksegs, one per Section. "
        "Sources: Lotta & Björn (S1 Grövelsjön→Storlien + S2 Storlien→Gäddede), "
        "Kalle (S3 Gäddede→Klimpfjäll) + lapland-trail-summer.gpx (S3 Klimpfjäll→Hemavan), "
        "Mårten (S4 Hemavan→Kvikkjokk), "
        "2028-plan-kvikkjokk-abisko.gpx (S5 + S5b — Padjelanta-west via Ritsem and KL via Sälka), "
        "2028-plan-abisko-paltsa.gpx (S6 — Nordkalottleden Abisko→Pältsa)."
    )
    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = name

    # One trkseg per Section (subsegments concatenated).
    for section, track in section_tracks:
        if not track:
            continue
        seg = SubElement(trk, "trkseg")
        SubElement(seg, "name").text = f"Section {section.id} — {section.title}"
        for p in track:
            _emit_trkpt(seg, p)

    # Camp waypoints (all sections that define them).
    for section, track in section_tracks:
        for camp in camp_waypoints_for_section(section, track):
            add_waypoint(gpx, camp["name"], camp["lat"], camp["lon"],
                         desc=camp["desc"], sym=camp["sym"], wpt_type=camp["type"])

    # Milestone waypoints (union across all sections, de-duplicated).
    seen: set[str] = set()
    for section, _ in section_tracks:
        for key in section.waypoints:
            if key in seen:
                continue
            seen.add(key)
            lat, lon = MILESTONES[key]
            add_waypoint(gpx, WPT_LABELS[key], lat, lon)

    out = OUT_DIR / "vita-bandet-2028-composite.gpx"
    rough = ET.tostring(gpx, encoding="unicode")
    parsed = minidom.parseString('<?xml version="1.0" encoding="UTF-8"?>\n' + rough)
    out.write_text(parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8"), encoding="utf-8")
    return out


# ----------------------------------------------------------------------------
# timestamps
# ----------------------------------------------------------------------------

def assign_plan_times(points: list[dict], start: datetime, end: datetime) -> None:
    if len(points) < 2:
        if points:
            points[0]["_iso"] = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        return
    cum = [0.0]
    for i in range(1, len(points)):
        cum.append(cum[-1] + haversine_m(
            points[i - 1]["lat"], points[i - 1]["lng"],
            points[i]["lat"], points[i]["lng"],
        ))
    total = cum[-1] or 1.0
    span = (end - start).total_seconds()
    for i, p in enumerate(points):
        t = start + timedelta(seconds=span * cum[i] / total)
        p["_iso"] = t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    state = {"summer_locs": None, "lapland_join": None, "lapland_end": None}

    per_section_subsegs: list[tuple[Section, list[tuple[str, list[dict]]]]] = []
    section_flat: list[tuple[Section, list[dict]]] = []

    for section in SECTIONS:
        subsegs = build_section_track(section, state)
        flat = [p for _, pts in subsegs for p in pts]
        per_section_subsegs.append((section, subsegs))
        section_flat.append((section, flat))

    # Assign plan-time stamps across the full route (linear interp by distance).
    all_points = [p for _, flat in section_flat for p in flat]
    assign_plan_times(all_points, datetime(2028, 2, 15, 10, 0), datetime(2028, 4, 19, 12, 0))

    # Per-section GPX files.
    section_paths: list[Path] = []
    for (section, subsegs), (_, flat) in zip(per_section_subsegs, section_flat):
        section_paths.append(write_section_gpx(section, subsegs, flat))

    # Composite GPX.
    composite_path = write_composite_gpx(section_flat)

    # Report.
    total_pts = sum(len(flat) for _, flat in section_flat)
    total_km = 0.0
    for _, flat in section_flat:
        total_km += sum(
            haversine_m(flat[i - 1]["lat"], flat[i - 1]["lng"], flat[i]["lat"], flat[i]["lng"])
            for i in range(1, len(flat))
        )
    total_km /= 1000

    print(f"Wrote composite: {composite_path.relative_to(ROOT)}  "
          f"({total_pts} pts, {total_km:.0f} km, {len(section_flat)} sections)")
    for p in section_paths:
        print(f"  · {p.relative_to(ROOT)}")
    print()
    print("Section breakdown:")
    for section, flat in section_flat:
        km = sum(
            haversine_m(flat[i - 1]["lat"], flat[i - 1]["lng"], flat[i]["lat"], flat[i]["lng"])
            for i in range(1, len(flat))
        ) / 1000 if len(flat) > 1 else 0
        gaps = [
            haversine_m(flat[i - 1]["lat"], flat[i - 1]["lng"], flat[i]["lat"], flat[i]["lng"])
            for i in range(1, len(flat))
        ]
        max_gap = max(gaps) / 1000 if gaps else 0
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        print(f"  S{section.id} {section.title:30s}  {len(flat):5d} pts  "
              f"{km:6.1f} km  avgGap={avg_gap:4.0f}m  maxGap={max_gap:5.2f}km")


if __name__ == "__main__":
    main()
