"""NASA FIRMS VIIRS active fires (plan 8.4): 1 degree cell counts. Points are not stored.

Without FIRMS_MAP_KEY the run uses the no-key 24-hour file in 'url' (status
'ok': no data is lost). With the key it uses 'alt_url' (the area API).
"""
import csv
import io

from lib import common, grid as gridlib
from lib.validate import ParseError

from .base import col, num, text_of


def firms(ds, body, ctx):
    rows = csv.DictReader(io.StringIO(text_of(body)))
    if not rows.fieldnames or "latitude" not in rows.fieldnames:
        raise ParseError("no latitude column")
    pts, newest = [], 0
    for r in rows:
        lat, lon = num(r.get("latitude")), num(r.get("longitude"))
        if lat is None or lon is None:
            continue
        pts.append((lat, lon))
        d, hm = r.get("acq_date"), (r.get("acq_time") or "0").zfill(4)
        if d:
            newest = max(newest, common.parse_iso(f"{d}T{hm[:2]}:{hm[2:]}:00"))
    if not pts:
        raise ParseError("no fire points")
    g = gridlib.spec((ds.get("grid") or {}).get("deg", 1))
    counts = gridlib.count_cells(pts, g)
    day = common.day_start(newest or ctx.now)
    return {"grid": {"t": day, "grid": g, "values": counts, "q": {"type": "lin", "scale": 1}, "fill": 0,
                     "range": (0, 1e6), "unit": "fires", "extra": {"points": len(pts), "newest": newest}},
            "series": {"cols": [col("count", "fires", 1, lo=0, hi=1e7, label="Fire detections, 24 h")],
                       "rows": {day: [len(pts)]}, "dt": 86400, "last": False},
            "newest": newest or day}
