#!/usr/bin/env python3
"""Convert VitaBandet-style location JSON to GPX track."""

import json
import sys
from datetime import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement

GPX_NS = "http://www.topografix.com/GPX/1/1"


def parse_time(time_str: str) -> str:
    """Parse 'YYYY-MM-DD HH:MM' to ISO 8601 UTC."""
    dt = datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M")
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_gpx(data: dict) -> ET.ElementTree:
    name = data.get("name", "Track")
    locations = data.get("locations", [])

    gpx = Element("gpx", attrib={
        "version": "1.1",
        "creator": "VitaBandet",
        "xmlns": GPX_NS,
    })

    metadata = SubElement(gpx, "metadata")
    SubElement(metadata, "name").text = name

    trk = SubElement(gpx, "trk")
    SubElement(trk, "name").text = name
    trkseg = SubElement(trk, "trkseg")

    for loc in locations:
        trkpt = SubElement(trkseg, "trkpt", attrib={
            "lat": f"{loc['lat']:.8f}".rstrip("0").rstrip("."),
            "lon": f"{loc['lng']:.8f}".rstrip("0").rstrip("."),
        })
        if "Time" in loc and loc["Time"]:
            SubElement(trkpt, "time").text = parse_time(loc["Time"])

    return ET.ElementTree(gpx)


def prettify(tree: ET.ElementTree) -> str:
    rough = ET.tostring(tree.getroot(), encoding="unicode")
    parsed = minidom.parseString(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + rough
    )
    return parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("UTF-8")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: json_to_gpx.py input.json output.gpx", file=sys.stderr)
        sys.exit(1)

    inpath = sys.argv[1]
    if inpath == "-":
        data = json.load(sys.stdin)
    else:
        with open(inpath, encoding="utf-8") as f:
            data = json.load(f)

    gpx_xml = prettify(build_gpx(data))

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(gpx_xml)

    print(f"Wrote {len(data.get('locations', []))} points to {sys.argv[2]}")


if __name__ == "__main__":
    main()
