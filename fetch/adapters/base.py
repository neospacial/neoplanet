"""Helpers for adapters.

An adapter is a function parse(ds, body, ctx) -> result. The result is a dict
with one or more of these parts:

    series    {"cols": [col], "rows": {t: [values]}, "dt": int or None, "last": bool}
    events    {"items": [event], "active": bool}
    record    dict, written to latest.json
    forecast  {"issued": t, "cols": [col], "rows": {t: [values]}}  (rule 9.4f, newest issue only)
    text      {"t": issue time, "text": str}
    grid      {"t": t, "grid": spec, "values": [..], "q": {..}, "fill": value, "extra": {..}}
    newest    newest data time (Unix seconds)

A column is {"name", "unit", "q": {"type": "lin" | "log10", "scale"}, "range": (lo, hi)}.
An event is the record of plan 5.5.
"""
import json

from lib.validate import ParseError


def col(name, unit, scale=1, qtype="lin", lo=None, hi=None, label=None, auto_off=False):
    q = {"type": qtype, "scale": scale}
    if auto_off:
        q["auto_off"] = True     # store values against a per-shard offset (store.with_offset)
    c = {"name": name, "unit": unit, "q": q, "range": (lo, hi)}
    if label:
        c["label"] = label
    return c


def load_json(body):
    try:
        return json.loads(body.decode("utf-8-sig") if isinstance(body, bytes) else body)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"JSON parse failed: {e}") from None


def text_of(body):
    try:
        return body.decode("utf-8-sig") if isinstance(body, bytes) else body
    except UnicodeDecodeError:
        return body.decode("latin-1")


def num(v):
    """Convert to float. Return None for a missing or fill value."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
    else:
        s = str(v).strip()
        if s in ("", "null", "NaN", "nan", "-", "--", "***", "n/a"):
            return None
        try:
            f = float(s)
        except ValueError:
            return None
    if f != f or f in (-1e31, -9999.0, -999.9, -99999.0, -9999.9, -999.0):
        return None
    return f


def records_of(obj):
    """Return a list of dicts. Accept a list of dicts or a table with a header row."""
    if isinstance(obj, list) and obj and isinstance(obj[0], list):
        header = [str(h) for h in obj[0]]
        return [dict(zip(header, row)) for row in obj[1:]]
    if isinstance(obj, list):
        return [r for r in obj if isinstance(r, dict)]
    raise ParseError("expected a JSON list")


def series_result(cols, rows, dt=None, last=False):
    newest = max(rows) if rows else None
    return {"series": {"cols": cols, "rows": rows, "dt": dt, "last": last}, "newest": newest}


def floor(t, dt):
    return t - t % dt if dt else t
