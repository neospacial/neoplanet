"""Data store: quantize, merge, never-shrink check, prune, atomic write (plan 5).

Layout (plan 5.1):

    data/<domain>/<name>/    series, record, forecast, text
    data/events/<id>/        events
    data/grids/<id>/         grids

Series shards (plan 5.2) are regular (t0, dt, n) or irregular (t0 and "t"
deltas). The span of a shard is one day, month, year, or "all".
"""
import math
import os

from . import common
from .common import DAY

SCHEMA = 1


class ShrinkError(Exception):
    """A new shard does not contain all old timestamps (plan 5.6 never shrink)."""


# ----------------------------------------------------------------- quantize

def quantize(value, q):
    """Convert a float to a stored integer. Return None for a missing value."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    scale = q.get("scale", 1)
    if q.get("type") == "log10":
        if v <= 0:
            return None
        return int(round(math.log10(v) * scale))
    return int(round((v - q.get("off", 0)) * scale))


def dequantize(value, q):
    if value is None:
        return None
    scale = q.get("scale", 1)
    if q.get("type") == "log10":
        return 10 ** (value / scale)
    return value / scale + q.get("off", 0)


# ----------------------------------------------------------------- spans

def span_key(t, span):
    if span == "day":
        return common.ymd(t)
    if span == "month":
        return common.ym(t)
    if span == "year":
        return str(common.utc(t).year)
    return "all"


def span_bounds(key, span):
    """Return (start, end) Unix seconds for a shard key. 'all' has no bounds."""
    if span == "day":
        y, m, d = (int(x) for x in key.split("-"))
        s = common.epoch(y, m, d)
        return s, s + DAY
    if span == "month":
        y, m = (int(x) for x in key.split("-"))
        s = common.epoch(y, m)
        return s, common.next_month(s)
    if span == "year":
        y = int(key)
        return common.epoch(y), common.epoch(y + 1)
    return None, None


def raw_span(ds, dt=None):
    """Choose the raw shard span from the dataset class and dt (the series dt wins)."""
    ret = ds.get("retention") or {}
    if ds.get("class") == "E" or "record" in ret:
        return "all"
    dt = dt or ds.get("dt") or 0
    if dt and dt < 3600:
        return "day"
    if dt and dt < DAY:
        return "month"
    return "year"


SUMMARY_TIERS = {"m5": (300, "month"), "h1": (3600, "month"), "d1": (DAY, "all")}


# ----------------------------------------------------------------- shard codec

def encode_series(sid, rows, cols, dt=None, start=None, end=None):
    """Make a shard dict from rows {t: [values]}.

    Regular shards need dt, start, and end. Values go to slot (t - start) // dt.
    """
    names = [c["name"] for c in cols]
    qs = {c["name"]: c.get("q", {"type": "lin", "scale": 1}) for c in cols}
    for j, c in enumerate(names):
        if qs[c].get("auto_off"):
            qs[c] = with_offset(qs[c], [v[j] for v in rows.values()])
    if dt and start is not None and end is not None:
        n = (end - start) // dt
        out = {c: [None] * n for c in names}
        first, last = n, -1
        for t, vals in rows.items():
            i = (t - start) // dt
            if 0 <= i < n:
                for c, v in zip(names, vals):
                    qv = quantize(v, qs[c])
                    if qv is not None:
                        out[c][i] = qv
                        first, last = min(first, i), max(last, i)
        # Trim the empty slots at both ends. The page reads t0 and n.
        if last < 0:
            first, last = 0, -1
        out = {c: v[first:last + 1] for c, v in out.items()}
        return {"v": SCHEMA, "id": sid, "t0": start + first * dt, "dt": dt, "n": last + 1 - first,
                "cols": out, "q": qs}
    ts = sorted(rows)
    deltas, prev = [], ts[0] if ts else 0
    for t in ts:
        deltas.append(t - prev)
        prev = t
    out = {c: [quantize(rows[t][j], qs[c]) for t in ts] for j, c in enumerate(names)}
    return {"v": SCHEMA, "id": sid, "t0": ts[0] if ts else 0, "t": deltas, "n": len(ts),
            "cols": out, "q": qs}


def with_offset(q, values):
    """Return a copy of q with 'off' = the median of the values, rounded to 100.

    A large baseline (example: a ground magnetometer H of 20,000 nT) then
    costs few digits. The offset is fixed for one shard.
    """
    vals = sorted(v for v in values if v is not None)
    out = {k: v for k, v in q.items() if k != "auto_off"}
    out["off"] = int(round(vals[len(vals) // 2] / 100.0)) * 100 if vals else 0
    return out


def shard_times(shard):
    if "t" in shard:
        out, t = [], shard["t0"]
        for d in shard["t"]:
            t += d
            out.append(t)
        return out
    return [shard["t0"] + i * shard["dt"] for i in range(shard["n"])]


def decode_series(shard, names=None):
    """Return rows {t: [values]} with dequantized floats. Skip all-null rows."""
    names = names or list(shard["cols"])
    times = shard_times(shard)
    rows = {}
    for i, t in enumerate(times):
        vals = []
        for c in names:
            col = shard["cols"].get(c)
            v = col[i] if col is not None and i < len(col) else None
            vals.append(dequantize(v, shard["q"].get(c, {})) if v is not None else None)
        if any(v is not None for v in vals):
            rows[t] = vals
    return rows


def present_times(shard):
    """Return the set of times with at least one non-null value."""
    times = shard_times(shard)
    out = set()
    for i, t in enumerate(times):
        for col in shard["cols"].values():
            if i < len(col) and col[i] is not None:
                out.add(t)
                break
    return out


def check_never_shrink(old, new, window_start=None):
    """Raise ShrinkError if new lacks a time of old that is inside the window."""
    if not old:
        return
    keep = present_times(old)
    if window_start is not None:
        keep = {t for t in keep if t >= window_start}
    missing = keep - present_times(new)
    if missing:
        raise ShrinkError(f"{len(missing)} old timestamps are missing in the new shard")


# ----------------------------------------------------------------- sparse grid codec

def encode_grid(values, q, fill=None):
    """Sparse run-length encode a flat grid (plan 5.4).

    Output: [skip, count, v1..vcount, skip, count, ...]. 'skip' is a run of
    cells equal to fill (after quantize). The values are quantized integers.
    """
    qv = [quantize(v, q) for v in values]
    fq = quantize(fill, q) if fill is not None else None
    out, i, n = [], 0, len(qv)
    while i < n:
        j = i
        while j < n and qv[j] == fq:
            j += 1
        k = j
        while k < n and qv[k] != fq:
            k += 1
        if k == j:            # only fill cells to the end
            break
        out.append(j - i)
        out.append(k - j)
        out.extend(qv[j:k])
        i = k
    return out


def decode_grid(data, q, n, fill=None):
    out = [fill] * n
    i = p = 0
    while p < len(data):
        i += data[p]
        count = data[p + 1]
        p += 2
        for k in range(count):
            out[i + k] = dequantize(data[p + k], q)
        i += count
        p += count
    return out


# ----------------------------------------------------------------- store

class Store:
    def __init__(self, root, clock, env=None):
        self.root = root
        self.clock = clock
        self.env = env
        self.changed = set()   # dataset IDs with a changed file in this run

    # paths
    def dir_for(self, ds):
        kind = ds.get("kind")
        if kind == "events":
            return os.path.join(self.root, "events", ds["id"])
        if kind == "grid":
            return os.path.join(self.root, "grids", ds["id"])
        domain, _, name = ds["id"].partition(".")
        return os.path.join(self.root, domain, name or domain)

    def rel_dir(self, ds):
        return os.path.relpath(self.dir_for(ds), self.root).replace(os.sep, "/")

    def write(self, ds, rel, obj):
        path = os.path.join(self.dir_for(ds), rel)
        if common.write_json(path, obj, self.env):
            self.changed.add(ds["id"])
            return True
        return False

    def read(self, ds, rel, default=None):
        return common.read_json(os.path.join(self.dir_for(ds), rel), default)

    def remove(self, ds, rel):
        try:
            os.unlink(os.path.join(self.dir_for(ds), rel))
            self.changed.add(ds["id"])
            return True
        except OSError:
            return False

    def list(self, ds, sub=""):
        d = os.path.join(self.dir_for(ds), sub)
        try:
            return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json") and not f.startswith("."))
        except OSError:
            return []

    # series
    def merge_series(self, ds, tier, rows, cols, dt, span, window_start=None):
        """Merge rows into the shards of one tier. Return (t_min, t_max) of the input.

        New values replace old values at the same time. A null new value does
        not remove an old value. Raise ShrinkError before any write if a shard
        would lose an old timestamp.
        """
        if not rows:
            return None
        groups = {}
        for t, vals in rows.items():
            groups.setdefault(span_key(t, span), {})[t] = vals
        pending = []
        names = [c["name"] for c in cols]
        for key, part in sorted(groups.items()):
            rel = f"{tier}/{key}.json"
            old = self.read(ds, rel)
            merged = decode_series(old, names) if old else {}
            for t, vals in part.items():
                prev = merged.get(t, [None] * len(names))
                merged[t] = [v if v is not None else p for v, p in zip(vals, prev)]
            start, end = span_bounds(key, span)
            if span == "all" and dt and merged:
                start = min(merged)
                if old and "dt" in old:
                    start = min(start, old["t0"])
                start -= start % dt
                end = max(merged) + dt
            new = encode_series(ds["id"], merged, cols, dt if (dt and start is not None) else None, start, end)
            check_never_shrink(old, new, window_start)
            pending.append((rel, new))
        for rel, new in pending:
            self.write(ds, rel, new)
        return min(rows), max(rows)

    def load_rows(self, ds, tier, span, names, t_from, t_to):
        rows = {}
        for key in self.list(ds, tier):
            s, e = span_bounds(key, span)
            if s is not None and (e <= t_from or s > t_to):
                continue
            shard = self.read(ds, f"{tier}/{key}.json")
            if shard:
                for t, v in decode_series(shard, names).items():
                    if t_from <= t <= t_to:
                        rows[t] = v
        return rows

    def prune_tier(self, ds, tier, span, keep_seconds):
        """Delete shards older than the window. Trim an 'all' regular shard."""
        if not keep_seconds:
            return 0
        cutoff = self.clock.now() - keep_seconds
        removed = 0
        for key in self.list(ds, tier):
            if span == "all":
                shard = self.read(ds, f"{tier}/{key}.json")
                if shard and "dt" in shard and shard["t0"] < cutoff - shard["dt"]:
                    drop = (cutoff - shard["t0"]) // shard["dt"]
                    drop = min(drop, shard["n"])
                    shard["t0"] += drop * shard["dt"]
                    shard["n"] -= drop
                    shard["cols"] = {c: v[drop:] for c, v in shard["cols"].items()}
                    self.write(ds, f"{tier}/{key}.json", shard)
                continue
            _, end = span_bounds(key, span)
            if end is not None and end <= cutoff:
                self.remove(ds, f"{tier}/{key}.json")
                removed += 1
        return removed

    # events
    def merge_events(self, ds, events, keep_seconds=None, key_time="t_start", span="month", keep_fn=None):
        """Merge event records into monthly (or yearly) files by event ID (plan 5.5).

        Events that are older than the window are not written.
        """
        if keep_seconds:
            cutoff = self.clock.now() - keep_seconds
            events = [e for e in events if (e.get(key_time) or 0) > cutoff and (keep_fn is None or keep_fn(e))]
        groups = {}
        for e in events:
            t = e.get(key_time) or e.get("t_start")
            if t is None:
                continue
            groups.setdefault(span_key(t, span), []).append(e)
        # An event can move to another month when the source changes its time.
        ids = {e["id"] for e in events}
        for key in self.event_keys(ds):
            if key in groups:
                continue
            shard = self.read(ds, f"{key}.json") or {}
            old = shard.get("events", [])
            kept = [e for e in old if e["id"] not in ids]
            if len(kept) != len(old):
                shard["events"] = kept
                self.write(ds, f"{key}.json", shard)
        for key, part in groups.items():
            shard = self.read(ds, f"{key}.json") or {"v": SCHEMA, "id": ds["id"], "period": key, "events": []}
            by_id = {e["id"]: e for e in shard["events"]}
            for e in part:
                by_id[e["id"]] = e
            shard["events"] = sorted(by_id.values(), key=lambda e: (e.get(key_time) or 0, e["id"]))
            self.write(ds, f"{key}.json", shard)
        if keep_seconds:
            cutoff = self.clock.now() - keep_seconds
            for key in self.event_keys(ds):
                _, end = span_bounds(key, "month" if "-" in key else "year")
                if end <= cutoff:
                    self.remove(ds, f"{key}.json")
                    continue
                # Inside the last file, drop the events that are older than the window.
                shard = self.read(ds, f"{key}.json") or {}
                kept = [e for e in shard.get("events", []) if (e.get(key_time) or 0) > cutoff
                        and (keep_fn is None or keep_fn(e))]
                if len(kept) != len(shard.get("events", [])):
                    shard["events"] = kept
                    self.write(ds, f"{key}.json", shard)

    def event_keys(self, ds):
        """Monthly keys 'YYYY-MM' or yearly keys 'YYYY'."""
        return [k for k in self.list(ds) if (len(k) == 7 and k[4] == "-") or (len(k) == 4 and k.isdigit())]

    def all_events(self, ds):
        out = []
        for key in self.event_keys(ds):
            out.extend((self.read(ds, f"{key}.json") or {}).get("events", []))
        return out

    # text products
    def merge_text(self, ds, issue, keep_seconds):
        key = common.ymd(issue["t"])
        shard = self.read(ds, f"r/{key}.json") or {"v": SCHEMA, "id": ds["id"], "date": key, "issues": []}
        by_t = {i["t"]: i for i in shard["issues"]}
        by_t[issue["t"]] = issue
        shard["issues"] = [by_t[t] for t in sorted(by_t)]
        self.write(ds, f"r/{key}.json", shard)
        self.prune_tier(ds, "r", "day", keep_seconds)

    # grids
    def merge_grid_snapshot(self, ds, snap, every, keep_seconds):
        """Add one snapshot to the day file. One snapshot for each 'every' seconds."""
        key = common.ymd(snap["t"])
        shard = self.read(ds, f"{key}.json") or {"v": SCHEMA, "id": ds["id"], "date": key,
                                                  "grid": snap["grid"], "enc": "sparse-rle",
                                                  "q": snap["q"], "fill": snap.get("fill"), "snaps": []}
        slot = snap["t"] - snap["t"] % every
        by_slot = {s["t"] - s["t"] % every: s for s in shard["snaps"]}
        by_slot[slot] = {"t": snap["t"], "data": snap["data"]}
        shard["snaps"] = [by_slot[k] for k in sorted(by_slot)]
        shard["grid"], shard["q"], shard["fill"] = snap["grid"], snap["q"], snap.get("fill")
        self.write(ds, f"{key}.json", shard)
        cutoff = self.clock.now() - keep_seconds
        for k in self.list(ds):
            if len(k) == 10 and k[4] == "-":
                _, end = span_bounds(k, "day")
                if end <= cutoff:
                    self.remove(ds, f"{k}.json")
        return key

    def grid_days(self, ds):
        return [k for k in self.list(ds) if len(k) == 10 and k[4] == "-"]

    def size(self, ds=None):
        base = self.dir_for(ds) if ds else self.root
        total = 0
        for dirpath, dirnames, files in os.walk(base):
            if "_state" in dirpath.split(os.sep):
                continue
            for f in files:
                total += os.path.getsize(os.path.join(dirpath, f))
        return total
