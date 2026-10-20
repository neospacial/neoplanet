"""Tropical cyclones (plan 8.4): NHC/CPHC active storms and IBTrACS active tracks."""
import csv
import io

from lib import common
from lib.validate import ParseError

from .base import load_json, num, text_of


def saffir(kt):
    """Saffir-Simpson category from the maximum wind (kt). 0 = tropical storm or weaker."""
    if kt is None:
        return 0
    for cat, lim in ((5, 137), (4, 113), (3, 96), (2, 83), (1, 64)):
        if kt >= lim:
            return cat
    return 0


def nhc_storms(ds, body, ctx):
    obj = load_json(body)
    storms = obj.get("activeStorms") if isinstance(obj, dict) else None
    if storms is None:
        raise ParseError("no 'activeStorms' list")
    items = []
    for s in storms:
        kt = num(s.get("intensity"))
        items.append({"id": s.get("id") or s.get("binNumber"), "t_start": common.parse_iso(s["lastUpdate"]),
                      "lat": num(s.get("latitudeNumeric")), "lon": num(s.get("longitudeNumeric")), "type": "cyclone",
                      "sev": saffir(kt), "mag": kt,
                      "title": f"{s.get('classification') or ''} {s.get('name') or ''}".strip(), "src": "NHC",
                      "url": "https://www.nhc.noaa.gov/",
                      "extra": {"pressure": num(s.get("pressure")), "move_dir": num(s.get("movementDir")),
                                "move_kt": num(s.get("movementSpeed")), "bin": s.get("binNumber")}})
    return {"events": {"items": items, "active": True}, "newest": max((e["t_start"] for e in items), default=ctx.now)}


def ibtracs(ds, body, ctx):
    """One event for each storm (SID). The track is in extra.track: [hours from start, lat, lon, wind kt]."""
    rows = list(csv.reader(io.StringIO(text_of(body))))
    if not rows or "SID" not in rows[0]:
        raise ParseError("no IBTrACS header")
    h = {k.strip(): i for i, k in enumerate(rows[0])}
    tracks = {}
    for r in rows[1:]:
        if len(r) < len(h) // 2:
            continue
        try:
            t = common.parse_iso(r[h["ISO_TIME"]])
        except ValueError:
            continue     # the units row
        wind = num(r[h["USA_WIND"]]) if "USA_WIND" in h else None
        if wind is None:
            wind = num(r[h["WMO_WIND"]])
        tracks.setdefault(r[h["SID"]], []).append((t, num(r[h["LAT"]]), num(r[h["LON"]]), wind, r[h["NAME"]].strip(),
                                                   r[h["BASIN"]].strip()))
    items = []
    for sid, pts in tracks.items():
        pts.sort()
        t0, last = pts[0][0], pts[-1]
        winds = [p[3] for p in pts if p[3] is not None]
        vmax = max(winds) if winds else None
        lon = last[2] - 360 if last[2] is not None and last[2] > 180 else last[2]
        items.append({"id": sid, "t_start": t0, "t_end": last[0], "lat": last[1], "lon": lon, "type": "cyclone",
                      "sev": saffir(vmax), "mag": vmax, "title": f"{last[4].title()} ({last[5]})", "src": "IBTrACS",
                      "url": "https://www.ncei.noaa.gov/products/international-best-track-archive",
                      "extra": {"track": [[round((p[0] - t0) / 3600), p[1], p[2], p[3]] for p in pts]}})
    return {"events": {"items": items, "active": True, "allow_empty": True},
            "newest": max((e["t_end"] for e in items), default=None)}
