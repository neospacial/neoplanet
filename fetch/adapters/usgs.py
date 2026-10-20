"""USGS adapters: geomagnetism (plan 8.2). Earthquakes and volcanoes follow in Phase 4."""
from lib import common
from lib.http import FetchError
from lib.validate import ParseError

from .base import col, load_json, num

GEOMAG_UNITS = {"H": "nT", "Z": "nT", "D": ""}
# 1 nT is enough to see storms. D stays in the raw tier only (no summaries), to keep the budget.
GEOMAG_SCALE = {"H": 1, "Z": 1, "D": 1000}


def geomag_cols(observatories):
    out = []
    for o in observatories:
        for e in ("H", "D", "Z"):
            label = f"{o} {e}" + (" (declination, USGS variation units)" if e == "D" else "")
            c = col(f"{o}_{e}", GEOMAG_UNITS[e], GEOMAG_SCALE[e], lo=-100000, hi=100000, label=label, auto_off=True)
            if e == "D":
                c["summary"] = False
            out.append(c)
    return out


def parse_geomag(body):
    """Return {t: {element: value}} for one observatory."""
    obj = load_json(body)
    times = obj.get("times") if isinstance(obj, dict) else None
    if not times:
        raise ParseError("no 'times' list")
    out = {}
    for v in obj.get("values") or []:
        el = v.get("id") or (v.get("metadata") or {}).get("element")
        vals = v.get("values") or []
        if len(vals) != len(times):
            raise ParseError("values and times have different lengths")
        for t, x in zip(times, vals):
            x = num(x)
            if x is not None:
                out.setdefault(common.parse_iso(t), {})[el] = x
    return out


def usgs_geomag(ds, ctx):
    """Fetch each observatory (the {OBS} placeholder) and make one series with 3 columns for each."""
    obs = ds.get("observatories") or []
    now = ctx.now
    start = now - (7 * 86400 if ctx.backfill else 4 * 3600)   # window: 4 x the 1 h cadence
    rows, missing, changed = {}, [], False
    for i, o in enumerate(obs):
        url, _ = common.expand_url(ds["url"], now, ctx.env, {"OBS": o})
        if not ctx.offline:
            url += f"&starttime={common.iso(start)}&endtime={common.iso(now)}"
        try:
            resp = ctx.client.get(url, conditional=not ctx.backfill, hash_check=True)
        except FetchError as e:
            missing.append(f"{o} ({e})")
            continue
        ctx.responses.append(resp)
        if resp.unchanged:
            continue
        changed = True
        for t, vals in parse_geomag(resp.body).items():
            row = rows.setdefault(t, [None] * (3 * len(obs)))
            for k, e in enumerate(("H", "D", "Z")):
                row[3 * i + k] = vals.get(e)
    if len(missing) == len(obs):
        raise FetchError("no observatory answered: " + ", ".join(missing))
    if not changed:
        return None
    out = {"series": {"cols": geomag_cols(obs), "rows": rows, "dt": ds.get("dt") or 60, "last": False},
           "newest": max(rows) if rows else None}
    if missing:
        out["message"] = "no data from " + ", ".join(missing)
    return out


# ----------------------------------------------------------------- earthquakes (plan 8.3)

PAGER = {"green": 1, "yellow": 2, "orange": 3, "red": 4}


def quake_sev(mag, alert):
    by_mag = 0 if mag is None or mag < 5 else 1 if mag < 6 else 2 if mag < 7 else 3 if mag < 8 else 4
    return max(by_mag, PAGER.get(alert or "", 0))


def usgs_quakes(ds, body, ctx):
    obj = load_json(body)
    feats = obj.get("features") if isinstance(obj, dict) else None
    if feats is None:
        raise ParseError("no 'features' list")
    items = []
    for f in feats:
        p, g = f.get("properties") or {}, (f.get("geometry") or {}).get("coordinates") or [None, None, None]
        if p.get("type") not in (None, "earthquake") or p.get("time") is None:
            continue
        mag = num(p.get("mag"))
        items.append({"id": f["id"], "t_start": int(p["time"]) // 1000, "lat": num(g[1]), "lon": num(g[0]),
                      "type": "quake", "sev": quake_sev(mag, p.get("alert")), "mag": mag,
                      "title": p.get("title") or f"M {mag}", "src": "USGS", "url": p.get("url"),
                      "extra": {"depth_km": num(g[2]), "pager": p.get("alert"), "tsunami": p.get("tsunami") or None,
                                "sig": p.get("sig"), "mag_type": p.get("magType"), "status": p.get("status")}})
    return {"events": {"items": items, "active": True, "allow_empty": True},
            "newest": max((e["t_start"] for e in items), default=None)}


# ----------------------------------------------------------------- volcanoes (plan 8.3)

COLOR = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}


def usgs_volcano(ds, body, ctx):
    recs = load_json(body)
    if not isinstance(recs, list):
        raise ParseError("expected a JSON list")
    items = []
    for r in recs:
        t = num(r.get("sent_unixtime"))
        if t is None:
            t = common.parse_iso(r["sent_utc"])
        code = str(r.get("color_code") or "").upper()
        items.append({"id": f"{r.get('vnum')}|{r.get('notice_identifier')}", "t_start": int(t), "type": "volcano",
                      "sev": COLOR.get(code, 0), "title": f"{r.get('volcano_name')}: {code.title()} / {str(r.get('alert_level') or '').title()}",
                      "src": "USGS", "url": (r.get("notice_url") or "").replace("\\/", "/"),
                      "extra": {"volcano": r.get("volcano_name"), "vnum": r.get("vnum"), "color": code,
                                "alert": r.get("alert_level"), "observatory": r.get("obs_abbr")}})
    return {"events": {"items": items, "active": True}, "newest": max((e["t_start"] for e in items), default=None)}
