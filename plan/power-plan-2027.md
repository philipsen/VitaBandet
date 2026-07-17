# Power plan — daily usage · Vita Bandet 2027

**Your profile (17 Jul 2026)** — built from your device list and usage answers.  
**Hardware:** [gear-inventory-2027.md](./gear-inventory-2027.md) · **Kit choices:** [gear-considerations-2027.md](./gear-considerations-2027.md#power-banks-wall-charger--cables)

**Planning assumption:** **14 days** max without wall power · **2× Anker Zolo 20k** (~144 Wh nominal) · warm-bank cold strategy with **~30% cold margin**.

---

## Devices on trail

| Device | Role | Daily use (your answers) | Charge port |
|--------|------|--------------------------|-------------|
| **GPSMAP 68i** | Primary GPS + inReach SOS | Expedition mode · screen off skiing · **10 min** tracking · **2–5 msgs/day** | USB-C |
| **Fairphone 5** | OsmAnd · photos · reading · messages | **Off/airplane** on ski day (jacket) · **camp** OsmAnd + 10–30 photos + reading + messages | USB-C PD |
| **Nitecore NU43** | Tent · cook · melt | **~1 h/night** — mostly low/mid, some red | USB-C |
| **Suunto Vertical 2** | Time · HR · notifications · flashlight backup | **Daily wear** · wrist-raise · not primary GPS | Proprietary USB (pack cable) |
| **Fairbuds XL** | Camp audio | **30–60 min/night** camp only | USB-C (on ear cup) |
| **Kindle (basic e-ink)** | Reading | Resupply charge only — weeks of runtime | Micro-USB or USB-C (model dependent) |
| **2× Anker Zolo 20k** | Storage + on-trail charging | One **warm on body** skiing · one in pulk | USB-C in/out |
| **Anker 100 W wall** | Resupply / hut refill | Both banks + all devices overnight | 2× C + 1× A |

**Not charging on trail:** Calazo maps · compass · CO sensor · headlamp spare (none).

---

## Daily rhythm

### Ski day (~8 h on trail)

| Time | Action |
|------|--------|
| **Morning** | 68i on · expedition mode · confirm inReach tracking **10 min** · phone **airplane mode** |
| **Pack** | **Bank A** in chest/jacket pocket (warm) · 68i on body · Suunto on wrist · Fairphone in jacket pocket (off) |
| **On trail** | 68i screen off — LED blink only · glance map only if needed · **no phone** |
| **inReach** | Batch messages at **lunch** or **camp** — not spread through ski hours |
| **Bank B** | In pulk top — **not** used while moving unless emergency |

### Camp / hut night

| Order | Task | Power |
|-------|------|-------|
| 1 | Tent up · melt start | NU43 **low/mid** ~20–30 min |
| 2 | **Boots off · booties** | — |
| 3 | Dinner + camp chores | NU43 as needed · Suunto stays on wrist |
| 4 | **Charge window** (~45–90 min) | See [charge calendar](#charge-calendar-14-day-cycle) — one or two devices from **warm Bank A** |
| 5 | Phone on — **OsmAnd** tomorrow track · photos · messages | Fairphone **~45–90 min** screen (biggest drain) |
| 6 | Reading | Kindle (no charge) · Fairbuds if wanted |
| 7 | Pre-sleep | Phone **airplane mode** · NU43 off · **phone + Bank A** in **bag foot** · 68i stays on body or bag top |

### Hut night (power available)

**Charge everything** — your rule. Priority order when outlets are limited:

1. **Both Zolo banks** (empty → full first — restores trail autonomy)
2. **Fairphone** (full)
3. **68i** (full)
4. **Suunto Vertical 2**
5. **NU43** · **Fairbuds**
6. **Kindle** (if due)

Use **your Anker 100 W** brick — hut USB ports are often weak / shared.

---

## Recommended device settings

### GPSMAP 68i

| Setting | Value | Why |
|---------|-------|-----|
| Mode | **Expedition** (auto or prompted) | **425 h** spec with inReach vs 165 h at 10 min normal GPS |
| inReach tracking | **10 min** | Your choice — balance SOS trail vs drain |
| Screen | **Off while skiing** | Expedition dims + fewer track points |
| Messages | **2–5/day batched** at camp | Typing on device in −20 °C costs power + patience |
| Charge target | **Top up every 3–4 days** | Expedition mode stretches far — every 2–3 days is fine if you prefer margin |

### Fairphone 5

| Setting | Value | Why |
|---------|-------|-----|
| Ski day | **Airplane mode** (or off) | Zero drain in jacket |
| Camp | Wi‑Fi/cell **on** only for messages window | OsmAnd works offline |
| Brightness | **Low** + short timeout | Cold + OLED = fast drain |
| Photos | **Moderate** — review/delete duds same night | Saves storage + export drain |
| Charge target | **Every 2 nights** to ~80% | See phone recommendation below |

### Suunto Vertical 2

| Setting | Value | Why |
|---------|-------|-----|
| Daily mode | Smartwatch · **HR on** | Your daily-wear use |
| Display | Wrist-raise **on** · brightness **medium-low** | 20-day spec drops fast in cold |
| GPS during ski | **Off** — 68i is primary | Saves massive drain |
| Flashlight | NU43 first · Suunto LED for **glove tasks only** | AMOLED + LED adds drain |
| Charge target | **Every 3 nights** (~30–40%) | Stretch to match phone rhythm |

### NU43

| Setting | Value | Why |
|---------|-------|-----|
| Camp default | **Low (100 lm)** or **mid (300 lm)** | ~1 h/night ≈ **3–7%**/night |
| Inside tent | **Red constant** | Night vision + 66 h runtime |
| Charge target | **Every 7–10 nights** partial top-up | Full charge only at ★ or hut |

### Fairbuds XL

| Setting | Value | Why |
|---------|-------|-----|
| Use | **Camp only** · 30–60 min | ~2–4%/night |
| ANC | **Off** in tent if solo | Saves ~15% vs ANC on |
| Charge target | **Every 7 days** or when case/phones hit ~30% |

### Kindle

| Setting | Value | Why |
|---------|-------|-----|
| Charge | **At ★ resupply only** | Basic e-ink lasts **3–4+ weeks** |
| Airplane | **On** always | Irrelevant drain either way |

---

## Energy budget (estimates)

*Wh = watt-hours stored in device battery. Cold reduces **effective bank output** ~20–40% — plan below uses **~30% margin**.*

| Device | Battery (≈) | Daily drain (your use) | Wh/day |
|--------|-------------|------------------------|--------|
| **68i** | ~12 Wh | Expedition + 10 min track + msgs | **~0.6–0.8** |
| **Fairphone 5** | ~16 Wh | Camp OsmAnd + photos + reading + msgs | **~3–4** |
| **NU43** | ~13 Wh | ~1 h low/mid | **~0.4** |
| **Suunto V2** | ~18 Wh | Daily smartwatch · no ski GPS | **~1.0–1.5** |
| **Fairbuds XL** | ~3 Wh | 30–60 min camp | **~0.15** |
| **Kindle** | ~2 Wh | Reading only | **~0.05** |
| **Total** | | | **~5.5–7 Wh/day** |

**14-day leg (no wall, no hut):** ~**77–98 Wh** device demand + **~15 Wh** bank self-loss/cold inefficiency ≈ **~95–115 Wh** needed.  
**2× Zolo full** = **~144 Wh** nominal → **~100–115 Wh** effective after cold → **fits 14 days** if you follow the charge calendar and don’t nightly-full-charge everything.

---

## Charge calendar (14-day cycle)

**Bank roles:** **A** = on body (primary) · **B** = reserve in pulk  
**Rule:** Only charge from a bank that has been **warm 15+ min** against body before plugging in.

| Night | Charge from Bank A | Notes |
|-------|-------------------|-------|
| **D1** | Fairphone → ~80% | After camp OsmAnd session |
| **D2** | Suunto → ~70% | Phone off · 68i still fine |
| **D3** | Fairphone → ~80% | |
| **D4** | **68i** → full | First 68i top-up · expedition mode stretch |
| **D5** | Suunto + NU43 partial | NU43 ~30 min top-up if needed |
| **D6** | Fairphone → ~80% | |
| **D7** | Fairphone + Fairbuds | Weekly buds top-up |
| **D8** | Suunto → ~70% | |
| **D9** | Fairphone → ~80% | |
| **D10** | **68i** → full | Second 68i top-up |
| **D11** | Suunto | |
| **D12** | Fairphone → ~80% | Bank A getting low — see below |
| **D13** | **Swap banks** — retire A to pulk · **Bank B** (full reserve) → body | Critical before empty |
| **D14** | Fairphone partial · 68i if needed | Enter ★ **next day** with B as warm bank |

**When Bank A hits ~25%:** Stop topping phone to 80% — **sips only** (Fairphone to 50%, 68i if below 40%). Save **Bank B** for D13 swap or emergency.

**Phone recommendation (you asked):** **Every 2 nights to ~80%** — not nightly full. Nightly 100% would add ~**25%** unnecessary Wh over 14 days.

**68i recommendation:** Your “every 2–3 days” is safe; **every 3–4 days** is enough in expedition mode — saves ~**8–12 Wh** per leg vs charging every 2 days.

---

## Bank rotation & carry

| Location | Item |
|----------|------|
| **Chest / jacket** | 68i · **Bank A (warm)** · Fairphone (off) |
| **Wrist** | Suunto Vertical 2 |
| **Head** | NU43 (evening only) |
| **Pulk top** | **Bank B** · wall charger · spare cables · Kindle |
| **Bag foot (sleep)** | Phone + Bank A when not charging |

**Overnight tent:** Phone + active bank in sleeping bag foot — **never** charge a cold bank below **−10 °C** without warming first.

---

## Cold-weather rules (recommended margin)

You were unsure — default to **conservative**:

| Temp | Rule |
|------|------|
| **0 to −10 °C** | Warm bank 10 min in jacket before use |
| **−10 to −20 °C** | Warm bank **15–20 min** · charge **one device at a time** |
| **Below −20 °C** | Banks live in jacket or bag foot · **no wall charging outside** · assume banks deliver **~65–70%** of rated Wh |
| **All temps** | Dry **68i** port cap before every plug |

**Skip heated Summit bank** unless shakedown shows Zolo won’t charge devices after warming — saves **~€120** and **~50 g** vs one Summit + one Zolo.

---

## ★ Resupply overnight checklist

At every shop stop (**Storlien · Gäddede · Hemavan · Kvikkjokk · Ritsem · Abisko · …**):

- [ ] Wall → **Bank B** full (then **Bank A**)
- [ ] **Fairphone** full
- [ ] **68i** full
- [ ] **Suunto** full
- [ ] **NU43** full
- [ ] **Fairbuds** full
- [ ] **Kindle** if &lt;50% or every 2nd resupply
- [ ] Note bank **%** in trail log — catch early fade
- [ ] Repack: **both banks full** · wall + cables in pulk · **Bank A** in jacket next morning

**Time budget:** ~**6–8 h** unattended overnight (both 20k banks @ 20 W in ≈ **4–5 h** each; run **parallel** on 100 W wall ≈ **3–4 h** total).

---

## Cables to pack (+1 for Suunto)

| Cable | For |
|-------|-----|
| **3× short braided USB-C ↔ C** | 68i · Fairphone · NU43 / Fairbuds / bank↔wall |
| **1× spare C–C** | Repair pouch |
| **1× Suunto Vertical 2 charge cable** | Watch — proprietary |
| **1× Kindle cable** | Micro-USB or USB-C — match your unit |
| **Wall box 1.5 m C–C** | Hut / hotel overnight only |

---

## Shakedown — validate this plan

Log **start % / end %** each day for one **3-night −15 °C** tent test:

1. **Day 1:** Ski 6–8 h · 68i expedition · phone airplane · camp OsmAnd 45 min + 15 photos  
2. **Day 2:** Repeat · charge Fairphone from warm bank · note Wh feel (bank % drop)  
3. **Day 3:** Add inReach **3 messages** · Suunto charge · compare to table above  

**Pass criteria:** Bank A drops **≤35%** over 3 days with one phone charge + one watch charge. If higher → extend phone to **every 3 nights** or drop Suunto to **HR off**.

---

## Quick reference card (print / phone note)

```
SKI DAY     68i expedition ON · phone AIRPLANE · Bank A in jacket
CAMP        NU43 low · phone ON for OsmAnd/photos/messages ~1h
CHARGE      Phone every 2 nights · 68i every 3–4 nights · Suunto every 3 nights
            NU43 + Fairbuds weekly · Kindle at ★ only
HUT         Charge ALL — banks first
COLD        Warm bank 15 min before USB · one device at a time below −20 °C
SOS         68i always on BODY
```

---

## Links

- [gear-inventory-2027.md](./gear-inventory-2027.md) — weights & purchase list  
- [gear-considerations-2027.md](./gear-considerations-2027.md#power-banks-wall-charger--cables) — bank/charger specs  
- [resupply-2027.md](./resupply-2027.md) — ★ shop stops  
- [pack-checklist-2027.md](./pack-checklist-2027.md) — pack verification  
