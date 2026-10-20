"""NOAA SWPC adapters (plan 8.1). Source: services.swpc.noaa.gov, no key."""
import re

from lib import common, grid as gridlib
from lib.validate import ParseError

from .base import col, load_json, text_of, num, records_of, series_result, floor

LOG_FLUX = {"qtype": "log10", "scale": 1000, "lo": 1e-12, "hi": 1e9}


def _t(rec, *keys):
    for k in keys:
        v = rec.get(k)
        if v:
            try:
                return common.parse_iso(str(v))
            except ValueError:
                raise ParseError(f"bad time {v!r}") from None
    raise ParseError(f"no time field {keys}")


def _rows(recs, cols, fields, dt=None, time_keys=("time_tag",)):
    rows = {}
    for r in recs:
        t = floor(_t(r, *time_keys), dt)
        rows[t] = [num(r.get(f)) for f in fields]
    return rows


# ----------------------------------------------------------------- swpc_table

TABLE = {
    "space.kp": ([col("kp", "Kp", 100, lo=0, hi=9, label="Kp")], ["Kp"], True),
    "space.dst": ([col("dst", "nT", 1, lo=-2000, hi=500, label="Dst")], ["dst"], False),
    "space.f107": ([col("f107", "sfu", 10, lo=0, hi=1000, label="F10.7")], ["flux"], False),
}

KP_KIND = {"observed": 0, "estimated": 1, "predicted": 2}


def swpc_table(ds, body, ctx):
    recs = records_of(load_json(body))
    if not recs:
        raise ParseError("empty table")
    sid = ds["id"]
    if sid == "space.kp-forecast":
        cols = [col("kp", "Kp", 100, lo=0, hi=9, label="Kp"),
                col("kind", "code", 1, lo=0, hi=2, label="0 observed, 1 estimated, 2 predicted"),
                col("g", "G level", 1, lo=0, hi=5, label="NOAA G scale")]
        rows = {}
        for r in recs:
            scale = r.get("noaa_scale") or ""
            g = int(scale[1]) if re.match(r"^G[1-5]$", str(scale)) else 0
            rows[_t(r, "time_tag")] = [num(r.get("kp")), KP_KIND.get(r.get("observed"), 2), g]
        observed = [t for t, v in rows.items() if v[1] == 0] or list(rows)
        return {"forecast": {"issued": max(observed), "cols": cols, "rows": rows}, "newest": max(observed)}
    cols, fields, last = TABLE[sid]
    rows = _rows(recs, cols, fields, ds.get("dt"))
    return series_result(cols, rows, ds.get("dt"), last)


# ----------------------------------------------------------------- swpc_records

def _month(tag):
    y, m = str(tag).split("-")[:2]
    return common.epoch(int(y), int(m))


def _neg_null(v):
    v = num(v)
    return None if v is None or v < 0 else v


def swpc_records(ds, body, ctx):
    recs = records_of(load_json(body))
    sid = ds["id"]
    if sid == "space.kp-1m":
        cols = [col("kp", "Kp", 100, lo=0, hi=9, label="Estimated Kp")]
        return series_result(cols, _rows(recs, cols, ["estimated_kp"], 60), 60)
    if sid == "space.enlil":
        cols = [col("density", "cm^-3", 100, lo=0, hi=1000, label="Density"),
                col("speed", "km/s", 1, lo=0, hi=3000, label="Radial speed"),
                col("temperature", "K", 1000, "log10", 1, 1e9, label="Temperature"),
                col("polarity", "", 1000, lo=-1.5, hi=1.5, label="Polarity"),
                col("cloud", "", 1000, lo=-10, hi=10, label="CME cloud")]
        rows = {}
        for r in recs:
            rows[_t(r, "time_tag")] = [num(r.get("earth_particles_per_cm3")), num(r.get("v_r")),
                                       num(r.get("temperature")), num(r.get("polarity")), num(r.get("cloud"))]
        if not rows:
            raise ParseError("empty Enlil series")
        return {"forecast": {"issued": min(rows), "cols": cols, "rows": rows}, "newest": max(rows)}
    if sid == "space.flare-prob":
        if not recs:
            raise ParseError("empty list")
        newest = max(recs, key=lambda r: r.get("date") or "")
        t = _t(newest, "date")
        return {"record": {"t": t, "values": newest}, "newest": t}
    if sid == "space.solar-regions":
        return {"events": {"items": _regions(recs), "active": True},
                "newest": max((_t(r, "observed_date") for r in recs), default=None)}
    if sid == "space.cycle-observed":
        cols = [col("ssn", "", 10, lo=0, hi=1000, label="Sunspot number"),
                col("ssn_smooth", "", 10, lo=0, hi=1000, label="Smoothed sunspot number"),
                col("f107", "sfu", 10, lo=0, hi=1000, label="F10.7"),
                col("f107_smooth", "sfu", 10, lo=0, hi=1000, label="Smoothed F10.7")]
        rows = {}
        for r in recs:
            rows[_month(r["time-tag"])] = [_neg_null(r.get("ssn")), _neg_null(r.get("smoothed_ssn")),
                                           _neg_null(r.get("f10.7")), _neg_null(r.get("smoothed_f10.7"))]
        return series_result(cols, rows, None)
    if sid == "space.cycle-predicted":
        names = ["predicted_ssn", "low_ssn", "high_ssn", "predicted_f10.7", "low_f10.7", "high_f10.7"]
        cols = [col(n.replace(".", ""), "sfu" if "f10" in n else "", 10, lo=0, hi=1000) for n in names]
        rows = {_month(r["time-tag"]): [_neg_null(r.get(n)) for n in names] for r in recs}
        if not rows:
            raise ParseError("empty prediction")
        return {"forecast": {"issued": min(rows), "cols": cols, "rows": rows}, "newest": max(rows)}
    raise ParseError(f"swpc_records has no rule for {sid}")


def _regions(recs):
    """One event for each active region. The newest observation wins."""
    by = {}
    for r in recs:
        reg = r.get("region")
        if reg is None:
            continue
        if reg not in by or (r.get("observed_date") or "") >= (by[reg].get("observed_date") or ""):
            by[reg] = r
    out = []
    keep = ("location", "latitude", "longitude", "carrington_longitude", "area", "spot_class", "extent",
            "number_spots", "mag_class", "c_xray_events", "m_xray_events", "x_xray_events", "proton_events",
            "c_flare_probability", "m_flare_probability", "x_flare_probability", "proton_probability")
    for reg, r in by.items():
        t_obs = _t(r, "observed_date")
        first = r.get("first_date")
        t0 = common.parse_iso(first) if first else t_obs
        mag = str(r.get("mag_class") or "").lower()
        sev = 2 if "delta" in mag or "d" == mag[-1:] else (1 if "gamma" in mag or "g" in mag else 0)
        out.append({"id": f"AR{reg}", "t_start": t0, "t_end": t_obs, "lat": None, "lon": None,
                    "type": "region", "sev": sev, "mag": num(r.get("area")),
                    "title": f"Region {reg} {r.get('location') or ''}".strip(), "src": "SWPC",
                    "url": "https://www.swpc.noaa.gov/products/solar-region-summary",
                    "extra": {k: r.get(k) for k in keep if r.get(k) is not None}})
    return out


# ----------------------------------------------------------------- swpc_goes

GOES = {
    "space.xray": {"0.05-0.4nm": "short", "0.1-0.8nm": "long"},
    # Three channels keep the dataset inside its budget: >=10 MeV (S scale), >=50, >=100 MeV.
    "space.protons": {f">={e} MeV": f"ge{e}" for e in (10, 50, 100)},
    "space.electrons": {">=2 MeV": "ge2"},
}
GOES_LABEL = {"short": "0.05-0.4 nm", "long": "0.1-0.8 nm"}
MAG_FIELDS = ["He", "Hp", "Hn", "total"]


def goes_cols(sid):
    if sid == "space.goes-mag":
        return [col(f, "nT", 10, lo=-2000, hi=2000, label=f) for f in MAG_FIELDS]
    unit = "W/m2" if sid == "space.xray" else "pfu"
    return [col(name, unit, label=GOES_LABEL.get(name, ch), **LOG_FLUX) for ch, name in GOES[sid].items()]


def swpc_goes(ds, body, ctx):
    recs = records_of(load_json(body))
    sid, dt = ds["id"], ds.get("dt") or 60
    cols = goes_cols(sid)
    if sid == "space.goes-mag":
        return series_result(cols, _rows(recs, cols, MAG_FIELDS, dt), dt)
    index = {ch: i for i, ch in enumerate(GOES[sid])}
    rows = {}
    for r in recs:
        i = index.get(r.get("energy"))
        if i is None:
            continue
        t = floor(_t(r, "time_tag"), dt)
        row = rows.setdefault(t, [None] * len(cols))
        row[i] = num(r.get(ds.get("value") or "flux"))
    if not rows:
        raise ParseError("no known energy channel")
    return series_result(cols, rows, dt)


# ----------------------------------------------------------------- swpc_rtsw

RTSW_COLS = {
    "proton_speed": col("speed", "km/s", 1, lo=0, hi=3000, label="Speed"),
    "proton_density": col("density", "cm^-3", 10, lo=0, hi=500, label="Density"),
    "proton_temperature": col("temperature", "K", 1000, "log10", 1, 1e9, label="Temperature"),
    "bt": col("bt", "nT", 10, lo=0, hi=500, label="Bt"),
    "bx_gsm": col("bx", "nT", 10, lo=-500, hi=500, label="Bx GSM"),
    "by_gsm": col("by", "nT", 10, lo=-500, hi=500, label="By GSM"),
    "bz_gsm": col("bz", "nT", 10, lo=-500, hi=500, label="Bz GSM"),
}
SPACECRAFT = {"DSCOVR": 1, "ACE": 2, "SOLAR1": 3, "IMAP": 4}


def swpc_rtsw(ds, body, ctx):
    recs = records_of(load_json(body))
    if "c" in ds.get("rules", []):
        recs = [r for r in recs if r.get("active") is True]   # rule 9.4c
    if not recs:
        raise ParseError("no active spacecraft rows")
    fields = ds["columns"]
    cols = [RTSW_COLS[f] for f in fields] + [col("src", "code", 1, lo=0, hi=9,
                                                 label="Spacecraft: " + ", ".join(f"{v} {k}" for k, v in SPACECRAFT.items()))]
    dt = ds.get("dt") or 60
    rows = {}
    for r in sorted(recs, key=lambda r: r.get("time_tag") or ""):
        t = floor(_t(r, "time_tag"), dt)
        rows[t] = [num(r.get(f)) for f in fields] + [SPACECRAFT.get(str(r.get("source")).upper(), 9)]
    return series_result(cols, rows, dt)


# ----------------------------------------------------------------- swpc_hemi_power

_HP = re.compile(r"^(\d{4}-\d\d-\d\d)_(\d\d:\d\d)\s+(\S+)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")


def swpc_hemi_power(ds, body, ctx):
    rows = {}
    for line in text_of(body).splitlines():
        m = _HP.match(line.strip())
        if m:
            t = common.parse_iso(f"{m.group(1)}T{m.group(2)}:00")
            rows[floor(t, ds.get("dt") or 300)] = [num(m.group(4)), num(m.group(5))]
    if not rows:
        raise ParseError("no data lines")
    cols = [col("north", "GW", 1, lo=0, hi=2000, label="North"), col("south", "GW", 1, lo=0, hi=2000, label="South")]
    return series_result(cols, rows, ds.get("dt") or 300)


# ----------------------------------------------------------------- swpc_text

_ISSUED = re.compile(r"^:Issued:\s*(\d{4}) (\w{3}) (\d{1,2}) (\d{2})(\d{2}) UTC", re.M)
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def issued_time(text):
    m = _ISSUED.search(text)
    if not m:
        raise ParseError("no ':Issued:' line")
    y, mon, d, hh, mm = m.groups()
    if mon not in MONTHS:
        raise ParseError(f"bad month {mon}")
    return common.epoch(int(y), MONTHS[mon], int(d), int(hh), int(mm))


def swpc_text(ds, body, ctx):
    text = text_of(body).replace("\r\n", "\n").strip()
    t = issued_time(text)
    return {"text": {"t": t, "text": text}, "newest": t}


# ----------------------------------------------------------------- swpc_45day

def swpc_45day(ds, body, ctx):
    obj = load_json(body)
    data = obj.get("data") if isinstance(obj, dict) else None
    if not data:
        raise ParseError("no data list")
    cols = [col("ap", "nT", 1, lo=0, hi=400, label="Ap"), col("f107", "sfu", 1, lo=0, hi=1000, label="F10.7")]
    rows = {}
    for r in data:
        t = _t(r, "time")
        row = rows.setdefault(t, [None, None])
        if r.get("metric") == "ap":
            row[0] = num(r.get("value"))
        elif r.get("metric") == "f107":
            row[1] = num(r.get("value"))
    issued = common.parse_iso(obj["issued"]) if obj.get("issued") else min(rows)
    return {"forecast": {"issued": issued, "cols": cols, "rows": rows}, "newest": issued}


# ----------------------------------------------------------------- swpc_scales

def swpc_scales(ds, body, ctx):
    obj = load_json(body)
    if not isinstance(obj, dict) or "0" not in obj:
        raise ParseError("no current scales")

    def lvl(v):
        n = num(v)
        return int(n) if n is not None else None

    def day(k):
        e = obj.get(k) or {}
        r, s, g = e.get("R") or {}, e.get("S") or {}, e.get("G") or {}
        return {"date": e.get("DateStamp"), "time": e.get("TimeStamp"),
                "R": lvl(r.get("Scale")), "S": lvl(s.get("Scale")), "G": lvl(g.get("Scale")),
                "R_minor_prob": lvl(r.get("MinorProb")), "R_major_prob": lvl(r.get("MajorProb")),
                "S_prob": lvl(s.get("Prob")), "G_text": g.get("Text")}

    now = day("0")
    t = common.parse_iso(f"{now['date']}T{now['time']}")
    record = {"t": t, "now": now, "max24": day("-1"),
              "forecast": [day(k) for k in ("1", "2", "3") if k in obj]}
    cols = [col("r", "R level", 1, lo=0, hi=5), col("s", "S level", 1, lo=0, hi=5), col("g", "G level", 1, lo=0, hi=5)]
    rows = {t: [now["R"], now["S"], now["G"]]}
    out = series_result(cols, rows, None)
    out["record"] = record
    return out


# ----------------------------------------------------------------- swpc_alerts

_CODE = re.compile(r"Space Weather Message Code:\s*(\w+)")
_SERIAL = re.compile(r"Serial Number:\s*(\d+)")
_HEAD = re.compile(r"^(ALERT|WARNING|WATCH|SUMMARY|EXTENDED WARNING|CANCEL \w+|CONTINUED ALERT):\s*(.+)$", re.M)
_SCALE = re.compile(r"\b([GSR])([1-5])\b")
_KIND = {"ALT": "alert", "WAR": "warning", "WAT": "watch", "SUM": "summary", "EXT": "warning", "CAN": "cancel"}


def swpc_alerts(ds, body, ctx):
    recs = records_of(load_json(body))
    items = []
    for r in recs:
        msg = (r.get("message") or "").replace("\r\n", "\n")
        code_m, serial_m = _CODE.search(msg), _SERIAL.search(msg)
        code = code_m.group(1) if code_m else (r.get("product_id") or "MSG")
        serial = serial_m.group(1) if serial_m else ""
        t = common.parse_iso(str(r.get("issue_datetime"))[:19])
        head = _HEAD.search(msg)
        title = f"{head.group(1).title()}: {head.group(2).strip()}" if head else code
        levels = [int(n) for _, n in _SCALE.findall(msg)]
        items.append({"id": f"{code}-{serial or t}", "t_start": t, "t_end": None, "lat": None, "lon": None,
                      "type": _KIND.get(code[:3], "other"), "sev": max(levels) if levels else 0,
                      "mag": None, "title": title[:160], "src": "SWPC",
                      "url": "https://www.swpc.noaa.gov/products/alerts-watches-and-warnings",
                      "extra": {"code": code, "serial": serial, "text": msg.strip()[:900]}})
    return {"events": {"items": items, "active": True},
            "newest": max((e["t_start"] for e in items), default=None)}


# ----------------------------------------------------------------- swpc_flares

def flare_r(flux):
    """NOAA R level from the peak 0.1-0.8 nm flux."""
    if flux is None:
        return 0
    for lvl, lim in ((5, 2e-3), (4, 1e-3), (3, 1e-4), (2, 5e-5), (1, 1e-5)):
        if flux >= lim:
            return lvl
    return 0


def swpc_flares(ds, body, ctx):
    recs = records_of(load_json(body))
    items = []
    for r in recs:
        t0 = _t(r, "begin_time", "time_tag")
        flux = num(r.get("max_xrlong"))
        end = r.get("end_time")
        items.append({"id": f"{r.get('satellite', '')}-{r.get('begin_time') or r.get('time_tag')}",
                      "t_start": t0, "t_end": common.parse_iso(end) if end and end != "Unk" else None,
                      "lat": None, "lon": None, "type": "flare", "sev": flare_r(flux), "mag": flux,
                      "title": f"{r.get('max_class') or '?'} flare", "src": "GOES",
                      "url": "https://www.swpc.noaa.gov/products/goes-x-ray-flux",
                      "extra": {"max_time": r.get("max_time"), "max_class": r.get("max_class"),
                                "begin_class": r.get("begin_class"), "end_class": r.get("end_class")}})
    return {"events": {"items": items, "active": True},
            "newest": max((e["t_start"] for e in items), default=None)}


# ----------------------------------------------------------------- swpc_ovation

AURORA_GRID = gridlib.spec(2, west=0.0)


def swpc_ovation(ds, body, ctx):
    obj = load_json(body)
    coords = obj.get("coordinates") if isinstance(obj, dict) else None
    if not coords or len(coords) < 60000:
        raise ParseError("aurora grid is short (truncated body?)")
    t = common.parse_iso(obj["Observation Time"])
    deg = (ds.get("grid") or {}).get("deg", 2)
    g = gridlib.spec(deg, west=0.0)
    values = gridlib.regrid_max(((c[1], c[0], c[2]) for c in coords), g)
    values = [0 if v is None else v for v in values]
    return {"grid": {"t": t, "grid": g, "values": values, "q": {"type": "lin", "scale": 1}, "fill": 0,
                     "range": (0, 100), "unit": "%",
                     "extra": {"forecast_time": obj.get("Forecast Time")}},
            "newest": t}
