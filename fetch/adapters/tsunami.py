"""NOAA/NWS Tsunami Warning Center Atom feeds (plan 8.3). An empty feed is valid (rule g)."""
import re
import xml.etree.ElementTree as ET

from lib import common
from lib.validate import ParseError

from .base import num

NS = {"a": "http://www.w3.org/2005/Atom", "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#"}
CATEGORY = {"information": 0, "advisory": 2, "watch": 3, "warning": 4, "threat": 4, "cancellation": 0}


def tsunami_atom(ds, body, ctx):
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        raise ParseError(f"XML parse failed: {e}") from None
    items = []
    for en in root.findall("a:entry", NS):
        summary = " ".join(en.find("a:summary", NS).itertext()) if en.find("a:summary", NS) is not None else ""
        cat = re.search(r"Category:\s*([A-Za-z]+)", summary)
        cat = cat.group(1).strip() if cat else "Message"
        mag = re.search(r"Preliminary Magnitude:\s*([\d.]+)", summary)
        link = next((l.get("href") for l in en.findall("a:link", NS) if l.get("rel") == "alternate"), None)
        title = (en.findtext("a:title", "", NS) or "").strip()
        items.append({"id": (en.findtext("a:id", "", NS) or title).strip(),
                      "t_start": common.parse_iso(en.findtext("a:updated", "", NS)),
                      "lat": num(en.findtext("geo:lat", None, NS)), "lon": num(en.findtext("geo:long", None, NS)),
                      "type": "tsunami", "sev": CATEGORY.get(cat.lower(), 1), "mag": num(mag.group(1)) if mag else None,
                      "title": f"{cat}: {title}", "src": ds["title"].split()[-1], "url": link or "https://www.tsunami.gov/",
                      "extra": {"category": cat}})
    return {"events": {"items": items, "active": True}, "newest": max((e["t_start"] for e in items), default=None)}
