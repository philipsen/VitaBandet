# Vita Bandet — historical track comparison

Nine completed Band tracks downloaded from [vgb.vitagronabandet.se](https://vgb.vitagronabandet.se) via `ajax/getRouteData.php` and converted to GPX. Factual comparison against the [2027 plan](./dag-for-dag-2027.md) (target **~900 km at Kvikkjokk by ~29 Mar**, start **15 Feb**) — describes range, not pacing prescription.

**2027 plan composite GPX:** [`vita-bandet-2027-composite.gpx`](../tracks/generated/vita-bandet-2027-composite.gpx) — 6 trksegs (one per Section).

| Section | Source(s) | Why |
|---------|-----------|-----|
| 1 Grövelsjön → Storlien | **Lotta & Björn** | Single dense track end-to-end: Grövelsjön +0.33 km, Helags +0.04 km, **Blåhammaren +0.18 km**, **Storlien village +0.44 km** — only track that hits every Section 1 milestone within ≤ 0.44 km |
| 2 Storlien → Gäddede | **Lotta & Björn** | Same source as S1 → clean **0.00 km seam** at Storlien (single continuous track for Sections 1 + 2) |
| 3 Gäddede → Hemavan | **Kalle** (G→Klimpfjäll) + `lapland-trail-summer.gpx` (Klimpfjäll→Hemavan) | Kalle has 139 dense pts (max gap 1.4 km) G→Klimpfjäll vs Ola's 17 pts (max 13.8 km); marked Lapplandsleden continues to Hemavan |
| 4 Hemavan → Kvikkjokk | Mårten | Dense, väster om Jäckvik |
| 5 Kvikkjokk → Abisko | **`2027-plan-kvikkjokk-abisko.gpx`** (own Garmin plan) | 6 902-pt dense planned route on Padjelanta-west / Ritsem then KL via Sälka. Two internal subsegs (§5 K→Sälka, §5b Sälka→Abisko) — 0 km seam at Sälka |
| 6 Abisko → Pältsa | **`2027-plan-abisko-paltsa.gpx`** (own Garmin plan, from `2027 nord.GPX`) | 12 123 pts · ~168 km · max gap ~7.7 km near Abisko start |

**Reference point:** Kvikkjokk ≈ `66.9513°N, 17.7285°E`.

---

## Data files

| Hiker | API `id` | Season | JSON (`tracks/source/`) | GPX (`tracks/source/`) |
|-------|---------:|:------:|-------------------------|------------------------|
| Erik | 2384 | 2026 | `eriks-band-track.json` | `eriks-band.gpx` |
| Jonathan | 2360 | 2026 | `jonathans-band-track.json` | `jonathans-band.gpx` |
| Bernhard | 528 | 2026 | `bernhard-gervide-eckel-s-band-track.json` | `bernhard-gervide-eckel-s-band.gpx` |
| Mårten | 2371 | 2026 | `martens-band-track.json` | `martens-band.gpx` |
| **Noah Bovin** | 451 | 2026 | `noah-bovin-s-band-track.json` | `noah-bovin-s-band.gpx` |
| **Kalle** | 2369 | 2026 | `kalles-band-track.json` | `kalles-band.gpx` |
| **Lotta & Björn** | 2278 | 2026 | `lottas-och-bjorns-band-track.json` | `lottas-och-bjorns-band.gpx` |
| Ola | 419 | 2025 | `olas-vita-band-2-track.json` | `olas-vita-band-2.gpx` |
| Paolo | 2102 | 2021 | `paolo-peralta-s-band-track.json` | `paolo-peralta-s-band.gpx` |

Convert script: `scripts/json_to_gpx.py` · Stats script: `scripts/track_stats.py` · Composite builder: `scripts/build_composite_gpx.py`.

---

## Summary — full route

Distances are sum of GPS segments along each track (not plan-book km).

| Hiker | GPS pts | Total km | Start → End | Days | km/day |
|-------|--------:|---------:|-------------|-----:|-------:|
| **Erik** | **2 619** | 1 232 | 2026-01-17 → 03-16 | 58.2 | 21.2 |
| Mårten | 2 313 | **1 276** | 2026-02-15 → 04-09 | 53.5 | 23.9 |
| **Lotta & Björn** | 2 173 | 1 234 | 2026-02-21 → 04-15 | 53.3 | 23.1 |
| **Noah Bovin** | 2 108 | 1 175 | 2026-02-28 → 04-14 | 45.0 | **26.1** |
| **Kalle** | 1 810 | 1 267 | 2026-02-26 → 04-02 | **35.3** | **35.9** ★ |
| Bernhard | 382 | 1 126 | 2026-02-12 → 04-19 | 66.3 | 17.0 |
| Jonathan | 328 | 1 115 | 2026-01-07 → 03-13 | 65.1 | 17.1 |
| Ola | 300 | 1 111 | 2025-03-04 → 04-24 | 51.1 | 21.7 |
| Paolo | 83 | 1 055 | 2021-02-05 → 05-04 | 88.0 | 12.0 |

---

## Kvikkjokk milestone (resupply)

| Hiker | Arrived Kvikkjokk | Off centre | km/day to Kvikkjokk* |
|-------|:-----------------:|-----------:|---------------------:|
| Jonathan | 2026-02-24 | 0.24 km | 15.8 |
| Erik | 2026-03-01 | 0.37 km | 20.0 |
| Kalle | 2026-03-22 | 0.46 km | **~36** |
| **Mårten** | **2026-03-25** | 0.46 km | 23.3 |
| **Plan target** | **~2026-03-29** | — | **~20** |
| Noah | 2026-04-01 | 0.19 km | 21.6 |
| Lotta & Björn | 2026-04-02 | 0.11 km | 22.0 |
| Bernhard | 2026-04-04 | 0.42 km | 15.2 |
| Ola | 2025-04-09 | 0.45 km | 21.1 |
| Paolo | 2021-04-13 | 2.92 km | 10.7 |

*Track km to Kvikkjokk divided by days.

---

## Milestone passages (km off plan)

S→N · all offsets in **km** · `—` means the hiker did not pass within 50 km.

| Hiker | Grövel | Helags | Blåhamm | Storlien | Gäddede | Klimpf | Hemavan | Ammar | Jäckvik | Kvikkj | Ritsem | Sälka | Abisko | Pältsa |
|-------|-------:|-------:|--------:|---------:|--------:|-------:|--------:|------:|--------:|-------:|-------:|------:|-------:|-------:|
| Erik | 0.18 | 1.32 | 33.5 | 41.7 | 1.53 | 1.76 | 1.00 | 0.27 | 0.13 | 0.37 | 29.2 | 0.17 | 0.34 | 7.75 |
| Jonathan | 11.6 | 11.7 | 35.4 | 43.2 | 1.95 | 1.45 | 1.42 | 0.80 | 0.34 | 0.24 | 28.3 | 0.07 | 0.50 | 7.16 |
| Bernhard | 0.20 | 0.07 | **0.16** | **1.86** | 1.52 | 13.1 | 0.35 | 0.54 | 0.47 | 0.42 | 29.3 | 0.05 | 2.12 | 7.75 |
| Mårten | 0.18 | **0.03** | 9.54 | 10.5 | 1.44 | 1.76 | 0.84 | 0.72 | 0.92 | 0.46 | 29.2 | **0.03** | **0.07** | **0.52** |
| Noah | 0.19 | 1.27 | 33.4 | 41.7 | 1.47 | 1.73 | 11.6 | 0.73 | 0.32 | 0.19 | 29.2 | 0.03 | 1.40 | 8.00 |
| Kalle | 0.21 | 0.07 | 33.5 | 41.9 | **0.68** | 1.40 | 12.1 | 0.73 | 0.38 | 0.46 | 29.2 | 0.02 | 0.09 | 7.74 |
| **L&B** | 0.33 | **0.04** | **0.18** | **0.44** ★ | 1.40 | 1.87 | **0.86** | 0.73 | 0.26 | **0.11** | 29.2 | **0.03** | **0.06** | 7.75 |
| Ola | 0.16 | **0.03** | **0.16** | 1.92 | 1.52 | 1.43 | 1.47 | 0.82 | 2.03 | 0.45 | 29.2 | 0.05 | 2.08 | **0.00** |
| Paolo | 0.46 | 0.07 | 2.27 | 1.88 | 1.59 | 7.13 | 1.58 | 0.84 | 0.53 | 2.92 | **1.17** ★ | 0.01 | 2.05 | 7.75 |

**Notable observations**

- **Storlien village:** Erik, Jonathan, Noah, Kalle, Mårten all skipped Storlien (10–43 km off — Undersåker corridor or väster om). Bernhard, Ola, Paolo, Lotta & Björn entered the village. **L&B got closest at 0.44 km** — primary reason it's used for Section 1+2.
- **Blåhammaren fjällstation:** Only **Bernhard, Ola, Lotta & Björn** pass through (≤ 0.2 km). Everyone else skirts ~9–35 km west or east.
- **Hemavan village skip:** Noah (11.6 km) and Kalle (12.1 km) went väster om — no village resupply stop. All others within 1.6 km of the ICA.
- **Ritsem (Section 5 question):** Only **Paolo** went the Padjelanta-west corridor (1.17 km off Ritsem). All other dense tracks (Mårten, Erik, L&B, Noah, Kalle, Bernhard, Jonathan, Ola) took the **Kungsleden / Saltoluokta line** (≥ 28 km off Ritsem). Because Paolo is only 13 pts on Kvikkjokk→Abisko (avg gap ~17 km), Section 5 now uses an **own planned GPX** (`2027-plan-kvikkjokk-abisko.gpx`, 6 902 pts, Garmin Desktop) on the same Padjelanta-west corridor — Ritsem +0.21 km, Sälka +0.01 km, Abisko +0.18 km.
- **Pältsa finish:** Only Ola finishes exactly at Pältsa (0 km). Mårten gets to 0.52 km. The rest stop at Treriksröset (7–8 km north of Pältsa).

---

## GPS quality tiers

Median time-gap between consecutive points:

| Tier | Hiker(s) | Median gap | Use for |
|------|----------|-----------:|---------|
| Very high | **Erik, Mårten, Kalle, Noah, Lotta & Björn** | **~10 min** | Corridor geometry; near-complete walked distance |
| Medium | Bernhard | ~60 min | Usable line; minor smoothing |
| Low | Jonathan, Ola | ~2 h | Milestone dates; distance likely understated |
| Very low | Paolo | ~24 h | Calendar / corridor sketch only — not for fine route geometry |

Five tracks in the very-high tier. Avg gap between points (any track):

| Hiker | avg gap (m) | max gap (km) |
|-------|------------:|-------------:|
| Erik | 471 | 4.5 |
| Mårten | 552 | 16.7 |
| Noah | 558 | 2.2 |
| L&B | 568 | 9.4 |
| Kalle | 701 | 19.7 |
| Bernhard | 2 955 | 11.5 |
| Jonathan | 3 409 | 15.9 |
| Ola | 3 716 | 16.0 |
| Paolo | 12 867 | 36.3 |

The single big gaps in Mårten (16.7 km, between Klimpfjäll +22 km and +38 km), Kalle (19.7 km, overnight east of Storlien) and L&B (9.4 km, 4 h stop at Klimpfjäll) are local data drops — the rest of those tracks is dense.

---

## Pace spread (full route)

| Band | km/day | Hiker(s) |
|------|-------:|----------|
| Very fast (≥ 30) | **36** | Kalle |
| Fast (22–27) | 24–26 | Mårten, Noah, L&B |
| Moderate (18–22) | 20–22 | Erik, Ola |
| Slow (15–17) | 17 | Bernhard, Jonathan |
| Very slow (≤ 15) | 12 | Paolo |

2027 plan target (~20 km/day from 900 km / 44 days to Kvikkjokk) sits in **Moderate**.

---

## Storlien vs Undersåker fork

| First village | Tracks | 2027 plan |
|---------------|--------|-----------|
| **Storlien** (via Blåhammaren) | Bernhard, Ola, Lotta & Björn, Paolo | **✓ chosen** |
| Undersåker corridor (west) | Erik, Mårten, Noah, Kalle | — |
| Different entry | Jonathan | — |

Plan picks **Storlien** for the day-9 resupply (Coop). Composite Section 1 uses L&B for the Helags → Blåhammaren → Storlien arc.

---

## Quick visual timeline (Kvikkjokk arrival, day 44 = plan target)

```
2021       Paolo ─────────────────────────────● (Apr 13, ~3 km off)
2025                     Ola ────────────────● (Apr 9)
2026  Jonathan ────────● (Feb 24)
      Erik ──────────● (Mar 1)
      Kalle ─────────────● (Mar 22)
      Mårten ─────────────● (Mar 25)
      Noah ─────────────────● (Apr 1)
      L&B ─────────────────● (Apr 2)
      Bernhard ─────────────● (Apr 4)

      Plan target ─────────● (Mar 29, 900 km)
```

---

*Generated from VitaBandet API tracks in `tracks/source/`. Re-run `python3 scripts/track_stats.py` and `python3 scripts/build_composite_gpx.py` after adding new `id=` routes.*
