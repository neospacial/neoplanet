"""ERDDAP griddap CSV (plan 8.5): SST anomaly, sea level anomaly, coral bleaching alert.

The URLs in sources.json already use a stride (1 degree, or 2 degrees for the
coral alert). The HTTP client follows redirects (the coral alert moves to
pae-paha.pacioos.hawaii.edu). Derived scalars (plan 7.2): the area-weighted
global mean, and the Nino 3.4 box mean (5N-5S, 170W-120W).
"""
import csv
import io

from lib import common, grid as gridlib
from lib.validate import ParseError

from .base import col, num, text_of

SPEC = {   # dataset -> (unit, quantize scale, valid range, fill)
    "ocean.sst-anom": ("degC", 100, (-15, 15)),
    "ocean.sla": ("m", 1000, (-3, 3)),
    "ocean.coral-alert": ("level", 1, (0, 4)),
}
NINO34 = (-5, 5, -170, -120)


def erddap_grid(ds, body, ctx):
    rows = list(csv.reader(io.StringIO(text_of(body))))
    if len(rows) < 3 or "latitude" not in rows[0]:
        raise ParseError("no ERDDAP CSV header")
    h = {k: i for i, k in enumerate(rows[0])}
    var = rows[0][-1]
    g = gridlib.spec((ds.get("grid") or {}).get("deg", 1))
    pts, t = [], None
    for r in rows[2:]:            # row 1 has the units
        if len(r) != len(h):
            continue
        if t is None:
            t = common.parse_iso(r[h["time"]])
        lon = float(r[h["longitude"]])
        pts.append((float(r[h["latitude"]]), lon - 360 if lon >= 180 else lon, num(r[-1])))
    if not pts:
        raise ParseError("no grid rows")
    values = gridlib.from_points(pts, g)
    unit, scale, rng = SPEC.get(ds["id"], ("", 100, (None, None)))
    out = {"grid": {"t": t, "grid": g, "values": values, "q": {"type": "lin", "scale": scale}, "fill": None,
                    "range": rng, "unit": unit, "extra": {"variable": var}},
           "newest": t}
    derived = ds.get("derived") or []
    if derived:
        cols, vals = [], []
        if "global_mean" in derived:
            cols.append(col("global_mean", unit, 1000 if unit == "degC" else 10000, lo=rng[0], hi=rng[1],
                            label="Global mean (area-weighted)"))
            vals.append(gridlib.area_mean(values, g))
        if "nino34_mean" in derived:
            cols.append(col("nino34_mean", unit, 1000, lo=rng[0], hi=rng[1], label="Nino 3.4 box mean"))
            vals.append(gridlib.area_mean(values, g, NINO34))
        out["series"] = {"cols": cols, "rows": {common.day_start(t): vals}, "dt": 86400, "last": False}
    return out
