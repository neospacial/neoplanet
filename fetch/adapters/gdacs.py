"""GDACS global disaster alerts (plan 8.3). Attribution: GDACS (EC JRC, UN OCHA)."""
from lib import common
from lib.validate import ParseError

from .base import load_json, num

LEVEL = {"green": 1, "orange": 3, "red": 4}


def gdacs(ds, body, ctx):
    obj = load_json(body)
    feats = obj.get("features") if isinstance(obj, dict) else None
    if feats is None:
        raise ParseError("no 'features' list")
    items = []
    for f in feats:
        p = f.get("properties") or {}
        g = (f.get("geometry") or {}).get("coordinates") or [None, None]
        sev = p.get("severitydata") or {}
        items.append({"id": f"{p.get('eventtype')}{p.get('eventid')}", "t_start": common.parse_iso(p["fromdate"]),
                      "t_end": common.parse_iso(p["todate"]) if p.get("todate") else None,
                      "lat": num(g[1]), "lon": num(g[0]), "type": str(p.get("eventtype") or "").lower(),
                      "sev": LEVEL.get(str(p.get("alertlevel") or "").lower(), 0), "mag": num(sev.get("severity")),
                      "title": p.get("name") or p.get("eventname") or "GDACS event", "src": "GDACS",
                      "url": (p.get("url") or {}).get("report") or "https://www.gdacs.org/",
                      "extra": {"level": p.get("alertlevel"), "country": p.get("country"),
                                "severity": sev.get("severitytext"), "episode": p.get("episodeid")}})
    return {"events": {"items": items, "active": True},
            "newest": max((e.get("t_end") or e["t_start"] for e in items), default=None)}
