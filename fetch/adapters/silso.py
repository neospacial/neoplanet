"""SILSO adapters (plan 8.2): daily sunspot number and the estimated daily number. CC BY-NC 4.0."""
from lib import common
from lib.validate import ParseError

from .base import col, num, text_of


def silso_csv(ds, body, ctx):
    rows = {}
    for line in text_of(body).splitlines():
        parts = [p.strip() for p in line.replace(";", ",").split(",")]
        if len(parts) < 6 or not parts[0].isdigit():
            continue
        try:
            t = common.epoch(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            continue
        ssn, std = num(parts[4]), num(parts[5])
        if ssn is not None and ssn < 0:          # -1 is a missing value
            ssn, std = None, None
        rows[t] = [ssn, std if std is not None and std >= 0 else None]
    if not rows:
        raise ParseError("no data lines")
    cols = [col("ssn", "", 1, lo=0, hi=1500, label="Sunspot number"),
            col("std", "", 10, lo=0, hi=500, label="Standard deviation")]
    return {"series": {"cols": cols, "rows": rows, "dt": 86400, "last": False}, "newest": max(rows)}
