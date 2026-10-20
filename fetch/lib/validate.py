"""Schema and range checks (plan 9.1 steps 5 and 6).

An adapter raises ParseError when the body has the wrong form. The checks in
this module run after the parse. A value out of range becomes null. If too
many values are bad, the whole result is not valid.
"""
from .common import DAY


class ParseError(Exception):
    """The body has the wrong form. Rule 9.4a: fetch again."""


class ValidationError(Exception):
    """The parsed data fails a check. Keep the last good data."""

    def __init__(self, message, sample=None):
        super().__init__(message)
        self.sample = sample


MAX_BAD_FRACTION = 0.5


def series(result, now, allow_future=False):
    """Check a series part. Set values out of range to null. Return the count of changed values."""
    rows, cols = result["rows"], result["cols"]
    if not isinstance(rows, dict):
        raise ValidationError("rows is not a dict")
    bad = total = 0
    limit = now + 2 * DAY
    for t in list(rows):
        if not isinstance(t, int):
            raise ValidationError("time is not an integer", sample=repr(t))
        if not allow_future and t > limit:
            raise ValidationError("time is in the future", sample=t)
        vals = rows[t]
        if len(vals) != len(cols):
            raise ValidationError("row length does not agree with the columns", sample=vals)
        for i, c in enumerate(cols):
            v = vals[i]
            if v is None:
                continue
            total += 1
            lo, hi = c.get("range", (None, None))
            if not isinstance(v, (int, float)) or (lo is not None and v < lo) or (hi is not None and v > hi):
                vals[i] = None
                bad += 1
    if total and bad / total > MAX_BAD_FRACTION:
        raise ValidationError(f"{bad} of {total} values are out of range")
    return bad


REQUIRED_EVENT = ("id", "t_start", "type")


def events(items, allow_empty=False):
    if not isinstance(items, list):
        raise ValidationError("events is not a list")
    if not items and not allow_empty:
        raise ValidationError("the event list is empty (rule g does not apply)")
    for e in items:
        for k in REQUIRED_EVENT:
            if e.get(k) in (None, ""):
                raise ValidationError(f"event field '{k}' is missing", sample=e)
        if not isinstance(e["t_start"], int):
            raise ValidationError("t_start is not an integer", sample=e)
        lat, lon = e.get("lat"), e.get("lon")
        if lat is not None and not -90 <= lat <= 90:
            raise ValidationError("lat is out of range", sample=e)
        if lon is not None and not -180 <= lon <= 360:
            raise ValidationError("lon is out of range", sample=e)
        sev = e.get("sev")
        if sev is not None and not 0 <= sev <= 5:
            raise ValidationError("sev is out of range 0 to 5", sample=e)


def grid(values, g, lo=None, hi=None):
    n = g["nlat"] * g["nlon"]
    if len(values) != n:
        raise ValidationError(f"grid has {len(values)} cells, expected {n}")
    present = [v for v in values if v is not None]
    if not present:
        raise ValidationError("grid has no values")
    out = [v for v in present if (lo is not None and v < lo) or (hi is not None and v > hi)]
    if len(out) > MAX_BAD_FRACTION * len(present):
        raise ValidationError(f"{len(out)} grid values are out of range")


def text(issue):
    if not issue.get("text") or not isinstance(issue.get("t"), int):
        raise ValidationError("text product has no text or no issue time")
