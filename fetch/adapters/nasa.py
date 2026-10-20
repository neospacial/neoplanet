"""NASA adapters: DONKI (plan 8.2) and EONET (plan 8.3)."""
import re

from lib import common
from lib.validate import ParseError

from .base import load_json, num
from .swpc import flare_r

DONKI_URL = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/"
CME_TYPE = {"S": 0, "C": 1, "O": 2, "R": 3, "ER": 4}


def _t(v):
    if not v:
        return None
    try:
        return common.parse_iso(str(v))
    except ValueError:
        raise ParseError(f"bad time {v!r}") from None


def flare_flux(cls):
    """Peak flux from a class text such as 'M1.2'."""
    m = re.match(r"^([ABCMX])(\d+(?:\.\d+)?)", str(cls or "").strip().upper())
    if not m:
        return None
    return float(m.group(2)) * 10 ** ("ABCMX".index(m.group(1)) - 8)


def _cme(r):
    analyses = r.get("cmeAnalyses") or []
    best = next((a for a in analyses if a.get("isMostAccurate")), analyses[-1] if analyses else {})
    speed = num(best.get("speed"))
    typ = best.get("type")
    return {"id": r["activityID"], "t_start": _t(r.get("startTime")), "t_end": None, "lat": None, "lon": None,
            "type": "cme", "sev": CME_TYPE.get(typ, 0), "mag": speed,
            "title": f"CME {int(speed)} km/s" + (f" ({typ}-type)" if typ else "") if speed else "CME",
            "src": "DONKI", "url": r.get("link") or DONKI_URL,
            "extra": {"source_location": r.get("sourceLocation"), "region": r.get("activeRegionNum"),
                      "half_angle": num(best.get("halfAngle")), "lat": num(best.get("latitude")),
                      "lon": num(best.get("longitude")), "note": (r.get("note") or "")[:300]}}


def _flr(r):
    flux = flare_flux(r.get("classType"))
    return {"id": r["flrID"], "t_start": _t(r.get("beginTime")), "t_end": _t(r.get("endTime")),
            "lat": None, "lon": None, "type": "flare", "sev": flare_r(flux), "mag": flux,
            "title": f"{r.get('classType') or '?'} flare", "src": "DONKI", "url": r.get("link") or DONKI_URL,
            "extra": {"peak": r.get("peakTime"), "source_location": r.get("sourceLocation"),
                      "region": r.get("activeRegionNum")}}


def _gst(r):
    kps = [num(k.get("kpIndex")) for k in r.get("allKpIndex") or []]
    kp = max([k for k in kps if k is not None], default=None)
    g = 0 if kp is None else (5 if kp >= 9 else 4 if kp >= 8 else 3 if kp >= 7 else 2 if kp >= 6 else 1 if kp >= 5 else 0)
    return {"id": r["gstID"], "t_start": _t(r.get("startTime")), "t_end": None, "lat": None, "lon": None,
            "type": "storm", "sev": g, "mag": kp, "title": f"Geomagnetic storm, Kp {kp:g} (G{g})" if kp else "Geomagnetic storm",
            "src": "DONKI", "url": r.get("link") or DONKI_URL, "extra": {}}


def _note(r):
    body = (r.get("messageBody") or "").replace("\r\n", "\n")
    m = re.search(r"## Summary:\s*\n+(.+)", body)
    title = (m.group(1) if m else r.get("messageType") or "Notification").strip()
    levels = [int(n) for n in re.findall(r"\b[GSR]([1-5])\b", body)]
    return {"id": r["messageID"], "t_start": _t(r.get("messageIssueTime")), "t_end": None, "lat": None, "lon": None,
            "type": str(r.get("messageType") or "note").lower(), "sev": max(levels, default=0), "mag": None,
            "title": title[:160], "src": "DONKI", "url": r.get("messageURL") or DONKI_URL, "extra": {"text": body[:900]}}


KINDS = {"space.donki-cme": _cme, "space.donki-flr": _flr, "space.donki-gst": _gst,
         "space.donki-notifications": _note}


def nasa_donki(ds, body, ctx):
    """DONKI sends a JSON list. An empty body or an empty list is valid: no events in the window."""
    text = body.strip() if isinstance(body, bytes) else str(body).strip()
    recs = [] if not text else load_json(body)
    if not isinstance(recs, list):
        raise ParseError("DONKI did not send a list")
    try:
        items = [KINDS[ds["id"]](r) for r in recs if isinstance(r, dict)]
    except KeyError as e:
        raise ParseError(f"DONKI field {e} is missing") from None
    items = [e for e in items if e["t_start"] is not None]
    return {"events": {"items": items, "active": True, "allow_empty": True},
            "newest": max((e["t_start"] for e in items), default=None)}


# ----------------------------------------------------------------- EONET (plan 8.3)

def _point(geom):
    c = geom.get("coordinates")
    if geom.get("type") == "Point":
        return c[1], c[0]
    ring = c[0] if geom.get("type") == "Polygon" else c
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return sum(ys) / len(ys), sum(xs) / len(xs)


def nasa_eonet(ds, body, ctx):
    obj = load_json(body)
    evs = obj.get("events") if isinstance(obj, dict) else None
    if evs is None:
        raise ParseError("no 'events' list")
    items = []
    for e in evs:
        geo = sorted(e.get("geometry") or [], key=lambda g: g.get("date") or "")
        if not geo:
            continue
        lat, lon = _point(geo[-1])
        cat = (e.get("categories") or [{}])[0]
        mv = num(geo[-1].get("magnitudeValue"))
        src = (e.get("sources") or [{}])[0]
        items.append({"id": e["id"], "t_start": _t(geo[0]["date"]), "t_end": _t(geo[-1]["date"]),
                      "lat": lat, "lon": lon, "type": cat.get("id") or "event",
                      "sev": 1 if cat.get("id") == "severeStorms" else 0, "mag": mv,
                      "title": e.get("title") or "EONET event", "src": "EONET", "url": src.get("url") or e.get("link"),
                      "extra": {"unit": geo[-1].get("magnitudeUnit"), "points": len(geo), "category": cat.get("title")}})
    return {"events": {"items": items, "active": True, "allow_empty": True},
            "newest": max((e["t_end"] for e in items), default=None)}
