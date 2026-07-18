#!/usr/bin/env python3
"""Scrape completed Vita / Gröna Bandet tracks from vgb.vitagronabandet.se.

Flow:
  1. Resolve Ribbon Archive URL (completed-ribbons page → ribbonArchiveStatic.php?v=…)
  2. Parse archive rows (tour id is on <tr data-id>)
  3. POST ajax/getRouteData.php with id=<tourID>
  4. Write tracks/source/<slug>-track.json and convert to GPX via json_to_gpx.py

Examples:
  python3 scripts/scrape_vgb_tracks.py --list
  python3 scripts/scrape_vgb_tracks.py --white --completed --limit 5
  python3 scripts/scrape_vgb_tracks.py --tour-id 2384
  python3 scripts/scrape_vgb_tracks.py --hiker-id 6924585236186
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "tracks" / "source"
JSON_TO_GPX = ROOT / "scripts" / "json_to_gpx.py"

BASE = "https://vgb.vitagronabandet.se"
COMPLETED_PAGE = "https://www.vitagronabandet.se/en/all-ribbons/completed-ribbons/"
# Stable token from vitagronabandet.se “completed ribbons” body link (LIST VIEW).
DEFAULT_ARCHIVE_V = "YVJXUjR0R0p5VjF4Z1p3Y0ZkU2lNUT09OmF4S3pZQjVnR0p0"
USER_AGENT = "VitaBandet-track-scraper/1.0 (+local planning; respectful delay)"


@dataclass
class ArchiveRow:
    tour_id: int
    hiker_id: str
    name: str
    nationality: str
    mode: str
    season: str  # White / Green
    ribbon_type: str  # Original / Sections
    start_point: str
    start_date: str
    finish_date: str
    total_km: str
    days: str
    classes: list[str]

    @property
    def completed(self) -> bool:
        return "approved" in self.classes and bool(
            re.match(r"\d{4}-\d{2}-\d{2}", self.finish_date or "")
        )

    @property
    def is_white(self) -> bool:
        return "white" in self.classes or self.season.lower() == "white"


def fetch(url: str, data: bytes | None = None, headers: dict | None = None) -> bytes:
    hdrs = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def archive_url_for_v(v: str, lang: str = "en") -> str:
    return f"{BASE}/ribbonArchiveStatic.php?v={urllib.parse.quote(v, safe='')}&lang={lang}"


def discover_archive_url(lang: str = "en") -> str:
    """Prefer the completed-ribbons body link; fall back to DEFAULT_ARCHIVE_V."""
    try:
        html = fetch(COMPLETED_PAGE).decode("utf-8", errors="ignore")
    except Exception:
        return archive_url_for_v(DEFAULT_ARCHIVE_V, lang)

    # Body copy on completed-ribbons mentions finishers — take first archive href after that.
    anchor = html.lower().find("finishers through the years")
    search = html[anchor:] if anchor >= 0 else html
    matches = re.findall(
        r'https://vgb\.vitagronabandet\.se/ribbonArchiveStatic\.php\?v=([^"\'&\s]+)',
        search,
    )
    if matches:
        v = matches[0].replace("&#038;", "&")
        # strip any trailing HTML entities leftovers
        v = v.split("&")[0]
        return archive_url_for_v(v, lang)
    return archive_url_for_v(DEFAULT_ARCHIVE_V, lang)


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_archive(html: str) -> list[ArchiveRow]:
    row_re = re.compile(
        r'<tr class="([^"]*)"[^>]*data-id="(\d+)"[^>]*>(.*?)</tr>',
        re.S | re.I,
    )
    rows: list[ArchiveRow] = []
    for cls, data_id, body in row_re.findall(html):
        classes = cls.split()
        tds = re.findall(r"<td[^>]*>(.*?)</td>", body, re.S | re.I)
        texts = [strip_tags(td) for td in tds]
        hiker = re.search(r"hiker\.php\?id=([a-z0-9]+)", body, re.I)
        if not hiker or len(texts) < 9:
            continue
        rows.append(
            ArchiveRow(
                tour_id=int(data_id),
                hiker_id=hiker.group(1),
                name=texts[0],
                nationality=texts[1] if len(texts) > 1 else "",
                mode=texts[2] if len(texts) > 2 else "",
                season=texts[4] if len(texts) > 4 else "",
                ribbon_type=texts[5] if len(texts) > 5 else "",
                start_point=texts[6] if len(texts) > 6 else "",
                start_date=texts[7] if len(texts) > 7 else "",
                finish_date=texts[8] if len(texts) > 8 else "",
                total_km=texts[9] if len(texts) > 9 else "",
                days=texts[10] if len(texts) > 10 else "",
                classes=classes,
            )
        )
    return rows


def slugify(name: str) -> str:
    # Normalize accents → ASCII, then kebab-case
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_name = ascii_name.lower()
    ascii_name = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
    return ascii_name or "track"


def track_slug(route_name: str, hiker_name: str) -> str:
    """Prefer API route name (e.g. 'Eriks Band') → eriks-band."""
    base = route_name.strip() if route_name.strip() else hiker_name
    slug = slugify(base)
    if not slug.endswith("-band") and "band" not in slug:
        # keep as-is (e.g. olas-vita-band-2 comes from route name)
        pass
    return slug


def get_route_data(tour_id: int) -> dict:
    body = urllib.parse.urlencode({"id": tour_id}).encode()
    raw = fetch(
        f"{BASE}/ajax/getRouteData.php",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": BASE,
            "Referer": f"{BASE}/",
        },
    )
    data = json.loads(raw.decode("utf-8"))
    if not data.get("status"):
        raise RuntimeError(f"getRouteData id={tour_id}: {data}")
    return data


def parse_hiker_page(hiker_id: str) -> tuple[int, dict]:
    html = fetch(f"{BASE}/hiker.php?id={hiker_id}&lang=en").decode("utf-8", errors="ignore")
    m = re.search(r"var\s+tourID\s*=\s*(\d+)\s*;", html)
    if not m:
        raise RuntimeError(f"No tourID on hiker.php?id={hiker_id}")
    tour_id = int(m.group(1))
    td = {}
    tm = re.search(r"var\s+tourData\s*=\s*(\{.*?\});\s*\n", html, re.S)
    if tm:
        td = json.loads(tm.group(1))
    return tour_id, td


def write_track(data: dict, out_dir: Path, slug: str, convert: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{slug}-track.json"
    gpx_path = out_dir / f"{slug}.gpx"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n = len(data.get("locations") or [])
    print(f"  wrote {json_path.name} ({n} pts)")
    if convert and n:
        subprocess.run(
            [sys.executable, str(JSON_TO_GPX), str(json_path), str(gpx_path)],
            check=True,
        )
    return json_path


def existing_tour_ids(out_dir: Path) -> dict[int, Path]:
    """Map tour_id → JSON path for already-scraped tracks under out_dir (recursive)."""
    found: dict[int, Path] = {}
    if not out_dir.exists():
        return found
    for path in out_dir.rglob("*-track.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        tid = (data.get("_scrape") or {}).get("tour_id")
        if tid is None:
            continue
        try:
            found[int(tid)] = path
        except (TypeError, ValueError):
            continue
    return found


def filter_rows(
    rows: list[ArchiveRow],
    *,
    white: bool,
    green: bool,
    completed: bool,
    year: int | None,
    year_from: int | None,
    year_to: int | None,
    tour_ids: set[int] | None,
    hiker_ids: set[str] | None,
) -> list[ArchiveRow]:
    out = []
    for r in rows:
        if tour_ids is not None and r.tour_id not in tour_ids:
            continue
        if hiker_ids is not None and r.hiker_id not in hiker_ids:
            continue
        if completed and not r.completed:
            continue
        start_year = None
        if r.start_date and len(r.start_date) >= 4 and r.start_date[:4].isdigit():
            start_year = int(r.start_date[:4])
        if year is not None:
            if start_year != year:
                continue
        if year_from is not None and (start_year is None or start_year < year_from):
            continue
        if year_to is not None and (start_year is None or start_year > year_to):
            continue
        is_green = "green" in r.classes or r.season.lower() == "green"
        if white or green:
            ok = (white and r.is_white) or (green and is_green)
            if not ok:
                continue
        out.append(r)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--archive-url", help="Full ribbonArchiveStatic.php?v=…&lang=en URL")
    p.add_argument("--list", action="store_true", help="List matching archive rows and exit")
    p.add_argument("--white", action="store_true", help="White Ribbon only")
    p.add_argument("--green", action="store_true", help="Green Ribbon only")
    p.add_argument("--completed", action="store_true", help="Completed only (class approved + finish date)")
    p.add_argument("--year", type=int, help="Filter by start-date year (e.g. 2026)")
    p.add_argument("--year-from", type=int, help="Inclusive start-date year lower bound")
    p.add_argument("--year-to", type=int, help="Inclusive start-date year upper bound")
    p.add_argument("--min-points", type=int, default=0, help="Skip routes with fewer GPS points")
    p.add_argument("--out-by-year", action="store_true", help="Write under OUT_DIR/<start-year>/")
    p.add_argument("--tour-id", type=int, action="append", default=[], help="Numeric tour/Ribbon ID (repeatable)")
    p.add_argument("--hiker-id", action="append", default=[], help="hiker.php hash id (repeatable)")
    p.add_argument("--limit", type=int, default=0, help="Max tracks to download (0 = all)")
    p.add_argument("--delay", type=float, default=1.0, help="Seconds between route downloads")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--no-gpx", action="store_true", help="Skip json_to_gpx conversion")
    p.add_argument("--force", action="store_true", help="Overwrite existing JSON")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    # Default filter when listing/scraping without explicit ids: completed white
    if not args.tour_id and not args.hiker_id and not args.white and not args.green:
        args.white = True
        args.completed = True

    archive_url = args.archive_url or discover_archive_url()
    print(f"Archive: {archive_url}")
    html = fetch(archive_url).decode("utf-8", errors="ignore")
    if "hiker.php?id=" not in html:
        raise SystemExit("Archive HTML has no hiker links — check --archive-url / v= token")

    rows = parse_archive(html)
    print(f"Parsed {len(rows)} archive rows")

    tour_ids = set(args.tour_id) if args.tour_id else None
    hiker_ids = set(args.hiker_id) if args.hiker_id else None

    # Resolve hiker-only requests via hiker page if not in archive filter yet
    if hiker_ids and tour_ids is None:
        for hid in list(hiker_ids):
            try:
                tid, _ = parse_hiker_page(hid)
                print(f"  hiker {hid} → tourID {tid}")
                tour_ids = (tour_ids or set()) | {tid}
            except Exception as e:
                print(f"  warn: {hid}: {e}", file=sys.stderr)

    matched = filter_rows(
        rows,
        white=args.white,
        green=args.green,
        completed=args.completed,
        year=args.year,
        year_from=args.year_from,
        year_to=args.year_to,
        tour_ids=tour_ids,
        hiker_ids=hiker_ids if not args.tour_id else None,
    )

    # If --tour-id given but not in archive (edge case), still download
    if args.tour_id:
        known = {r.tour_id for r in matched}
        for tid in args.tour_id:
            if tid not in known:
                matched.append(
                    ArchiveRow(
                        tour_id=tid,
                        hiker_id="",
                        name=f"tour-{tid}",
                        nationality="",
                        mode="",
                        season="",
                        ribbon_type="",
                        start_point="",
                        start_date="",
                        finish_date="",
                        total_km="",
                        days="",
                        classes=["approved", "white"],
                    )
                )

    matched.sort(key=lambda r: (r.start_date or "", r.name))
    if args.limit:
        matched = matched[: args.limit]

    if args.list:
        for r in matched:
            print(
                f"{r.tour_id:>5}  {r.hiker_id:13}  {r.season:5}  {r.start_date} → {r.finish_date or '—':10}  "
                f"{r.total_km:>5} km  {r.name}"
            )
        print(f"{len(matched)} rows")
        return

    if args.dry_run:
        print(f"Would download {len(matched)} tracks to {args.out_dir}"
              + ("/<year>/" if args.out_by_year else ""))
        for r in matched[:20]:
            print(f"  {r.tour_id} {r.start_date[:4] if r.start_date else '?'} {r.name}")
        if len(matched) > 20:
            print(f"  … +{len(matched) - 20} more")
        return

    used_slugs: set[str] = set()
    already = existing_tour_ids(args.out_dir)
    saved: list[ArchiveRow] = []
    saved_by_year: dict[str, list[ArchiveRow]] = {}
    kept = 0
    skipped_sparse = 0
    skipped_empty = 0
    skipped_existing = 0

    for i, r in enumerate(matched):
        year = (r.start_date or "unknown")[:4]
        out_dir = args.out_dir / year if args.out_by_year else args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"[{i + 1}/{len(matched)}] tour {r.tour_id} — {r.name} ({year})")
        if r.tour_id in already and not args.force:
            print(f"  exists {already[r.tour_id].name} — skip (use --force)")
            skipped_existing += 1
            continue
        try:
            data = get_route_data(r.tour_id)
        except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue
        locs = data.get("locations") or []
        if not locs:
            print("  skip: empty locations")
            skipped_empty += 1
            if i + 1 < len(matched) and args.delay > 0:
                time.sleep(args.delay)
            continue
        n = len(locs)
        if args.min_points and n < args.min_points:
            print(f"  skip: {n} pts < --min-points {args.min_points}")
            skipped_sparse += 1
            if i + 1 < len(matched) and args.delay > 0:
                time.sleep(args.delay)
            continue
        slug = track_slug(data.get("name") or "", r.name)
        slug_key = f"{year}/{slug}" if args.out_by_year else slug
        json_path = out_dir / f"{slug}-track.json"
        # Rename only on true slug collision with a *different* tour.
        if slug_key in used_slugs or (json_path.exists() and not args.force):
            slug = f"{slug}-{r.tour_id}"
            slug_key = f"{year}/{slug}" if args.out_by_year else slug
            json_path = out_dir / f"{slug}-track.json"
        if json_path.exists() and not args.force:
            print(f"  exists {json_path.name} — skip (use --force)")
            skipped_existing += 1
        else:
            out = dict(data)
            out["_scrape"] = {
                "tour_id": r.tour_id,
                "hiker_id": r.hiker_id,
                "archive_name": r.name,
                "start_date": r.start_date,
                "finish_date": r.finish_date,
                "season": r.season,
            }
            write_track(out, out_dir, slug, convert=not args.no_gpx)
            used_slugs.add(slug_key)
            already[r.tour_id] = json_path
            kept += 1
            saved.append(r)
            saved_by_year.setdefault(year, []).append(r)
        if i + 1 < len(matched) and args.delay > 0:
            time.sleep(args.delay)

    # Index only successfully saved tracks (not skipped / failed / sparse).
    if args.out_by_year:
        for year, year_rows in saved_by_year.items():
            index_path = args.out_dir / year / "vgb-scrape-index.json"
            index_path.write_text(
                json.dumps([asdict(r) for r in year_rows], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Index: {index_path}")
    else:
        index_path = args.out_dir / "vgb-scrape-index.json"
        index_path.write_text(
            json.dumps([asdict(r) for r in saved], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Index: {index_path}")

    print(
        f"Done: kept {kept} · existing {skipped_existing} · empty {skipped_empty} · "
        f"sparse {skipped_sparse} · listed {len(matched)}"
    )


if __name__ == "__main__":
    main()
