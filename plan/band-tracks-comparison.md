# Vita Bandet — historical track comparison

Six completed or near-complete Band tracks from [vgb.vitagronabandet.se](https://vgb.vitagronabandet.se), downloaded via `getRouteData.php` and converted to GPX. Factual comparison against the [2028 plan](./dag-for-dag-2028.md) (target **~900 km at Kvikkjokk by ~29 Mar**, start **15 Feb**) — not a pacing prescription.

**2028 plan route:** **Storlien** · **Lapplandsleden** (§3) · **Paolo** Kvikkjokk → Sälka (`paolo-peralta-s-band.gpx`) · **Ola** Abisko → Treriksröset (`olas-vita-band-2.gpx`) · [dag-for-dag](./dag-for-dag-2028.md).

**Reference point:** Kvikkjokk ≈ `66.9513°N, 17.7285°E` (STF / village centre).

---

## Data files

| Hiker | API `id` | Season | JSON | GPX |
|-------|----------|--------|------|-----|
| Erik | 2384 | 2026 | `eriks-band-track.json` | `eriks-band.gpx` |
| Jonathan | 2360 | 2026 | `jonathans-band-track.json` | `jonathans-band.gpx` |
| Bernhard | 528 | 2026 | `bernhard-gervide-eckel-s-band-track.json` | `bernhard-gervide-eckel-s-band.gpx` |
| Mårten | 2371 | 2026 | `martens-band-track.json` | `martens-band.gpx` |
| Ola | 419 | 2025 | `olas-vita-band-2-track.json` | `olas-vita-band-2.gpx` |
| Paolo | 2102 | 2021 | `paolo-peralta-s-band-track.json` | `paolo-peralta-s-band.gpx` |

Convert script: `scripts/json_to_gpx.py`.

---

## Summary — to Kvikkjokk

Distances are **sum of GPS segments** along each track (not plan book km). Times are from track timestamps (no timezone conversion; treated as local wall clock).

| Hiker | Start | At Kvikkjokk | Days | Track km | km/day | Off Kvikkjokk |
|-------|-------|--------------|------|----------|--------|---------------|
| **Ola** | 2025-03-04 | 2025-04-09 | **36** | 760 | **21.1** | 0.5 km |
| **Mårten** | 2026-02-15 | 2026-03-25 | **38** | **890** | **23.3** | 0.5 km |
| **Erik** | 2026-01-17 | 2026-03-01 | 43 | 863 | 20.0 | 0.4 km |
| **Jonathan** | 2026-01-07 | 2026-02-24 | 48 | 756 | 15.8 | 0.2 km |
| **Bernhard** | 2026-02-12 | 2026-04-04 | 51 | 780 | 15.2 | 0.4 km |
| **Paolo** | 2021-02-05 | 2021-04-13 | 67 | 717 | 10.7 | **2.9 km** |

**vs 2028 plan:** ~900 km cumulative, arrive Kvikkjokk **~29 Mar** (day 44; start **15 Feb**).

| Hiker | Distance vs 900 km | Calendar vs ~29 Mar (plan) |
|-------|-------------------|-------------------|
| Mårten | **+10 days late**, **−10 km** (closest match on distance) | Late Mar |
| Erik | **−37 km**, **~2 weeks early** | 1 Mar |
| Ola | **−140 km**, mid-April (later start season) | 9 Apr |
| Jonathan | **−144 km**, early Feb (different start) | Not comparable |
| Bernhard | **−120 km**, **~3 weeks late** | 4 Apr |
| Paolo | **−183 km**, **~1 month late**; did not ping in village | 13 Apr |

---

## Full route

| Hiker | GPS points | Total track km | Days (start → end) | End latitude | Notes |
|-------|------------|----------------|--------------------|--------------|-------|
| Mårten | 2,313 | **1,276** | 53 | 69.05°N | Longest measured line |
| Erik | 2,619 | 1,232 | 58 | 69.06°N | Track ends **16 Mar** — north leg may be truncated in feed |
| Bernhard | 382 | 1,126 | 66 | 69.06°N | Sparse GPS |
| Jonathan | 328 | 1,115 | 65 | 69.05°N | Sparse GPS; offset start |
| Ola | 300 | 1,111 | 51 | 69.05°N | 2025 season |
| Paolo | 83 | 1,055 | 88 | 69.06°N | Very sparse; slow 2021 season |

**After Kvikkjokk** (Padjelanta / KL / north): all six continue **~32–34%** of total distance north (~338–385 km of track), except where the feed stops early (Erik).

---

## Start position

| Hiker | Start offset from Grövelsjön (~62.10°N, 12.31°E) |
|-------|--------------------------------------------------|
| Erik, Bernhard, Mårten, Ola, Paolo | **&lt; 0.5 km** (standard trailhead) |
| Jonathan | **~12 km ENE** — different entry, 10 days before Erik |

---

## Milestone calendar (first GPS near village)

| Milestone | Jonathan | Erik | Ola | Mårten | Bernhard | Paolo |
|-----------|----------|------|-----|--------|----------|-------|
| Grövelsjön area | 2026-01-07 | 2026-01-17 | 2025-03-04 | 2026-02-15 | 2026-02-12 | 2021-02-05 |
| Undersåker | 2026-01-17 | 2026-01-28 | 2025-03-14 | 2026-02-26 | 2026-03-02 | 2021-03-04 |
| Gäddede | 2026-01-29 | 2026-02-08 | 2025-03-22 | 2026-03-04 | 2026-03-10 | 2021-03-19 |
| Hemavan | 2026-02-08 | 2026-02-19 | 2025-03-30 | 2026-03-15 | 2026-03-24 | 2021-04-02 |
| **Kvikkjokk** | **2026-02-24** | **2026-03-01** | **2025-04-09** | **2026-03-25** | **2026-04-04** | **2021-04-13** |

Jonathan is **~2–3 weeks ahead** of the main 2026 Grövelsjön cohort through the south. Bernhard is **~3–5 weeks behind** from Hemavan onward.

---

## GPS data quality

Median time between points **before Kvikkjokk**:

| Tier | Hiker | Median gap | Use for |
|------|-------|------------|---------|
| High | Erik, Mårten | **~10 min** | Corridor shape; walked distance more complete |
| Medium | Ola | **~2.7 h** | Usable line; may be slightly smoothed |
| Low | Jonathan, Bernhard | **~2 h** | Milestone dates; distance likely understated |
| Very low | Paolo | **~24 h** | Calendar spread only; not for route geometry |

Sparse tracks connect straight lines between pings — **zigzags and detours disappear**, so km totals trend **low** vs dense tracks for the same hike.

---

## Corridor — same Band, different lines

All six follow the **south→north Vita Bandet corridor** (mountain chain, resupply villages). Lateral spread between tracks (sampled vs one dense 2026 line): typical **~5 km**, max **~30–47 km** — different valleys and resupply approaches, same expedition.

Typical separation **~5 km** is normal (wide corridor, weather, resupply roads). Occasional **30–47 km** splits are different valleys or approach routes — not a different expedition.

---

## Takeaways for 2028 planning

### Resupply (Kvikkjokk)

All except Paolo ping **within ~0.5 km** of Kvikkjokk centre — confirms **STF Kvikkjokk** resupply. **§5:** plan uses **Paolo corridor** Kvikkjokk → Ritsem → **Sälka** (`paolo-peralta-s-band.gpx`).

### Distance spread (GPS, to Kvikkjokk)

Plan book **900 km** sits in the middle of what people actually walked:

- **Lower track km:** Jonathan 756, Ola 760, Paolo 717 (sparse / straighter lines)
- **Higher track km:** Mårten 890, Erik 863 (dense tracks, more zigzag)

### Pace spread (GPS, to Kvikkjokk)

| Band | km/day | Who |
|------|--------|-----|
| Fast | 21–23 | Ola, Mårten, Erik |
| Moderate | 15–16 | Jonathan, Bernhard |
| Slow | ~11 | Paolo |

Your **plan pace** (~20 km/day from 900 km / 44 days) is your own target — historical tracks only show **range**, not which line to copy.

### First resupply fork (Grövelsjön area)

| Via | Tracks | 2028 plan |
|-----|--------|-----------|
| **Undersåker** | Erik, Jonathan | — |
| **Storlien** | Ola, Bernhard, Mårten, Paolo | **✓ chosen** |

Undersåker **W** (väster om, day 12) — not the Storlien shop corridor; no village stop.

---

## Quick visual timeline (Kvikkjokk arrival)

```
2021        Paolo ─────────────────────────────● (Apr 13, ~3 km off)
2025              Ola ────────────────● (Apr 9)
2026  Jonathan ────────● (Feb 24)
      Erik ──────────● (Mar 1)
      Mårten ─────────────● (Mar 25)
      Bernhard ──────────────────● (Apr 4)
      
      Plan target ────────────────● (29 Mar, 900 km)
```

---

*Generated from VitaBandet API tracks in `plan/`. Re-run analysis after downloading new `id=` routes.*
