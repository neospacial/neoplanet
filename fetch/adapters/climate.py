"""Climate record adapters (plan 8.5). Each one gives a full record (class E)."""
import csv
import io
import re

from lib import common
from lib.http import FetchError
from lib.validate import ParseError

from .base import col, load_json, num, text_of

MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()


def _series(cols, rows, dt=None):
    if not rows:
        raise ParseError("no data rows")
    return {"series": {"cols": cols, "rows": rows, "dt": dt, "last": False}, "newest": max(rows)}


def ncei_cag(ds, body, ctx):
    obj = load_json(body)
    data = obj.get("data") if isinstance(obj, dict) else None
    if not isinstance(data, dict):
        raise ParseError("no 'data' object")
    rows = {}
    for k, v in data.items():
        val = v.get("anomaly", v.get("departure")) if isinstance(v, dict) else v
        if len(k) == 6 and k.isdigit():
            rows[common.epoch(int(k[:4]), int(k[4:]))] = [num(val)]
    return _series([col("anom", "degC", 100, lo=-5, hi=5, label="Anomaly vs 1901-2000")], rows)


def gistemp(ds, body, ctx):
    lines = text_of(body).splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("Year,")), None)
    if start is None:
        raise ParseError("no 'Year' header")
    rows = {}
    for r in csv.reader(lines[start + 1:]):
        if not r or not r[0].isdigit():
            continue
        for m in range(12):
            v = num(r[m + 1])
            if v is not None:
                rows[common.epoch(int(r[0]), m + 1)] = [v]
    return _series([col("anom", "degC", 100, lo=-5, hi=5, label="Anomaly vs 1951-1980")], rows)


GML_UNIT = {"co2": "ppm", "ch4": "ppb", "n2o": "ppb", "sf6": "ppt"}


def gml_csv(ds, body, ctx):
    lines = [l for l in text_of(body).splitlines() if l.strip() and not l.startswith("#")]
    if not lines:
        raise ParseError("no data lines")
    head = [h.strip() for h in lines[0].split(",")]
    if head[0].isalpha():
        lines = lines[1:]
    elif len(head) == 5:           # daily file without a header: year, month, day, decimal, value
        head = ["year", "month", "day", "decimal", "average"]
    else:
        raise ParseError("no header line")
    h = {k: i for i, k in enumerate(head)}
    gas = ds["id"].split(".")[1].split("-")[0]
    unit = GML_UNIT.get(gas, "")
    trend_name = "deseasonalized" if "deseasonalized" in h else "trend" if "trend" in h else None
    rows = {}
    for l in lines:
        r = [x.strip() for x in l.split(",")]
        try:
            t = common.epoch(int(r[h["year"]]), int(r[h["month"]]), int(r[h["day"]]) if "day" in h else 1)
        except (ValueError, KeyError, IndexError):
            continue
        vals = [num(r[h["average"]]) if "average" in h else num(r[-1])]
        if trend_name:
            vals.append(num(r[h[trend_name]]))
        rows[t] = [v if v is not None and v > 0 else None for v in vals]
    cols = [col("value", unit, 100, lo=0, hi=5000, label=gas.upper())]
    if trend_name:
        cols.append(col("trend", unit, 100, lo=0, hi=5000, label="Trend" if trend_name == "trend" else "Deseasonalized"))
    return _series(cols, rows, 86400 if "day" in h else None)


def nsidc(ds, body, ctx):
    rows = {}
    for r in csv.reader(io.StringIO(text_of(body))):
        if len(r) < 4 or not r[0].strip().isdigit():
            continue
        try:
            t = common.epoch(int(r[0]), int(r[1]), int(r[2]))
        except ValueError:
            continue
        v = num(r[3])
        rows[t] = [v if v is not None and v >= 0 else None]
    return _series([col("extent", "million km2", 1000, lo=0, hi=30, label="Extent")], rows, 86400)


SEASONS = "DJF JFM FMA MAM AMJ MJJ JJA JAS ASO SON OND NDJ".split()


def cpc_oni(ds, body, ctx):
    rows = {}
    for l in text_of(body).splitlines():
        p = l.split()
        if len(p) == 4 and p[0] in SEASONS and p[1].isdigit():
            # The value is for 3 months. The time is the center month: DJF 1950 -> January 1950.
            m = SEASONS.index(p[0]) + 1
            rows[common.epoch(int(p[1]), m)] = [num(p[2]), num(p[3])]
    return _series([col("total", "degC", 100, lo=20, hi=32, label="Nino 3.4 SST"),
                    col("anom", "degC", 100, lo=-5, hi=5, label="ONI")], rows)


_WEEK = re.compile(r"^\s*(\d\d)([A-Z]{3})(\d{4})((?:\s*-?\d+\.\d){8})")
NINO = ["nino12", "nino12_a", "nino3", "nino3_a", "nino34", "nino34_a", "nino4", "nino4_a"]


def cpc_nino_weekly(ds, body, ctx):
    rows = {}
    for l in text_of(body).splitlines():
        m = _WEEK.match(l)
        if m:
            vals = [float(x) for x in re.findall(r"-?\d+\.\d", m.group(4))]
            rows[common.epoch(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))] = vals
    cols = [col(n, "degC", 10, lo=-10, hi=35, label=n.replace("_a", " anomaly").replace("nino", "Nino ")) for n in NINO]
    return _series(cols, rows)


def cpc_daily(ds, body, ctx):
    rows = {}
    for r in csv.reader(io.StringIO(text_of(body))):
        if len(r) >= 4 and r[0].strip().isdigit():
            try:
                rows[common.epoch(int(r[0]), int(r[1]), int(r[2]))] = [num(r[3])]
            except ValueError:
                continue
    name = ds["id"].split(".")[1].upper()
    return _series([col("index", "", 1000, lo=-10, hi=10, label=name)], rows, 86400)


def ozone_watch(ds, body, ctx):
    """Ozone hole area (rule f): the file has future rows with the climatology only."""
    rows = {}
    for l in text_of(body).splitlines():
        p = l.split()
        if len(p) >= 9 and re.match(r"^\d{4}-\d\d-\d\d$", p[0]):
            v = [num(x) for x in p[1:9]]
            rows[common.parse_iso(p[0])] = [v[0], v[1], v[4], v[7]]
    cols = [col("area", "million km2", 100, lo=0, hi=40, label="Area"),
            col("clim_min", "million km2", 100, lo=0, hi=40, label="Climatology minimum"),
            col("clim_mean", "million km2", 100, lo=0, hi=40, label="Climatology mean"),
            col("clim_max", "million km2", 100, lo=0, hi=40, label="Climatology maximum")]
    out = _series(cols, rows, 86400)
    obs = [t for t, v in rows.items() if v[0] is not None]
    out["newest"] = max(obs) if obs else None
    return out


def bom_mjo(ds, body, ctx):
    """BoM RMM index. Lines: year month day RMM1 RMM2 phase amplitude ... A value of 1.E36 is missing."""
    rows = {}
    for l in text_of(body).splitlines():
        p = l.split()
        if len(p) >= 7 and p[0].isdigit() and len(p[0]) == 4:
            try:
                t = common.epoch(int(p[0]), int(p[1]), int(p[2]))
            except ValueError:
                continue
            v = [num(x) for x in p[3:7]]
            v = [None if x is None or abs(x) > 1e30 else x for x in v]
            if v[2] is not None and not 0 <= v[2] <= 8:      # phase 999 is missing
                v[2] = None
            rows[t] = v
    cols = [col("rmm1", "", 1000, lo=-10, hi=10, label="RMM1"), col("rmm2", "", 1000, lo=-10, hi=10, label="RMM2"),
            col("phase", "", 1, lo=0, hi=8, label="Phase"), col("amplitude", "", 1000, lo=0, hi=10, label="Amplitude")]
    return _series(cols, rows, 86400)


def parse_gmsl(body):
    """NOAA STAR global mean sea level CSV: decimal year, then one column for each mission (mm)."""
    rows = {}
    for l in text_of(body).splitlines():
        p = [x.strip() for x in l.split(",")]
        try:
            yr = float(p[0])
        except (ValueError, IndexError):
            continue
        vals = [num(x) for x in p[1:] if x]
        vals = [v for v in vals if v is not None]
        if vals:
            y = int(yr)
            t0, t1 = common.epoch(y), common.epoch(y + 1)
            t = int(t0 + (yr - y) * (t1 - t0))
            rows[t - t % 86400] = [vals[-1]]
    return rows


def star_gmsl(ds, ctx):
    """Global mean sea level. If STAR fails, use the area-weighted mean of the ocean.sla grid (fallback)."""
    cols = [col("gmsl", "mm", 10, lo=-500, hi=500, label="Global mean sea level")]
    url, _ = common.expand_url(ds["url"], ctx.now, ctx.env)
    try:
        resp = ctx.client.get(url, hash_check=True)
        ctx.responses.append(resp)
        if resp.unchanged:
            return None
        rows = parse_gmsl(resp.body)
        if not rows:
            raise ParseError("no data rows")
        return {"series": {"cols": cols, "rows": rows, "dt": None, "last": False}, "newest": max(rows)}
    except (FetchError, ParseError) as e:
        sla = {"id": "ocean.sla", "kind": "grid"}
        shard = ctx.store.read(sla, "r/" + common.ym(ctx.now)[:4] + ".json") or {}
        from lib.store import decode_series
        rows = {t: [v[0] * 1000 if v[0] is not None else None]
                for t, v in decode_series(shard, ["global_mean"]).items()} if shard else {}
        if not rows:
            raise FetchError(f"STAR failed ({e}) and the ocean.sla fallback has no data")
        cols[0]["label"] = "Global mean sea level anomaly (fallback: ocean.sla grid mean)"
        return {"series": {"cols": cols, "rows": rows, "dt": None, "last": False}, "newest": max(rows),
                "degraded": True, "message": f"fallback: ocean.sla grid mean (STAR: {e})"}
