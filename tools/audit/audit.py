#!/usr/bin/env python3
"""Phase 0 endpoint audit for the public data dashboard.

Version 0.1.1. Python 3.9+ standard library only.

For each candidate endpoint in endpoints.json, this script:
  1. Sends one GET with a User-Agent that contains the repository URL.
  2. Records HTTP status, time, size, gzip use, and cache headers.
  3. Sends a conditional GET (If-None-Match / If-Modified-Since) to test 304.
  4. Parses the body and records the schema, record count, and time coverage.
  5. Estimates the store size in the plan format (quantized integer JSON).
It writes report.md, report.json, and one sample file for each endpoint.
The sample files become the test fixtures in Phase 1.

Usage:
  python3 audit/audit.py --out audit-out
  python3 audit/audit.py --out audit-out --only swpc.
  python3 audit/audit.py --out audit-out --pages-check https://<user>.github.io/<repo>/test.json
"""

import argparse
import csv
import datetime as dt
import gzip
import json
import os
import platform
import re
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

VERSION = "0.1.1"
MAX_BYTES = 80 * 1024 * 1024    # stop reading a body after 80 MB
SAMPLE_MAX = 3 * 1024 * 1024    # keep max 3 MB of each body as a fixture
TIMEOUT = 45                    # seconds for each request
WORKERS = 6
PER_HOST = 2                    # max parallel requests to one host (plan 9.2)
BYTES_PER_VALUE = 5             # quantized integer plus comma (plan 5.2)
BYTES_PER_EVENT = 120           # normalized event record (plan 5.5)
BUDGET_MB = 150                 # plan 3.2
KEEP_HEADERS = ["Content-Type", "Content-Encoding", "Content-Length", "ETag", "Last-Modified",
                "Expires", "Cache-Control", "Age", "Retry-After", "X-RateLimit-Limit",
                "X-RateLimit-Remaining", "Access-Control-Allow-Origin"]
STALE_DAYS = {"30m": 1, "1h": 2, "1d": 10, "1w": 120}

NOW = dt.datetime.now(dt.timezone.utc)
_host_sem = defaultdict(lambda: threading.Semaphore(PER_HOST))
_host_sem_lock = threading.Lock()


# --------------------------------------------------------------------------- URLs

def expand_url(url, env):
    """Replace {placeholders}. Return (url, missing_key or None)."""
    today = NOW.date()
    subs = {
        "D0": today.isoformat(),
        "D-7": (today - dt.timedelta(days=7)).isoformat(),
        "D-30": (today - dt.timedelta(days=30)).isoformat(),
        "Y": str(today.year),
        "NASA_API_KEY": env.get("NASA_API_KEY") or "DEMO_KEY",
        "FIRMS_MAP_KEY": env.get("FIRMS_MAP_KEY") or "",
    }
    missing = []

    def rep(m):
        k = m.group(1)
        if k in subs:
            if subs[k] == "":
                missing.append(k)
            return subs[k]
        return m.group(0)

    out = re.sub(r"\{([A-Z0-9_\-]+)\}", rep, url)
    return out, (missing[0] if missing else None)


def mask(text, env):
    for k in ("NASA_API_KEY", "FIRMS_MAP_KEY"):
        v = env.get(k)
        if v and v != "DEMO_KEY":
            text = text.replace(v, "***")
    return text


# --------------------------------------------------------------------------- HTTP

def http_get(url, ua, extra=None):
    headers = {"User-Agent": ua, "Accept-Encoding": "gzip", "Accept": "*/*"}
    headers.update(extra or {})
    req = urllib.request.Request(url, headers=headers)
    host = urllib.request.urlparse(url).netloc
    with _host_sem_lock:
        sem = _host_sem[host]
    t0 = time.monotonic()
    with sem:
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                status, hdrs, final = r.status, r.headers, r.geturl()
                raw = r.read(MAX_BYTES + 1)
        except urllib.error.HTTPError as e:
            status, hdrs, final = e.code, e.headers, url
            try:
                raw = e.read(65536)
            except Exception:
                raw = b""
        except Exception as e:  # DNS, TLS, timeout, proxy refusal
            return {"status": 0, "error": f"{type(e).__name__}: {e}",
                    "ms": round((time.monotonic() - t0) * 1000)}
    ms = round((time.monotonic() - t0) * 1000)
    truncated = len(raw) > MAX_BYTES
    raw = raw[:MAX_BYTES]
    keep = {k: hdrs.get(k) for k in KEEP_HEADERS if hdrs is not None and hdrs.get(k)}
    body = raw
    if "gzip" in (keep.get("Content-Encoding") or "").lower():
        try:
            body = gzip.decompress(raw)
        except Exception:
            body = zlib.decompress(raw, 47)
    return {"status": status, "ms": ms, "headers": keep, "wire_bytes": len(raw),
            "body": body, "final_url": final, "truncated": truncated}


def conditional_status(url, ua, headers):
    extra = {}
    if headers.get("ETag"):
        extra["If-None-Match"] = headers["ETag"]
    if headers.get("Last-Modified"):
        extra["If-Modified-Since"] = headers["Last-Modified"]
    if not extra:
        return None
    r = http_get(url, ua, extra)
    st = r.get("status")
    h2 = r.get("headers") or {}
    changed = st == 200 and ((h2.get("ETag") and h2.get("ETag") != headers.get("ETag")) or
                             (h2.get("Last-Modified") and h2.get("Last-Modified") != headers.get("Last-Modified")))
    return "200 (data changed)" if changed else st


# --------------------------------------------------------------------------- value helpers

NULLS = {"", "null", "none", "nan", "na", "n/a", "-", "--", "-999", "-999.0", "-999.9", "-99999",
         "-9999", "-9999.0", "-99.9", "9999", "99999", "-1e31", "-1.0e31", "-1.00e+31"}
_num_re = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_iso_re = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T_](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?)?(Z|[+-]\d{2}:?\d{2})?$")
_compact_re = re.compile(r"^(\d{4})(\d{2})(\d{2})(?:T?(\d{2})(\d{2})(\d{2})?)?Z?$")
_ym_re = re.compile(r"^(\d{4})-(\d{2})$")


def is_null(v):
    if v is None:
        return True
    if isinstance(v, float) and v != v:
        return True
    if isinstance(v, (int, float)):
        return v in (-999, -9999, -99999, -1e31, 99999)
    return isinstance(v, str) and v.strip().lower() in NULLS


def is_num(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    return isinstance(v, str) and bool(_num_re.match(v.strip()))


def to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def parse_time(v, epoch_ok=False):
    """Return Unix seconds or None. Accepts ISO 8601 forms, YYYY-MM, compact forms, epoch."""
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if not epoch_ok:
            return None
        x = float(v)
        if 1e11 < x < 1e14:
            x /= 1000.0           # epoch milliseconds
        return x if 3e8 < x < 5e9 else None
    s = str(v).strip()
    m = _iso_re.match(s)
    if m:
        y, mo, d, hh, mi, ss = (int(g) if g else 0 for g in m.groups()[:6])
        try:
            t = dt.datetime(y, mo, d, hh, mi, ss, tzinfo=dt.timezone.utc)
        except ValueError:
            return None
        tz = m.group(7)
        if tz and tz != "Z":
            sign = 1 if tz[0] == "+" else -1
            tz = tz[1:].replace(":", "")
            t -= sign * dt.timedelta(hours=int(tz[:2]), minutes=int(tz[2:4]))
        return t.timestamp()
    m = _ym_re.match(s)
    if m:
        return dt.datetime(int(m.group(1)), int(m.group(2)), 15, tzinfo=dt.timezone.utc).timestamp()
    m = _compact_re.match(s)
    if m and 1900 <= int(m.group(1)) <= 2100:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mi, ss = (int(g) if g else 0 for g in m.groups()[3:6])
        try:
            return dt.datetime(y, mo, d, hh, mi, ss, tzinfo=dt.timezone.utc).timestamp()
        except ValueError:
            return None
    if re.search(r"[A-Za-z]{3}", s) and re.search(r"\d{4}", s) and len(s) <= 40:
        s2 = re.sub(r"\s+(UTC|GMT|UT|Z|\+0000)$", "", s)
        for fmt in _TEXT_FORMATS:
            try:
                return dt.datetime.strptime(s2, fmt).replace(tzinfo=dt.timezone.utc).timestamp()
            except ValueError:
                continue
    return None


_TEXT_FORMATS = ["%Y-%b-%d %H:%M", "%Y-%b-%d %H:%M:%S", "%Y %b %d %H%M", "%Y %b %d %H:%M", "%Y %b %d",
                 "%a, %d %b %Y %H:%M:%S", "%d %b %Y %H:%M:%S", "%d %b %Y %H:%M", "%d %b %Y", "%b %d, %Y",
                 "%B %d, %Y", "%Y-%b-%d"]
_SEASONS = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8, "ASO": 9,
            "SON": 10, "OND": 11, "NDJ": 12}


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M") if t is not None else None


def human_step(s):
    if s is None:
        return "-"
    if s < 120:
        return f"{s:.0f} s"
    if s < 7200:
        return f"{s / 60:.0f} min"
    if s < 172800:
        return f"{s / 3600:.1f} h"
    return f"{s / 86400:.1f} d"


def decode(body):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return body.decode(enc)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", "replace")


# --------------------------------------------------------------------------- table analysis

def column_info(name, values):
    sample = values[:3000]
    nonnull = [v for v in sample if not is_null(v)]
    kinds = Counter()
    for v in nonnull:
        if isinstance(v, (dict, list)):
            kinds["nested"] += 1
        elif is_num(v):
            kinds["number"] += 1
        elif parse_time(v) is not None:
            kinds["time"] += 1
        else:
            kinds["string"] += 1
    ctype = kinds.most_common(1)[0][0] if kinds else "empty"
    first = next((v for v in values if not is_null(v)), None)
    sample_txt = json.dumps(first)[:40] if first is not None else ""
    null_frac = 1 - len(nonnull) / len(sample) if sample else 1.0
    return {"name": str(name), "type": ctype, "null_pct": round(100 * null_frac, 1), "sample": sample_txt}


def pick_time(header, cols, rows, ep):
    """Return (list of unix seconds, description) or (None, None)."""
    if ep.get("time_col"):
        names = [c["name"] for c in cols]
        if ep["time_col"] in names:
            i = names.index(ep["time_col"])
            fmt = ep.get("time_fmt")
            out = []
            for r in rows:
                v = r[i] if i < len(r) else None
                try:
                    t = (dt.datetime.strptime(str(v).strip(), fmt).replace(tzinfo=dt.timezone.utc).timestamp()
                         if fmt else parse_time(v, epoch_ok=True))
                except ValueError:
                    t = None
                if t is not None:
                    out.append(t)
            return (out or None), f"column '{ep['time_col']}'" + (f" ({fmt})" if fmt else "")
    if ep.get("time_nested"):
        names = [c["name"] for c in cols]
        col, key = ep["time_nested"]["col"], ep["time_nested"]["key"]
        if col in names:
            i = names.index(col)
            out = []
            for r in rows:
                v = r[i] if i < len(r) else None
                if isinstance(v, list) and v and isinstance(v[-1], dict):
                    t = parse_time(v[-1].get(key))
                    if t is not None:
                        out.append(t)
            return (out or None), f"last item of '{col}', key '{key}'"
    if ep.get("time_season"):
        si, yi = ep["time_season"]
        out = []
        for r in rows:
            try:
                out.append(dt.datetime(int(r[yi]), _SEASONS[r[si].upper()], 15,
                                       tzinfo=dt.timezone.utc).timestamp())
            except (KeyError, ValueError, IndexError):
                continue
        return (out or None), f"season column {si} + year column {yi}"
    hint = ep.get("time_ymd") or ep.get("time_ym")
    if hint:
        out = []
        for r in rows:
            try:
                parts = [int(float(r[i])) for i in hint]
            except (ValueError, IndexError, TypeError):
                continue
            if ep.get("time_ym"):
                parts = parts[:2] + [15]
            parts += [0] * (6 - len(parts))
            y, mo, d, hh, mi, ss = parts[:6]
            if y < 100:
                y += 2000 if y < 70 else 1900
            try:
                out.append(dt.datetime(y, mo, d, hh, mi, ss, tzinfo=dt.timezone.utc).timestamp())
            except ValueError:
                continue
        return (out or None), f"columns {hint}"
    order = sorted(range(len(cols)), key=lambda i: (
        0 if re.search(r"time|date|epoch|issue|begin|start", cols[i]["name"], re.I) else 1, i))
    for i in order:
        c = cols[i]
        name_hit = re.search(r"time|date|epoch", c["name"], re.I)
        if c["type"] == "time" or (c["type"] == "number" and name_hit):
            ts = [parse_time(r[i] if i < len(r) else None, epoch_ok=bool(name_hit)) for r in rows]
            ts = [t for t in ts if t is not None]
            if len(ts) >= max(1, len(rows) // 2):
                return ts, f"column '{c['name']}'"
    return None, None


def time_stats(ts):
    u = sorted(set(ts))
    first, last = u[0], u[-1]
    diffs = [b - a for a, b in zip(u, u[1:])]
    return {"first": iso(first), "last": iso(last), "first_unix": first, "last_unix": last,
            "span_days": round((last - first) / 86400, 3),
            "median_step_s": statistics.median(diffs) if diffs else None,
            "unique_times": len(u),
            "age_hours": round((NOW.timestamp() - last) / 3600, 1)}


def analyze_table(header, rows, ep, shape):
    header = [str(h) for h in header]
    width = max([len(header)] + [len(r) for r in rows[:200]]) if rows else len(header)
    header += [f"c{i}" for i in range(len(header), width)]
    cols = [column_info(h, [r[i] if i < len(r) else None for r in rows]) for i, h in enumerate(header)]
    ts, tdesc = pick_time(header, cols, rows, ep)
    a = {"shape": shape, "records": len(rows), "columns": cols,
         "numeric_cols": sum(1 for c in cols if c["type"] == "number"
                             and not re.search(r"^(year|month|day|yy|mm|dd|hh|time|date)$", c["name"], re.I))}
    hint_cols = ep.get("time_ymd") or ep.get("time_ym") or ep.get("time_season") or []
    a["numeric_cols"] = max(0, a["numeric_cols"] - sum(
        1 for i in hint_cols if i < len(cols) and cols[i]["type"] == "number"
        and not re.search(r"^(year|month|day|yy|mm|dd|hh)$", cols[i]["name"], re.I)))
    if ts:
        a["time"] = time_stats(ts)
        a["time"]["source"] = tdesc
    if ep.get("grid_from_points"):
        names = [h.lower() for h in header]
        li = next((i for i, h in enumerate(names) if h in ("latitude", "lat")), None)
        oi = next((i for i, h in enumerate(names) if h in ("longitude", "lon", "lng")), None)
        if li is not None and oi is not None:
            deg = ep["grid_from_points"]
            cells = set()
            for r in rows:
                la, lo = to_float(r[li]), to_float(r[oi])
                if la is not None and lo is not None:
                    cells.add((int((la + 90) // deg), int((lo + 180) // deg)))
            a["nonnull_cells"] = len(cells)
            a["grid_note"] = f"{len(rows)} points fall in {len(cells)} cells of {deg} deg"
    return a


def analyze_records(recs, ep, shape):
    keys = []
    for r in recs[:300]:
        for k in r:
            if k not in keys:
                keys.append(k)
    rows = [[r.get(k) for k in keys] for r in recs]
    return analyze_table(keys, rows, ep, shape)


def analyze_matrix(rows, ep, shape, meta=None):
    n = len(rows)
    width = len(rows[0]) if n else 0
    last = [r[-1] for r in rows if r]
    nums = [to_float(v) for v in last if is_num(v)]
    nonzero = sum(1 for v in nums if v not in (0, 0.0))
    a = {"shape": f"{shape}, {n} x {width}", "records": n, "columns": [], "numeric_cols": 1,
         "cells": n, "nonnull_cells": nonzero,
         "grid_note": f"last column: {nonzero} of {n} cells non-zero ({100 * nonzero / n:.1f} %)" if n else ""}
    if nums:
        a["value_range"] = [min(nums), max(nums)]
    if meta:
        a["meta"] = {k: (str(v)[:60]) for k, v in meta.items()}
        for k, v in meta.items():
            t = parse_time(v)
            if t:
                a["time"] = time_stats([t])
                a["time"]["source"] = f"key '{k}'"
                break
    return a


def analyze_json(obj, ep):
    if isinstance(obj, dict):
        if obj.get("type") == "FeatureCollection" or isinstance(obj.get("features"), list):
            feats = [f for f in obj.get("features") or [] if isinstance(f, dict)]
            geoms = Counter((f.get("geometry") or {}).get("type", "none") for f in feats)
            props = [dict(f.get("properties") or {}) for f in feats]
            a = analyze_records(props, ep, f"GeoJSON, {len(feats)} features, geometry {dict(geoms)}")
            if obj.get("metadata"):
                a["meta"] = {k: str(v)[:60] for k, v in obj["metadata"].items()}
            return a
        if isinstance(obj.get("fields"), list) and isinstance(obj.get("data"), list):
            return analyze_table(obj["fields"], obj["data"], ep, "object with fields + data rows")
        if isinstance(obj.get("times"), list) and isinstance(obj.get("values"), list):
            series = [v for v in obj["values"] if isinstance(v, dict)]
            header = ["time"] + [s.get("id", f"v{i}") for i, s in enumerate(series)]
            vals = [s.get("values") or [] for s in series]
            rows = [[t] + [v[i] if i < len(v) else None for v in vals] for i, t in enumerate(obj["times"])]
            return analyze_table(header, rows, ep, "object with times + values arrays")
        if isinstance(obj.get("coordinates"), list) and obj["coordinates"] and isinstance(obj["coordinates"][0], list):
            meta = {k: v for k, v in obj.items() if k != "coordinates"}
            return analyze_matrix(obj["coordinates"], ep, "grid points [lon, lat, value]", meta)
        lists = [(k, v) for k, v in obj.items() if isinstance(v, list) and v]
        if lists:
            k, v = max(lists, key=lambda kv: len(kv[1]))
            a = analyze_json(v, ep)
            a["shape"] = f"object, list in key '{k}': " + a["shape"]
            a["top_keys"] = list(obj.keys())[:20]
            return a
        big = [(k, v) for k, v in obj.items() if isinstance(v, dict) and len(v) > 20]
        if big:
            k, v = max(big, key=lambda kv: len(kv[1]))
            recs = [dict(x, _key=kk) if isinstance(x, dict) else {"_key": kk, "value": x} for kk, x in v.items()]
            a = analyze_records(recs, ep, f"object, key '{k}' maps {len(recs)} keys to records")
            a["top_keys"] = list(obj.keys())[:20]
            return a
        if obj and all(isinstance(v, dict) for v in obj.values()):
            recs = [dict(v, _key=k) for k, v in obj.items()]
            return analyze_records(recs, ep, f"object of {len(recs)} objects")
        return {"shape": "object", "records": 1, "columns": [], "numeric_cols": 0,
                "top_keys": list(obj.keys())[:30]}
    if isinstance(obj, list):
        if not obj:
            return {"shape": "empty list", "records": 0, "columns": [], "numeric_cols": 0}
        head = obj[:50]
        if all(isinstance(r, list) for r in head):
            first = obj[0]
            if len(obj) > 1 and first and all(isinstance(x, str) for x in first) \
                    and sum(is_num(x) for x in first) < len(first) / 2:
                return analyze_table(first, obj[1:], ep, "list of rows, first row is header")
            return analyze_matrix(obj, ep, "list of rows, no header")
        if all(isinstance(r, dict) for r in head):
            return analyze_records([r for r in obj if isinstance(r, dict)], ep, "list of objects")
        return analyze_table(["value"], [[v] for v in obj], ep, "list of values")
    return {"shape": type(obj).__name__, "records": 1, "columns": [], "numeric_cols": 0}


def split_lines(text, ep):
    lines = text.splitlines()[ep.get("skip_lines", 0):]
    c = ep.get("comment")
    if c:
        lines = [ln for ln in lines if not ln.lstrip().startswith(c)]
    return [ln for ln in lines if ln.strip()]


def finish_rows(rows, ep):
    if not rows:
        return [], []
    use_header = ep.get("header", True)
    if use_header and sum(is_num(x) for x in rows[0]) >= max(1, len(rows[0]) // 2):
        use_header = False          # first row is data
    if use_header:
        header, rows = rows[0], rows[1:]
    else:
        header = [f"c{i}" for i in range(len(rows[0]))]
    if ep.get("units_row") and rows:
        rows = rows[1:]
    return header, rows


def read_csv(text, ep):
    lines = split_lines(text, ep)
    delim = ep.get("csv_delim")
    if not delim:
        probe = "\n".join(lines[:20])
        delim = max([",", ";", "\t", "|"], key=probe.count)
    rows = [[x.strip() for x in r] for r in csv.reader(lines, delimiter=delim)]
    return finish_rows(rows, ep)


def read_ws(text, ep):
    rows = [ln.split() for ln in split_lines(text, ep)]
    return finish_rows(rows, ep)


def analyze_text(text):
    lines = text.splitlines()
    issued = next((ln.split(":", 2)[-1].strip() for ln in lines if re.match(r"^:?Issued:", ln.strip())), None)
    head = [ln.strip() for ln in lines if ln.strip()][:3]
    a = {"shape": f"text, {len(lines)} lines", "records": len(lines), "columns": [], "numeric_cols": 0,
         "head": head}
    if issued:
        a["issued"] = issued
        t = parse_time(issued)
        if t:
            a["time"] = time_stats([t])
            a["time"]["source"] = "Issued line"
    return a


def analyze_xml(body):
    root = ET.fromstring(body)

    def local(tag):
        return tag.rsplit("}", 1)[-1]

    items = [e for e in root.iter() if local(e.tag) in ("entry", "item")]
    if not items:
        tags = Counter(local(c.tag) for c in root)
        tag, n = tags.most_common(1)[0] if tags else ("-", 0)
        return {"shape": f"XML <{local(root.tag)}>, {n} <{tag}> children", "records": n,
                "columns": [], "numeric_cols": 0}
    first = items[0]
    fields = {local(c.tag): (c.text or "").strip() for c in first}
    times = []
    for it in items:
        for c in it:
            if local(c.tag) in ("updated", "published", "pubDate", "date"):
                t = parse_time(c.text or "")
                if t is None:
                    try:
                        t = dt.datetime.strptime((c.text or "").strip()[:25], "%a, %d %b %Y %H:%M:%S").replace(
                            tzinfo=dt.timezone.utc).timestamp()
                    except ValueError:
                        t = None
                if t:
                    times.append(t)
                    break
    a = {"shape": f"XML feed <{local(root.tag)}>, {len(items)} items", "records": len(items),
         "columns": [{"name": k, "type": "string", "null_pct": 0, "sample": json.dumps(v)[:40]}
                     for k, v in list(fields.items())[:12]],
         "numeric_cols": 0}
    if times:
        a["time"] = time_stats(times)
        a["time"]["source"] = "item date"
    return a


def analyze_index(text):
    plain = re.sub(r"<[^>]+>", " ", text)
    files = []
    for ln in plain.splitlines():
        m = re.match(r"^\s*(\S+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(\S+)", ln)
        if m and m.group(1) not in ("Parent", "Name"):
            files.append({"name": m.group(1), "modified": m.group(2), "size": m.group(3)})
    if not files:
        names = re.findall(r'href="([^"?#]+)"', text)
        files = [{"name": n, "modified": "", "size": ""} for n in names
                 if not n.startswith(("/", "..", "http")) and n != "./"]
    return {"shape": f"directory listing, {len(files)} entries", "records": len(files), "columns": [],
            "numeric_cols": 0, "files": files}


def analyze_erddap_info(text):
    rows = list(csv.reader(text.splitlines()))
    glob = {r[2]: r[4] for r in rows if len(r) >= 5 and r[0] == "attribute" and r[1] == "NC_GLOBAL"}
    dims = [f"{r[1]}: {r[4]}" for r in rows if len(r) >= 5 and r[0] == "dimension"]
    var_names = [r[1] for r in rows if len(r) >= 2 and r[0] == "variable"]
    a = {"shape": "ERDDAP dataset info", "records": len(rows), "columns": [], "numeric_cols": 0,
         "meta": {"title": glob.get("title", "")[:80],
                  "time_coverage_start": glob.get("time_coverage_start", ""),
                  "time_coverage_end": glob.get("time_coverage_end", ""),
                  "dimensions": "; ".join(dims)[:200],
                  "variables": ", ".join(var_names)[:200]}}
    t = parse_time(glob.get("time_coverage_end", ""))
    if t:
        a["time"] = time_stats([t])
        a["time"]["source"] = "time_coverage_end"
    return a


def analyze_erddap_search(text):
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        return {"shape": "empty", "records": 0, "columns": [], "numeric_cols": 0}
    h = rows[0]
    idx = {name: h.index(name) for name in ("griddap", "Title", "Dataset ID", "Institution") if name in h}
    found = []
    for r in rows[1:]:
        if len(r) < len(h):
            continue
        found.append({"name": r[idx["Dataset ID"]] if "Dataset ID" in idx else "",
                      "modified": "griddap" if ("griddap" in idx and r[idx["griddap"]]) else "tabledap",
                      "size": (r[idx["Title"]] if "Title" in idx else "")[:110]})
    return {"shape": f"ERDDAP search, {len(found)} datasets", "records": len(found), "columns": [],
            "numeric_cols": 0, "files": found}


def analyze_erddap_grid(text, ep):
    rows = list(csv.reader(text.splitlines()))
    if len(rows) < 3:
        return {"shape": "ERDDAP grid (no data)", "records": 0, "columns": [], "numeric_cols": 0}
    header, units, data = rows[0], rows[1], rows[2:]
    vi = len(header) - 1
    vals = [to_float(r[vi]) for r in data if len(r) > vi]
    good = [v for v in vals if v is not None and v == v]
    lat_i = next((i for i, h in enumerate(header) if h.lower().startswith("lat")), None)
    lon_i = next((i for i, h in enumerate(header) if h.lower().startswith("lon")), None)
    nlat = len({r[lat_i] for r in data}) if lat_i is not None else 0
    nlon = len({r[lon_i] for r in data}) if lon_i is not None else 0
    a = {"shape": f"ERDDAP grid CSV, {nlat} lat x {nlon} lon, variable '{header[vi]}' ({units[vi]})",
         "records": len(data), "cells": len(data), "nonnull_cells": len(good), "numeric_cols": 1,
         "columns": [{"name": h, "type": "", "null_pct": 0, "sample": (data[0][i] if data else "")}
                     for i, h in enumerate(header)],
         "grid_note": f"{len(good)} of {len(data)} cells have a value ({100 * len(good) / max(1, len(data)):.1f} %)"}
    if good:
        a["value_range"] = [round(min(good), 3), round(max(good), 3)]
    ti = header.index("time") if "time" in header else None
    if ti is not None and data:
        ts = [t for t in (parse_time(r[ti]) for r in data[:5]) if t]
        if ts:
            a["time"] = time_stats(ts)
            a["time"]["source"] = "grid time"
    return a


def analyze(ep, body):
    fmt = ep.get("fmt", "json")
    if fmt == "xml":
        return analyze_xml(body)
    text = decode(body)
    if fmt == "index":
        return analyze_index(text)
    if fmt == "text":
        return analyze_text(text)
    if fmt == "erddap_info":
        return analyze_erddap_info(text)
    if fmt == "erddap_search":
        return analyze_erddap_search(text)
    if fmt == "erddap_csv":
        return analyze_erddap_grid(text, ep)
    if fmt == "csv":
        h, rows = read_csv(text, ep)
        return analyze_table(h, rows, ep, f"CSV, {len(h)} columns")
    if fmt == "ws":
        h, rows = read_ws(text, ep)
        return analyze_table(h, rows, ep, f"whitespace table, {len(h)} columns")
    return analyze_json(json.loads(text), ep)


# --------------------------------------------------------------------------- estimate and checks

def estimate(ep, a):
    kind = ep.get("kind")
    t = a.get("time") or {}
    span = t.get("span_days") or 0
    per_day = None
    basis = ""
    if kind == "series" and a.get("records") and span > 0:
        cols = ep.get("store_cols") or a.get("numeric_cols") or 1
        per_day = a["records"] / span * cols * BYTES_PER_VALUE
        basis = f"{a['records'] / span:.0f} rows/day x {cols} cols x {BYTES_PER_VALUE} B"
    elif kind == "events" and a.get("records") and span > 0.5:
        per_day = a["records"] / span * BYTES_PER_EVENT
        basis = f"{a['records'] / span:.1f} events/day x {BYTES_PER_EVENT} B"
    elif kind == "grid" and a.get("nonnull_cells") is not None:
        snaps = ep.get("snaps_per_day", 1)
        per_day = a["nonnull_cells"] * BYTES_PER_VALUE * snaps
        basis = f"{a['nonnull_cells']} cells x {BYTES_PER_VALUE} B x {snaps} snapshots/day"
    out = {"bytes_per_day": round(per_day) if per_day else None, "basis": basis}
    days = ep.get("retain_days")
    if per_day and days:
        out["window_mb"] = round(per_day * days / 1e6, 2)
    return out


def checks(ep, res):
    issues = []
    if ep.get("note"):
        issues.append(f"note: {ep['note']}")
    for n in res.get("notes") or []:
        issues.append(n)
    st = res.get("status")
    if st != 200:
        issues.append(f"no connection: {res.get('error', '')}" if st == 0 else f"HTTP {st}")
        return issues
    if res.get("truncated"):
        issues.append(f"body is more than {MAX_BYTES // 1e6:.0f} MB; truncated")
    if res.get("parse_error"):
        issues.append(f"parse error: {res['parse_error']}")
        return issues
    a = res.get("analysis") or {}
    h = res.get("headers") or {}
    discovery = ep.get("kind") == "discovery"
    if not discovery and not (h.get("ETag") or h.get("Last-Modified")):
        issues.append("no ETag or Last-Modified: compare a hash to detect change")
    elif not discovery and res.get("cond_status") not in (304, None, "200 (data changed)"):
        issues.append(f"conditional GET gave {res.get('cond_status')}, not 304")
    if ep.get("kind") in ("series", "events") and not a.get("time") and (a.get("records") or 0) > 1:
        issues.append("no time column found: add a time hint to endpoints.json")
    if a.get("records") == 0 and ep.get("kind") not in ("events",):
        issues.append("no records")
    t = a.get("time")
    lim = ep.get("max_age_days") or STALE_DAYS.get(ep.get("tier"))
    if t and lim and t.get("age_hours") is not None and t["age_hours"] > lim * 24:
        issues.append(f"newest data is {t['age_hours'] / 24:.1f} days old (limit {lim} d for tier {ep.get('tier')})")
    if t and t.get("age_hours") is not None and t["age_hours"] < -48 and ep.get("kind") == "series" \
            and not ep.get("forecast"):
        issues.append("file contains future times (forecast rows?)")
    return issues


# --------------------------------------------------------------------------- run one

def run_one(ep, ua, env, samples_dir):
    url, missing = expand_url(ep["url"], env)
    res = {"id": ep["id"], "domain": ep.get("domain", ""), "kind": ep.get("kind", ""),
           "tier": ep.get("tier", ""), "url": mask(url, env), "license": ep.get("license", "")}
    if missing:
        res.update(status=None, url=ep["url"], skipped=f"secret {missing} not set")
        return res
    r = http_get(url, ua)
    body = r.pop("body", b"")
    res.update(r)
    if "final_url" in res:
        res["final_url"] = mask(res["final_url"], env)
    if res.get("error"):
        res["error"] = mask(res["error"], env)
    res["body_bytes"] = len(body)
    if body:
        res["gzip_bytes"] = len(gzip.compress(body, 6))
        ext = {"json": "json", "csv": "csv", "erddap_csv": "csv", "erddap_info": "csv", "erddap_search": "csv",
               "xml": "xml", "index": "html"}.get(ep.get("fmt"), "txt")
        name = f"{ep['id']}.{ext}" + (".truncated" if len(body) > SAMPLE_MAX else "")
        with open(os.path.join(samples_dir, name), "wb") as f:
            f.write(body[:SAMPLE_MAX])
    if res.get("status") == 200 and body:
        for attempt in range(3):     # some servers send a truncated body; try again (plan 9.1)
            try:
                res["analysis"] = analyze(ep, body)
                res.pop("parse_error", None)
                break
            except Exception as e:
                res["parse_error"] = f"{type(e).__name__}: {e}"[:300]
                if attempt == 2:
                    break
                time.sleep(3)
                r2 = http_get(url, ua)
                if r2.get("status") != 200:
                    break
                body = r2.pop("body", b"")
                res["parse_retries"] = attempt + 1
        if res.get("parse_retries") and not res.get("parse_error"):
            res.setdefault("notes", []).append(f"parse OK after {res['parse_retries']} retry")
        res["cond_status"] = conditional_status(url, ua, res.get("headers") or {})
        if res.get("analysis"):
            res["estimate"] = estimate(ep, res["analysis"])
    res["issues"] = checks(ep, res)
    return res


def pages_check(url, ua):
    out = {"url": url}
    r = http_get(url, ua)
    body = r.pop("body", b"")
    out.update(status=r.get("status"), headers=r.get("headers"), wire_bytes=r.get("wire_bytes"),
               body_bytes=len(body), error=r.get("error"))
    out["gzip_served"] = "gzip" in ((r.get("headers") or {}).get("Content-Encoding") or "")
    out["cond_status"] = conditional_status(url, ua, r.get("headers") or {}) if r.get("status") == 200 else None
    return out


# --------------------------------------------------------------------------- report

def kb(n):
    return "-" if n is None else (f"{n / 1024:.0f}" if n >= 10240 else f"{n / 1024:.1f}")


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def write_report(results, meta, pages, out_dir):
    ok = [r for r in results if r.get("status") == 200 and not r.get("parse_error")]
    failed = [r for r in results if r.get("status") not in (200, None)]
    parse_bad = [r for r in results if r.get("parse_error")]
    skipped = [r for r in results if r.get("skipped")]
    cond = [r for r in ok if (r.get("headers") or {}).get("ETag") or (r.get("headers") or {}).get("Last-Modified")]
    c304 = [r for r in ok if r.get("cond_status") == 304]
    gz = [r for r in ok if "gzip" in ((r.get("headers") or {}).get("Content-Encoding") or "")]
    total_mb = sum((r.get("estimate") or {}).get("window_mb") or 0 for r in ok if r.get("tier") != "backfill")

    L = []
    L.append("# Phase 0 endpoint audit\n")
    L.append(f"Audit version {VERSION} · run {meta['run_utc']} · {meta['runner']} · Python {meta['python']}\n")
    L.append("## Summary\n")
    L.append(f"- Endpoints: {len(results)}. OK: {len(ok)}. Failed: {len(failed)}. "
             f"Parse errors: {len(parse_bad)}. Skipped (no secret): {len(skipped)}.")
    L.append(f"- Conditional GET headers (ETag or Last-Modified): {len(cond)} of {len(ok)}. "
             f"304 confirmed: {len(c304)}.")
    L.append(f"- Server sends gzip: {len(gz)} of {len(ok)}.")
    L.append(f"- Estimated raw-window store for the measured datasets: {total_mb:.1f} MB "
             f"(plan budget {BUDGET_MB} MB). Summary tiers are not included.\n")

    act = [r for r in results if r.get("issues") or r.get("skipped")]
    L.append("## Action items\n")
    if not act:
        L.append("None.\n")
    else:
        L.append("| ID | Problem | URL |")
        L.append("| --- | --- | --- |")
        for r in act:
            prob = r.get("skipped") or "; ".join(r.get("issues") or [])
            L.append(f"| {r['id']} | {md_escape(prob)[:220]} | {md_escape(r['url'])[:120]} |")
        L.append("")

    L.append("## Results by domain\n")
    by_dom = defaultdict(list)
    for r in results:
        if r.get("kind") != "discovery":
            by_dom[r["domain"]].append(r)
    for dom, rs in by_dom.items():
        L.append(f"### {dom}\n")
        L.append("| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |")
        L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in rs:
            a = r.get("analysis") or {}
            t = a.get("time") or {}
            h = r.get("headers") or {}
            cache = "".join(["E" if h.get("ETag") else "", "L" if h.get("Last-Modified") else "",
                             "C" if h.get("Cache-Control") else "", "X" if h.get("Expires") else ""]) or "-"
            e = r.get("estimate") or {}
            status = r.get("status") if r.get("status") is not None else "skip"
            L.append(f"| {r['id']} | {status} | {r.get('ms', '-')} | {kb(r.get('body_bytes'))} | "
                     f"{kb(r.get('gzip_bytes'))} | {cache} | {r.get('cond_status') or '-'} | "
                     f"{a.get('records', '-')} | {t.get('last') or '-'} | {human_step(t.get('median_step_s'))} | "
                     f"{kb(e.get('bytes_per_day'))} | {e.get('window_mb', '-')} |")
        L.append("")
    L.append("Cache: E = ETag, L = Last-Modified, C = Cache-Control, X = Expires. "
             "KB = decompressed body. gzip KB = body after local gzip -6.\n")

    L.append("## Dataset details\n")
    for r in results:
        if r.get("kind") == "discovery" or r.get("status") != 200:
            continue
        a = r.get("analysis") or {}
        h = r.get("headers") or {}
        L.append(f"### {r['id']}\n")
        L.append(f"- URL: `{r['url']}`")
        if r.get("final_url") and r["final_url"] != r["url"]:
            L.append(f"- Redirected to: `{r['final_url']}`")
        L.append(f"- Content-Type: {h.get('Content-Type', '-')}. Cache-Control: {h.get('Cache-Control', '-')}. "
                 f"Expires: {h.get('Expires', '-')}.")
        if r.get("license"):
            L.append(f"- License note: {r['license']}")
        if r.get("parse_error"):
            L.append(f"- Parse error: {r['parse_error']}\n")
            continue
        L.append(f"- Shape: {a.get('shape')}")
        if a.get("time"):
            t = a["time"]
            L.append(f"- Time ({t.get('source')}): {t['first']} to {t['last']} UTC, span {t['span_days']} d, "
                     f"step {human_step(t.get('median_step_s'))}, age of newest {t['age_hours']} h")
        if a.get("grid_note"):
            L.append(f"- Grid: {a['grid_note']}")
        if a.get("value_range"):
            L.append(f"- Value range: {a['value_range'][0]} to {a['value_range'][1]}")
        if a.get("issued"):
            L.append(f"- Issued: {a['issued']}")
        if a.get("head"):
            L.append(f"- First lines: {md_escape(' / '.join(a['head']))[:200]}")
        if a.get("meta"):
            L.append("- Metadata: " + "; ".join(f"{k} = {md_escape(v)}" for k, v in a["meta"].items())[:400])
        if a.get("top_keys"):
            L.append(f"- Top keys: {', '.join(map(str, a['top_keys']))}")
        if r.get("estimate", {}).get("basis"):
            L.append(f"- Estimate basis: {r['estimate']['basis']}")
        if a.get("columns"):
            L.append("")
            L.append("| Column | Type | Null % | Sample |")
            L.append("| --- | --- | --- | --- |")
            for c in a["columns"][:30]:
                L.append(f"| {md_escape(c['name'])[:40]} | {c['type']} | {c['null_pct']} | {md_escape(c['sample'])} |")
            if len(a["columns"]) > 30:
                L.append(f"| ... {len(a['columns']) - 30} more | | | |")
        if r.get("issues"):
            L.append("")
            L.append("Issues: " + "; ".join(r["issues"]))
        L.append("")

    L.append("## Discovery\n")
    for r in results:
        if r.get("kind") != "discovery":
            continue
        a = r.get("analysis") or {}
        L.append(f"### {r['id']}\n")
        L.append(f"`{r['url']}` · HTTP {r.get('status')} {r.get('error', '') or ''}\n")
        if a.get("meta"):
            for k, v in a["meta"].items():
                L.append(f"- {k}: {md_escape(v)}")
        files = a.get("files") or []
        if files:
            L.append("| Name | Modified / type | Size / title |")
            L.append("| --- | --- | --- |")
            for f in files[:150]:
                L.append(f"| {md_escape(f['name'])} | {md_escape(f['modified'])} | {md_escape(f['size'])} |")
            if len(files) > 150:
                L.append(f"| ... {len(files) - 150} more | | |")
        elif a.get("shape"):
            L.append(f"- Shape: {a['shape']}")
        L.append("")

    if pages:
        L.append("## GitHub Pages check\n")
        h = pages.get("headers") or {}
        L.append(f"- URL: `{pages['url']}` · HTTP {pages.get('status')} {pages.get('error') or ''}")
        L.append(f"- gzip served: {'yes' if pages.get('gzip_served') else 'no'} "
                 f"({kb(pages.get('wire_bytes'))} KB on the wire, {kb(pages.get('body_bytes'))} KB body)")
        L.append(f"- Cache-Control: {h.get('Cache-Control', '-')}. ETag: {h.get('ETag', '-')}. "
                 f"Last-Modified: {h.get('Last-Modified', '-')}. Conditional GET: {pages.get('cond_status')}\n")

    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------- main

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=f"Phase 0 endpoint audit v{VERSION}")
    ap.add_argument("--endpoints", default=os.path.join(here, "endpoints.json"))
    ap.add_argument("--out", default="audit-out")
    ap.add_argument("--only", default="", help="comma-separated id prefixes")
    ap.add_argument("--pages-check", default="", help="URL of a JSON file on your GitHub Pages site")
    args = ap.parse_args()

    env = dict(os.environ)
    repo = env.get("AUDIT_REPO_URL") or (
        f"{env['GITHUB_SERVER_URL']}/{env['GITHUB_REPOSITORY']}" if env.get("GITHUB_REPOSITORY") else "local-test")
    ua = f"public-data-dashboard-audit/{VERSION} (+{repo})"

    with open(args.endpoints) as f:
        eps = json.load(f)["endpoints"]
    prefixes = [p.strip() for p in args.only.split(",") if p.strip()]
    if prefixes:
        eps = [e for e in eps if any(e["id"].startswith(p) for p in prefixes)]

    samples = os.path.join(args.out, "samples")
    os.makedirs(samples, exist_ok=True)
    print(f"audit v{VERSION}: {len(eps)} endpoints, UA '{ua}'", flush=True)

    results = [None] * len(eps)
    with ThreadPoolExecutor(WORKERS) as pool:
        futs = {pool.submit(run_one, ep, ua, env, samples): i for i, ep in enumerate(eps)}
        for fut in futs:
            i = futs[fut]
            try:
                results[i] = fut.result()
            except Exception as e:  # never stop the whole audit for one endpoint
                results[i] = {"id": eps[i]["id"], "domain": eps[i].get("domain", ""), "kind": eps[i].get("kind"),
                              "url": mask(eps[i]["url"], env), "status": 0,
                              "error": f"audit crash: {type(e).__name__}: {e}", "issues": ["audit crash"]}
            r = results[i]
            print(f"  {r['id']:<32} {str(r.get('status')):>4}  {r.get('ms', '-'):>6} ms  "
                  f"{(r.get('error') or r.get('skipped') or '')[:70]}", flush=True)

    pages = pages_check(args.pages_check, ua) if args.pages_check else None
    meta = {"version": VERSION, "run_utc": NOW.strftime("%Y-%m-%d %H:%M UTC"),
            "runner": "GitHub Actions" if env.get("GITHUB_ACTIONS") else "local",
            "python": platform.python_version(), "user_agent": ua}
    with open(os.path.join(args.out, "report.json"), "w") as f:
        json.dump({"meta": meta, "results": results, "pages_check": pages}, f, indent=1, default=str)
    write_report(results, meta, pages, args.out)
    bad = sum(1 for r in results if r.get("status") not in (200, None))
    print(f"done: {len(results) - bad} reachable, {bad} failed. Report: {args.out}/report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
