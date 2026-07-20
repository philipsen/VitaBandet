# Band track alternatives — scrape set (≥500 pts)

**Source:** `tracks/scrape/` · **32** completed White Ribbon tracks with **≥500** GPS points (VGB `getRouteData`, Jul 2026).  
**Method:** nearest-point offset to fixed milestones (same idea as [band-tracks-comparison.md](./band-tracks-comparison.md)).

---

## Inventory

| Pts range | Count | Notes |
|----------:|------:|-------|
| ≥1000 | 19 | Dense enough for corridor stitching |
| 500–999 | 13 | Useful for fork detection; gaps larger |
| **Total** | **32** | Years **2019–2026** (older seasons mostly empty on API) |

---

## Major forks (what differs)

### 1. Section 5 — **Padjelanta / Ritsem** vs **Kungsleden / Saltoluokta**

| Corridor | Tracks | Ritsem off | Saltoluokta off |
|----------|--------|------------|-----------------|
| **Padjelanta-west (via Ritsem)** | **Evelina Silokangas** (2020, 2850 pts) · **Hannes & Ebba** (2026, 918) · **Jonas Peterson** (2019, 591) | ≤1.1 km | 15–56 km |
| **Kungsleden (via Saltoluokta)** | **28 / 32** tracks | ~27–29 km | ≤1.3 km |

**2027 plan** uses Padjelanta-west — historically **rare** among dense GPS tracks. Best historical reference for that corridor in this set: **Evelina** (dense + finishes Pältsa). Hannes/Ebba also hit Ritsem but are thinner and farther from Sälka (~10 km).

### 2. Storlien village vs skip

| Choice | Count | Examples |
|--------|------:|----------|
| **Through Storlien** (≤2 km) | 8 | Lotta & Björn · Kall på tur · Silvana · Emil · Evelina · Roy · Hannes/Ebba · Jonas |
| **Skip** (Undersåker / west corridor, ≫8 km) | 24 | Erik · Mårten · Noah · Kalle · most 2025–26 |

### 3. Blåhammaren

| Choice | Count |
|--------|------:|
| **Via station** (≤1 km) | 6 — Emil · Hannes/Ebba · Jonas · Kall · L&B · Silvana |
| **Bypass** | 24 |

### 4. Hemavan village

| Choice | Count | Examples |
|--------|------:|----------|
| **Village / ICA** (≤2 km) | 23 | Most |
| **West skip** (>5 km) | 8 | Noah · Kalle · Lenita/Lisbeth · Tuss · Anders · Jonas · one Christian-och-Benni |

### 5. Finish — Pältsa vs Treriksröset

| Finish | Count |
|--------|------:|
| **Pältsa** (≤1 km) | 8 — Evelina · Hannes/Ebba · Lenita/Lisbeth · Mårten · Mette · Mika · Upplevelserik |
| **Treriksröset** (~7–8 km N of Pältsa) | 16 |

### 6. Adolfström

Almost every track passes **~1.1 km** from the village pin — that is the **Band corridor west of Adolfström**, not proof of a Handelsbod visit. True shop detour needs a hand check / diary, not GPS alone.

---

## Tracks worth opening for alternatives

| Track | Pts | Why look |
|-------|----:|----------|
| **Evelina Silokangas** | 2850 | Dense **Padjelanta + Ritsem** + Storlien + **Pältsa** |
| **Hannes och Ebbas band** | 918 | Second **Ritsem** track; Storlien + Blåhammaren |
| **Jonas Peterson** | 591 | Third **Ritsem**; Storlien + Blåhammaren; Hemavan west |
| **Lottas och Björns Band** | 2173 | Classic **Storlien + Blåhammaren** corridor (plan S1–S2) |
| **Kall på tur** | 2472 | Storlien + Blåhammaren on KL-north finish |
| **Noah / Kalle** | 2108 / 1810 | **Hemavan west-skip** on main KL S5 |

Files: `tracks/scrape/<slug>.gpx` (+ `-track.json`).

---

## Still missing / thin

- **2024:** API still returns **empty** locations for all completed White Ribbons that year.
- Pre-**2019:** almost no ≥500-pt tracks in the public VGB feed.
- **Paolo** (Padjelanta pioneer in older comparison) is only **83 pts** — below this cut; still in `tracks/source/` if needed.
