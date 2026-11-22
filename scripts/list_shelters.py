#!/usr/bin/env python3
"""Shelters within 3 km of the 2027 plan track and the picked alternatives.

OpenStreetMap via Overpass (tourism=wilderness_hut, tourism=alpine_hut,
amenity=shelter). Bus shelters are dropped. Distance is to the nearest
track sample. Writes JSON for the plan list.
"""

from __future__ import annotations

import json
import math
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plan" / "shelters-along-track-2027.json"
RADIUS_KM = 3.0
SAMPLE_M = 200

TRACKS = [
    ("plan", ROOT / "tracks" / "generated" / "vita-bandet-2027-composite.gpx"),
    ("undersaker", ROOT / "tracks" / "alternatives" / "picked" / "helags-olden__undersaker__christian-kammer-2023.gpx"),
    ("hemavan-village", ROOT / "tracks" / "alternatives" / "picked" / "klimpf-hemavan__village__christian-kammer-2023.gpx"),
    ("kungsleden", ROOT / "tracks" / "alternatives" / "picked" / "kvikkjokk-salka__kungsleden__christian-kammer-2023.gpx"),
    ("finish-traditional", ROOT / "tracks" / "alternatives" / "picked" / "abisko-finish__traditional__christian-kammer-2023.gpx"),
]

NS = {"g": "http://www.topografix.com/GPX/1/1"}
OVERPASS = "https://overpass-api.de/api/interpreter"


def hav(a, b) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def load_track(path: Path) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for _ev, el in ET.iterparse(path, events=("end",)):
        if el.tag != f"{{{NS['g']}}}trkpt":
            continue
        lat, lon = el.get("lat"), el.get("lon")
        if lat and lon:
            pts.append((float(lat), float(lon)))
        el.clear()
    return pts


def resample(pts: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
    """(lat, lon, km from start), about every SAMPLE_M."""
    if not pts:
        return []
    out = [(pts[0][0], pts[0][1], 0.0)]
    acc = 0.0
    since = 0.0
    prev = pts[0]
    for p in pts[1:]:
        d = hav(prev, p)
        acc += d
        since += d
        if since >= SAMPLE_M / 1000:
            out.append((p[0], p[1], acc))
            since = 0.0
        prev = p
    if out[-1][:2] != pts[-1]:
        out.append((pts[-1][0], pts[-1][1], acc))
    return out


CACHE = Path("/tmp/vitabandet-shelter-cache")


def windows(samples: list[tuple[float, float, float]], span_km: float = 40.0):
    if not samples:
        return
    lat0, lon0, km0 = samples[0]
    box = [lat0, lon0, lat0, lon0]
    for lat, lon, km in samples[1:]:
        if km - km0 >= span_km:
            yield pad(box)
            box = [lat, lon, lat, lon]
            km0 = km
        else:
            box[0] = min(box[0], lat)
            box[1] = min(box[1], lon)
            box[2] = max(box[2], lat)
            box[3] = max(box[3], lon)
    yield pad(box)


def pad(box):
    s, w, n, e = box
    mid = (s + n) / 2
    lat_pad = 3.6 / 111.0
    lon_pad = 3.6 / (111.0 * max(0.25, math.cos(math.radians(mid))))
    return (round(s - lat_pad, 3), round(w - lon_pad, 3), round(n + lat_pad, 3), round(e + lon_pad, 3))


def overpass_bbox(bbox) -> list[dict]:
    s, w, n, e = bbox
    CACHE.mkdir(exist_ok=True)
    cache = CACHE / f"{s}_{w}_{n}_{e}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    q = f"""
[out:json][timeout:60];
(
  nwr["tourism"="wilderness_hut"]({s},{w},{n},{e});
  nwr["tourism"="alpine_hut"]({s},{w},{n},{e});
  nwr["amenity"="shelter"]({s},{w},{n},{e});
);
out center tags;
"""
    last = "no attempt"
    for attempt in range(5):
        proc = subprocess.run(
            [
                "curl", "-sS", "-m", "80",
                "-A", "VitaBandet-shelter-list/1.0 (personal trip plan)",
                "-w", "\n%{http_code}",
                "--data-urlencode", f"data={q}",
                OVERPASS,
            ],
            check=False, capture_output=True, text=True,
        )
        raw = proc.stdout or ""
        if "\n" not in raw:
            last = proc.stderr[:160] or "empty"
        else:
            payload, code = raw.rsplit("\n", 1)
            code = code.strip()
            if code == "200":
                body = json.loads(payload)
                els = body.get("elements", [])
                cache.write_text(json.dumps(els))
                return els
            last = f"HTTP {code} {payload[:120].replace(chr(10), ' ')}"
        wait = 8 * (attempt + 1)
        print(f"    retry {attempt + 1}: {last} (sleep {wait}s)")
        time.sleep(wait)
    raise SystemExit(f"overpass failed for {bbox}: {last}")


def point_of(el: dict):
    if el["type"] == "node":
        return el.get("lat"), el.get("lon")
    c = el.get("center") or {}
    return c.get("lat"), c.get("lon")


def nearest(lat, lon, samples):
    best = None
    for s in samples:
        d = hav((lat, lon), (s[0], s[1]))
        if best is None or d < best[0]:
            best = (d, s[2])
    return best


def keep(tags: dict) -> bool:
    st = (tags.get("shelter_type") or "").lower()
    if st in {"public_transport", "bus_stop", "gazebo"}:
        return False
    if tags.get("highway") in {"bus_stop"} or tags.get("public_transport") == "platform":
        return False
    if tags.get("amenity") == "shelter" and tags.get("shelter_type") in {None, ""} and tags.get("tourism") not in {
        "wilderness_hut",
        "alpine_hut",
    }:
        # bare shelter with no name is usually a bus stop or a picnic roof
        if not tags.get("name") and not tags.get("name:sv") and not tags.get("name:no"):
            return False
    return True


def main() -> None:
    corridors = {}
    for key, path in TRACKS:
        raw = load_track(path)
        samples = resample(raw)
        print(f"{key}: {len(raw)} pts → {len(samples)} samples, {samples[-1][2]:.0f} km" if samples else f"{key}: empty")
        corridors[key] = samples

    seen: dict[str, dict] = {}
    for key, samples in corridors.items():
        boxes = list(windows(samples))
        print(f"{key}: {len(boxes)} boxes")
        for i, bbox in enumerate(boxes, 1):
            els = overpass_bbox(bbox)
            print(f"  {key} {i}/{len(boxes)} → {len(els)}", flush=True)
            for el in els:
                tags = el.get("tags") or {}
                if not keep(tags):
                    continue
                lat, lon = point_of(el)
                if lat is None:
                    continue
                hit = nearest(lat, lon, samples)
                if hit is None or hit[0] > RADIUS_KM:
                    continue
                oid = f"{el['type']}/{el['id']}"
                row = seen.get(oid)
                if row is None:
                    row = {
                        "id": oid,
                        "lat": round(lat, 5),
                        "lon": round(lon, 5),
                        "name": tags.get("name") or tags.get("name:sv") or tags.get("name:no") or "",
                        "tags": {
                            k: tags.get(k)
                            for k in (
                                "tourism",
                                "amenity",
                                "shelter_type",
                                "building",
                                "access",
                                "locked",
                                "fee",
                                "reservation",
                                "capacity",
                                "beds",
                                "operator",
                                "brand",
                                "opening_hours",
                                "website",
                                "phone",
                                "ele",
                                "description",
                                "ref",
                            )
                            if tags.get(k)
                        },
                        "near": {},
                    }
                    seen[oid] = row
                row["near"][key] = {"km_off": round(hit[0], 2), "along_km": round(hit[1], 1)}
            time.sleep(1)

    rows = sorted(
        seen.values(),
        key=lambda r: (
            0 if "plan" in r["near"] else 1,
            r["near"].get("plan", {}).get("along_km", 10_000),
            min(v["km_off"] for v in r["near"].values()),
        ),
    )
    OUT.write_text(json.dumps({"radius_km": RADIUS_KM, "count": len(rows), "shelters": rows}, ensure_ascii=False, indent=2))
    print(f"wrote {len(rows)} → {OUT}")


if __name__ == "__main__":
    main()
