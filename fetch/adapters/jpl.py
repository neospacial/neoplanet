"""NASA JPL SSD/CNEOS adapters (plan 8.2): close approaches, fireballs, Sentry."""
import datetime as dt
import math

from lib import common
from lib.validate import ParseError

from .base import load_json, num

AU_LD = 149597870.7 / 384400.0      # lunar distances in one au
CNEOS = "https://cneos.jpl.nasa.gov/"


def _table(obj):
    if not isinstance(obj, dict) or "fields" not in obj:
        raise ParseError("no 'fields' in the JPL answer")
    fields = obj["fields"]
    return [dict(zip(fields, row)) for row in obj.get("data") or []]


def diameter_from_h(h, albedo=0.14):
    """Estimated diameter (m) from the absolute magnitude H."""
    if h is None:
        return None
    return 1329.0 / math.sqrt(albedo) * 10 ** (-h / 5) * 1000


def jpl_cad(ds, body, ctx):
    rows = _table(load_json(body))
    items = []
    for r in rows:
        try:
            t = int(dt.datetime.strptime(r["cd"], "%Y-%b-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
        except (KeyError, ValueError):
            raise ParseError(f"bad close-approach time {r.get('cd')!r}") from None
        dist = num(r.get("dist"))
        ld = dist * AU_LD if dist is not None else None
        h = num(r.get("h"))
        diam = num(r.get("diameter"))
        size = diam * 1000 if diam else diameter_from_h(h)
        sev = (2 if ld is not None and ld < 1 else 1 if ld is not None and ld < 5 else 0) + (1 if size and size >= 140 else 0)
        items.append({"id": f"{r['des']}|{r['cd']}", "t_start": t, "t_end": None, "lat": None, "lon": None,
                      "type": "neo", "sev": min(sev, 5), "mag": round(ld, 3) if ld is not None else None,
                      "title": f"{r['des']} at {ld:.1f} LD" if ld is not None else r["des"], "src": "JPL CNEOS",
                      "url": CNEOS + "ca.html",
                      "extra": {"des": r["des"], "dist_au": dist, "v_rel": num(r.get("v_rel")), "h": h,
                                "size_m": round(size) if size else None, "size_est": not diam,
                                "t_sigma": r.get("t_sigma_f")}})
    return {"events": {"items": items, "active": True, "allow_empty": True},
            "newest": common.day_start(ctx.now)}


def jpl_fireball(ds, body, ctx):
    rows = _table(load_json(body))
    items = []
    for r in rows:
        t = common.parse_iso(r["date"])
        lat, lon = num(r.get("lat")), num(r.get("lon"))
        if lat is not None and r.get("lat-dir") == "S":
            lat = -lat
        if lon is not None and r.get("lon-dir") == "W":
            lon = -lon
        kt = num(r.get("impact-e"))
        items.append({"id": r["date"], "t_start": t, "t_end": None, "lat": lat, "lon": lon, "type": "fireball",
                      "sev": 2 if kt and kt >= 1 else 1 if kt and kt >= 0.1 else 0, "mag": kt,
                      "title": f"Fireball {kt:g} kt" if kt is not None else "Fireball", "src": "JPL CNEOS",
                      "url": CNEOS + "fireballs/",
                      "extra": {"energy_e10j": num(r.get("energy")), "alt_km": num(r.get("alt")),
                                "vel_kms": num(r.get("vel"))}})
    if not items:
        raise ParseError("empty fireball list")
    return {"events": {"items": items, "active": False}, "newest": max(e["t_start"] for e in items)}


SENTRY_KEEP = ("des", "fullname", "ps_cum", "ps_max", "ts_max", "ip", "n_imp", "range", "diameter", "h", "v_inf",
               "last_obs")


def jpl_sentry(ds, body, ctx):
    obj = load_json(body)
    data = obj.get("data") if isinstance(obj, dict) else None
    if not data:
        raise ParseError("empty Sentry list")
    out = []
    for r in data:
        rec = {}
        for k in SENTRY_KEEP:
            v = r.get(k)
            if k not in ("des", "fullname", "range", "last_obs"):
                v = num(v)
            if v is not None:
                rec[k] = v
        out.append(rec)
    out.sort(key=lambda r: -(r.get("ps_cum") if r.get("ps_cum") is not None else -99))
    return {"record": {"t": common.day_start(ctx.now), "count": len(out), "objects": out},
            "newest": common.day_start(ctx.now)}
