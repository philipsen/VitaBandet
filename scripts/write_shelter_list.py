#!/usr/bin/env python3
"""Turn the Overpass shelter JSON into the plan list."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "plan" / "shelters-along-track-2027.json"
OUT = ROOT / "plan" / "shelters-along-track-2027.md"

# Winter 2027 staffed windows already checked against STF pages.
STF_WINTER = {
    "grovelsjon": "14 Jan – 18 Apr 2027 · station open, restaurant closed",
    "rogen": "19 Feb – 18 Apr 2027",
    "helags": "5 Mar – 18 Apr 2027",
    "sylarna": "5 Mar – 18 Apr 2027",
    "blahammaren": "5 Mar – 18 Apr 2027",
    "blåhammaren": "5 Mar – 18 Apr 2027",
    "storulvan": "25 Feb – 18 Apr 2027",
    "storulvån": "25 Feb – 18 Apr 2027",
    "saltoluokta": "26 Feb – 18 Apr 2027",
    "ritsem": "26 Feb – 25 Apr 2027",
    "sitasjaure": "26 Feb – 25 Apr 2027",
    "hukejaure": "26 Feb – 25 Apr 2027",
    "salka": "19 Feb – 18 Apr 2027",
    "sälka": "19 Feb – 18 Apr 2027",
    "tjaktja": "19 Feb – 18 Apr 2027",
    "tjäktja": "19 Feb – 18 Apr 2027",
    "alesjaure": "19 Feb – 18 Apr 2027",
    "abiskojaure": "19 Feb – 18 Apr 2027",
    "abisko": "Year-round",
    "paltsa": "19 Mar – 18 Apr 2027",
    "pältsa": "19 Mar – 18 Apr 2027",
    "paltastugan": "19 Mar – 18 Apr 2027",
    "kebnekaise": "26 Feb – 18 Apr 2027",
    "vakkotavare": "26 Feb – 18 Apr 2027",
    "serve": "26 Feb – 2 May 2027 (day plan)",
}

# Lock facts read off the operator page, not guessed for the whole chain.
DNT_LOCK = {
    "dividal": "Locked, DNT key. Open all year. Pay. A Troms Turlag member has to be in the party.",
    "altevas": "Code lock. The code comes with a prebooking. Not the standard DNT key.",
    "darta": "Troms Turlag. DNT key (not on their code-lock list).",
}

CORRIDOR = {
    "plan": "plan",
    "undersaker": "Undersåker",
    "hemavan-village": "Hemavan village",
    "kungsleden": "Kungsleden",
    "finish-traditional": "traditional finish",
}


def norm(s: str) -> str:
    return (
        s.lower()
        .replace("å", "a")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("é", "e")
        .replace("æ", "a")
        .replace("ø", "o")
        .replace(" ", "")
        .replace("-", "")
    )


def stf_window(name: str) -> str:
    n = norm(name)
    for key, window in STF_WINTER.items():
        if norm(key) in n:
            return window
    return ""


def dnt_lock(name: str) -> str:
    n = norm(name)
    for key, text in DNT_LOCK.items():
        if key in n:
            return text
    return ""


def display_name(name: str, tags: dict) -> str:
    if name:
        return name
    st = tags.get("shelter_type") or "shelter"
    return {
        "lean_to": "Lean-to",
        "basic_hut": "Basic hut",
        "weather_shelter": "Weather shelter",
    }.get(st, "Shelter")


def is_stf(name: str, tags: dict) -> bool:
    op = (tags.get("operator") or "") + (tags.get("brand") or "")
    if "turistfören" in op.lower() or "turistforen" in op.lower() or op.strip().upper() == "STF":
        return True
    if "laponia" in op.lower() or "badjel" in op.lower():
        return False
    if norm(name).startswith("havlingestug"):
        return False
    n = norm(name)
    return "fjallstuga" in n or "fjallstation" in n


def kind_of(name: str, tags: dict) -> str:
    blob = " ".join(
        [
            name,
            tags.get("operator", ""),
            tags.get("brand", ""),
            tags.get("shelter_type", ""),
            tags.get("tourism", ""),
        ]
    ).lower()
    if "metsahallitus" in blob or "metsähallitus" in blob:
        if "varaustupa" in blob:
            return "Finnish reservation hut"
        if "autiotupa" in blob:
            return "Finnish open hut"
        return "Finnish hut"
    if "statskog" in blob:
        return "Statskog hut"
    if "laponia" in blob or "badjel" in blob:
        return "Laponia cabin"
    if any(w in blob for w in ("rastskydd", "raststuga", "nodstuga", "nödstuga")):
        return "Rastskydd"
    if "vindskydd" in blob or tags.get("shelter_type") == "lean_to":
        return "Vindskydd"
    if tags.get("shelter_type") == "weather_shelter":
        return "Weather shelter"
    if any(w in blob for w in ("dnt", "turistforening", "turlag")) or name.lower().endswith("hytta"):
        return "Norway hut"
    if is_stf(name, tags):
        if any(w in blob for w in ("station", "turiststation", "fjällstation", "wardshus", "värdshus")):
            return "STF station"
        return "STF hut"
    if "lansstyrel" in blob or "länsstyrel" in blob or norm(name).startswith("havlingestug"):
        return "County cabin"
    if tags.get("tourism") == "alpine_hut":
        return "Alpine hut"
    if tags.get("tourism") == "wilderness_hut":
        return "Wilderness hut"
    if tags.get("shelter_type") == "basic_hut":
        return "Basic hut"
    return "Shelter"


def facts(name: str, tags: dict, kind: str) -> tuple[str, str, str]:
    """open, locked, sleep — only from a tag or a cited rule for that kind."""
    access = (tags.get("access") or "").lower()
    locked_tag = (tags.get("locked") or "").lower()
    hours = tags.get("opening_hours") or ""
    window = stf_window(name) if kind.startswith("STF") else ""

    if "pieljekaise" in norm(name) and "rast" not in norm(name):
        return (
            "Day room open year-round",
            "Day room unlocked. The 4-bed room is locked.",
            "Yes, if you take the key at Handlar'n in Jäckvik or Handelsboden in Adolfström",
        )
    if norm(name).startswith("havlingestug"):
        kind = "County cabin"
        return (
            "Year-round building",
            "Unlocked",
            "Yes. Dalarna’s unlocked cabins here are 100–200 kr a bed",
        )

    if access == "private" or locked_tag == "yes" and kind not in {"Rastskydd", "STF hut", "STF station"}:
        locked = "Locked" if locked_tag == "yes" else "Private"
        if access == "private":
            locked = "Private"
        return (hours or "Not stated", locked, "No")

    if kind == "Rastskydd":
        return ("Year-round building", "Unlocked", "Emergency only")

    if kind == "Finnish open hut":
        return ("Year-round", "Unlocked", "Yes, free, one or two nights. No booking")
    if kind == "Finnish reservation hut":
        return ("Year-round", "Locked without a booking", "Yes, paid bed, booked ahead")
    if kind == "Statskog hut":
        return (hours or "Not stated", "Unlocked" if access == "yes" or locked_tag != "yes" else "Locked", "Short stay. Confirm the cabin on ut.no")
    if kind == "Laponia cabin":
        return (hours or "Not stated", "Not stated", "Not stated — see laponia.nu for this cabin")

    if kind in {"Vindskydd", "Weather shelter", "Basic hut"}:
        locked = "Unlocked" if locked_tag != "yes" and access != "private" else "Locked"
        if access == "yes":
            locked = "Unlocked (map tag)"
        return ("Year-round building", locked, "Not stated")

    if kind.startswith("STF"):
        open_ = window or (hours or "Seasonal — winter dates not in the openings file")
        n = norm(name)
        no_safety = ("grovelsjon" in n) or ("vakkotavare" in n) or n in {
            "abisko",
            "abiskoturiststation",
            "stfabisko",
            "stfabiskoturiststation",
        }
        if no_safety:
            return (
                open_,
                "No safety room at this station.",
                "Yes, pay, while the station is open. No safety room when it is closed.",
            )
        return (
            open_,
            "Staffed rooms while open. Safety room stays unlocked when the hut is closed.",
            "Yes, pay, while staffed. Outside the season the safety room is for an emergency, not a planned night.",
        )

    if kind == "Norway hut":
        specific = dnt_lock(name)
        if specific:
            open_ = "Open all year" if "all year" in specific.lower() else (hours or "Not stated")
            return (open_, specific, "Yes, pay")
        if locked_tag == "no" or access == "yes":
            return (hours or "Not stated", "Unlocked (map tag)", "Yes if it is a public hut — confirm the fee")
        return (hours or "Not stated", "Not stated — check ut.no", "Yes, pay, if it is a DNT hut. Confirm the lock on ut.no")

    if kind == "County cabin":
        locked = "Unlocked" if locked_tag != "yes" and access != "private" else "Locked"
        if access == "yes":
            locked = "Unlocked (map tag)"
        return (hours or "Not stated", locked, "Often a paid night — the fee is posted in the cabin. Confirm it is not a rest shelter.")

    if access == "yes" and locked_tag != "yes":
        locked = "Unlocked (map tag)"
    elif locked_tag == "no":
        locked = "Unlocked (map tag)"
    else:
        locked = "Not stated"
    sleep = "Not stated"
    if tags.get("fee") == "yes":
        sleep = "Fee tagged on the map. Overnight rule not stated."
    return (hours or "Not stated", locked, sleep)


def corridor_note(near: dict) -> str:
    bits = []
    for key, label in CORRIDOR.items():
        if key == "plan" or key not in near:
            continue
        bits.append(f"{label} {near[key]['km_off']:.2f} km")
    return ", ".join(bits)


def row_line(r: dict, along_key: str) -> str:
    near = r["near"][along_key]
    if r["tags"].get("shelter_type") in {"picnic_shelter", "rock_shelter"}:
        return ""
    name = display_name(r["name"], r["tags"])
    tags = r["tags"]
    kind = kind_of(name, tags)
    open_, locked, sleep = facts(name, tags, kind)
    op = tags.get("operator") or tags.get("brand") or ""
    note_bits = [b for b in (op, corridor_note(r["near"]) if along_key == "plan" else "") if b]
    note = " · ".join(note_bits)
    return (
        f"| {near['along_km']:.0f} | {near['km_off']:.2f} | {name} | {kind} | {open_} | {locked} | {sleep} | "
        f"{r['lat']:.5f}, {r['lon']:.5f} | {note} |"
    )


def main() -> None:
    data = json.loads(SRC.read_text())
    rows = data["shelters"]
    def listed(r: dict) -> bool:
        return r["tags"].get("shelter_type") not in {"picnic_shelter", "rock_shelter"}

    rows = [r for r in rows if listed(r)]
    plan = [r for r in rows if "plan" in r["near"]]
    plan.sort(key=lambda r: r["near"]["plan"]["along_km"])

    lines = [
        "# Shelters within 3 km — 2027",
        "",
        "Pulled from OpenStreetMap on **22 Nov 2026** (`tourism=wilderness_hut`, `tourism=alpine_hut`, `amenity=shelter`).",
        "Distance is to the composite plan track, Grövelsjön → Treriksröset, and to the four picked alternatives:",
        "Undersåker (Helags → Olden), the Hemavan village line, Kungsleden (Kvikkjokk → Sälka), and the traditional Abisko finish.",
        "A shelter on the plan is listed once. One that is only on an alternative is in the later tables.",
        "Bus shelters are left out. An unnamed shelter with no type is left out.",
        "",
        "Map tags are thin. **Open**, **locked**, and **sleep** below use the tag when it exists, otherwise the rule for that kind of building.",
        "Where the cell says **not stated**, the map and these rules do not answer it.",
        "",
        "**Rastskydd.** County rest shelters on the state trail. The building is there year-round and is unlocked, for a rest or for bad weather.",
        "A planned night is not allowed. Wood is for an emergency.",
        "[Jämtland](https://www.lansstyrelsen.se/jamtland/besoksmal/fjallvarlden.html) ·",
        "[Dalarna](https://www.lansstyrelsen.se/dalarna/besoksmal/stugor-i-dalafjallen.html) ·",
        "[Västerbotten](https://www.lansstyrelsen.se/vasterbotten/besoksmal/stugor.html) ·",
        "[Norrbotten](https://www.lansstyrelsen.se/norrbotten/besoksmal/friluftsliv-och-allemansratt/leder-och-stugor.html) ·",
        "[STF](https://www.svenskaturistforeningen.se/boende/boendetyper/fjallstuga/).",
        "",
        "**STF huts and stations.** Pay and sleep there while the hut is staffed.",
        "When it is closed, a safety room stays unlocked for an emergency, not for a planned night.",
        "Abisko, Grövelsjön, and Vakkotavare have no safety room.",
        "Winter 2027 dates are the ones already in [stf-openings-2027.md](./stf-openings-2027.md). Serve’s dates are the ones in the day plan.",
        "Other STF huts on this list still need their own page checked.",
        "",
        "**County cabins** (not rest shelters). Often unlocked, with a fee on a notice in the room. Dalarna’s unlocked overnight cabins are 100–200 kr a bed. Västerbotten’s stugor are 200 kr; a koja there is free. The map does not always say which of those a cabin is.",
        "",
        "**Norway.** DNT and turlag huts are paid. Many unstaffed ones are locked with the DNT key; some use a code.",
        "[What the lock status means](https://hjelp.ut.no/hc/no/articles/8731118341394-Hva-betyr-l%C3%A5sestatusen-p%C3%A5-hyttene).",
        "Dividalshytta: DNT key, open all year ([DNT](https://hyttebestilling.dnt.no/hytte/10659)).",
        "Altevasshytta: code lock, code with a booking ([Troms Turlag](https://www.dnt.no/dnt-der-du-er/troms-turlag/lokale-hytter/dnt-nokkel/)).",
        "Every other Norway hut on this list still needs its ut.no page.",
        "",
        "**Not in this map pull.** STF Abisko Turiststation sits in the village and is open year-round; it is tagged as a station, not a mountain hut, so it is not a row below.",
        "Gåsen’s STF hut closed on 1 Jan 2024. Länsstyrelsen Jämtland has put a new rest shelter about 400 m southwest of the old site. That shelter did not come back in this pull.",
        "A building that was never mapped will be missing. The day-plan names that did come back are in the table.",
        "",
        f"**{len(plan)}** on the plan track. **{len(rows) - len(plan)}** only on an alternative.",
        "",
        "## On the plan track",
        "",
        "| km | Off | Name | Kind | Open | Locked | Sleep | Position | Note |",
        "|---:|----:|------|------|------|--------|-------|----------|------|",
    ]
    for r in plan:
        line = row_line(r, "plan")
        if line:
            lines.append(line)

    for key, title in (
        ("undersaker", "Undersåker — Helags to Olden, not on the plan"),
        ("hemavan-village", "Hemavan village line, not on the plan"),
        ("kungsleden", "Kungsleden — Kvikkjokk to Sälka, not on the plan"),
        ("finish-traditional", "Traditional Abisko finish, not on the plan"),
    ):
        extra = [r for r in rows if key in r["near"] and "plan" not in r["near"]]
        extra.sort(key=lambda r: r["near"][key]["along_km"])
        lines += [
            "",
            f"## {title}",
            "",
            f"**{len(extra)}** shelters within 3 km of this line and more than 3 km from the plan track.",
            "",
            "| km | Off | Name | Kind | Open | Locked | Sleep | Position | Note |",
            "|---:|----:|------|------|------|--------|-------|----------|------|",
        ]
        body = [row_line(r, key) for r in extra]
        body = [line for line in body if line]
        if not body:
            lines.append("|  |  | — |  |  |  |  |  |  |")
        lines.extend(body)

    lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(plan)} on plan)")


if __name__ == "__main__":
    main()
