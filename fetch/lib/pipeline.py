"""The procedure for one dataset (plan 9.1): fetch, parse, validate, merge, roll up, prune."""
import os
import time
import traceback

from . import common, grid as gridlib, rollup, validate
from .common import DAY
from .http import FetchError
from .store import SUMMARY_TIERS, ShrinkError, encode_series, raw_span
from .validate import ParseError, ValidationError

PARSE_RETRIES = 2      # rule 9.4a
PARSE_WAIT = 3         # seconds


class Context:
    """What an adapter can use: the clock, the client, the store, and the log."""

    def __init__(self, clock, client, store, offline=False, env=None, log=print, sleep=time.sleep,
                 backfill=False):
        self.clock = clock
        self.client = client
        self.store = store
        self.offline = offline
        self.env = env
        self.log = log
        self.sleep = sleep
        self.backfill = backfill
        self.responses = []    # responses to commit after a good write

    @property
    def now(self):
        return self.clock.now()


def retention(ds, key, default=None):
    return common.duration((ds.get("retention") or {}).get(key)) or default


def event_filter(ds, now):
    """A second window for part of the events: 'events_m4.5': '5y' keeps M4.5+ for 5 y, others 1 y."""
    ret = ds.get("retention") or {}
    if "events_m4.5" not in ret:
        return None
    short = now - (common.duration(ret.get("events")) or 365 * DAY)
    return lambda e: (e.get("mag") or 0) >= 4.5 or e["t_start"] > short


def event_keep(ds):
    """Seconds to keep events. 'window': '-30d..+60d' keeps 30 d of the past (NEO)."""
    ret = ds.get("retention") or {}
    if "window" in ret:
        past = ret["window"].split("..")[0].lstrip("-")
        return common.duration(past)
    return max(retention(ds, "events", 0), retention(ds, "events_m4.5", 0)) or None


def primary_url(ds, ctx):
    """Return (url, fallback_used) for the main request of a dataset."""
    if ds.get("alt_url") and ds.get("alt_key_secret"):
        # The key only selects the optional alternative URL (FIRMS area API).
        # The no-key URL is a full source, so the dataset stays "ok" without the key.
        env = ctx.env if ctx.env is not None else os.environ
        if env.get(ds["alt_key_secret"]):
            url, _ = common.expand_url(ds["alt_url"], ctx.now, ctx.env)
            return url, False
        url, _ = common.expand_url(ds["url"], ctx.now, ctx.env)
        return url, False
    return common.expand_url(ds["url"], ctx.now, ctx.env)


def fetch_parse(ds, url, parse, ctx, conditional=True):
    """GET url and parse it. Retry a parse error (rule 9.4a). Return (result or None if unchanged, response)."""
    hash_check = "b" in ds.get("rules", [])
    resp = ctx.client.get(url, conditional=conditional and not ctx.backfill, hash_check=hash_check)
    if resp.unchanged:
        return None, resp
    for attempt in range(PARSE_RETRIES + 1):
        try:
            return parse(ds, resp.body, ctx), resp
        except ParseError as e:
            if ctx.offline or attempt == PARSE_RETRIES:
                raise
            ctx.log(f"{ds['id']}: parse failed ({e}). Wait {PARSE_WAIT} s and fetch again.")
            ctx.sleep(PARSE_WAIT)
            resp = ctx.client.get(url, conditional=False, hash_check=False)
    raise ParseError("unreachable")


def process(ds, adapters, ctx):
    """Run one dataset. Return an outcome dict for the manifest. Never raise."""
    sid = ds["id"]
    fetcher, parse = adapters.get(ds["adapter"])
    if fetcher is None and parse is None:
        return {"status": "error", "message": f"adapter '{ds['adapter']}' is not built yet"}
    ctx = Context(ctx.clock, ctx.client, ctx.store, ctx.offline, ctx.env, ctx.log, ctx.sleep, ctx.backfill)
    degraded = False
    note = None
    try:
        if fetcher is not None:
            result = fetcher(ds, ctx)
            if result:
                degraded = bool(result.pop("degraded", False))
                note = result.pop("message", None)
            results = [result]
        else:
            url, degraded = primary_url(ds, ctx)
            urls = [url]
            if ctx.backfill:
                urls = [common.expand_url(ds[k], ctx.now, ctx.env)[0]
                        for k in ("backfill_url", "backfill_url_2") if ds.get(k)] + urls
            results = []
            for u in urls:
                result, resp = fetch_parse(ds, u, parse, ctx)
                ctx.responses.append(resp)
                results.append(result)
        if all(r is None for r in results):
            for r in ctx.responses:
                ctx.client.commit(r)
            return {"status": "degraded" if degraded else "ok", "changed": False,
                    "message": "not changed", "degraded": degraded}
        newest = None
        for result in results:
            if result is not None:
                write(ds, result, ctx)
                if result.get("newest") is not None:
                    newest = max(newest or 0, result["newest"])
        for r in ctx.responses:
            ctx.client.commit(r)
        changed = sid in ctx.store.changed
        msg = note or ("fallback without key" if degraded else None)
        return {"status": "degraded" if degraded else "ok", "changed": changed, "newest": newest,
                "message": msg, "degraded": degraded}
    except FetchError as e:
        return {"status": "error", "message": common.mask(f"fetch failed: {e}", ctx.env)}
    except ParseError as e:
        return {"status": "error", "message": common.mask(f"parse failed: {e}", ctx.env)}
    except ValidationError as e:
        sample = common.mask(repr(e.sample)[:300], ctx.env) if e.sample is not None else ""
        return {"status": "error", "message": common.mask(f"validation failed: {e}", ctx.env), "sample": sample}
    except ShrinkError as e:
        return {"status": "error", "message": f"not written: {e}"}
    except Exception as e:   # a bug in an adapter must not stop the run
        tb = traceback.format_exc(limit=3)
        ctx.log(common.mask(tb, ctx.env))
        return {"status": "error", "message": common.mask(f"{type(e).__name__}: {e}", ctx.env)}


# ----------------------------------------------------------------- write

def compact(e):
    """Drop null fields of an event record and its 'extra' (smaller files)."""
    out = {k: v for k, v in e.items() if v is not None and k != "extra"}
    extra = {k: v for k, v in (e.get("extra") or {}).items() if v not in (None, "")}
    if extra:
        out["extra"] = extra
    return out


def meta_cols(cols):
    out = []
    for c in cols:
        m = {k: v for k, v in c.items() if k != "range"}
        m["q"] = {k: v for k, v in (c.get("q") or {}).items() if k != "auto_off"}
        out.append(m)
    return out


def write_meta(ds, ctx, extra):
    meta = {"v": 1, "id": ds["id"], "title": ds["title"], "domain": ds["domain"], "kind": ds["kind"],
            "class": ds.get("class"), "tier": ds["tier"], "retention": ds.get("retention"),
            "attribution": ds.get("attribution"), "license": ds.get("license"),
            "url": common.mask(ds.get("url"), ctx.env), "dt": ds.get("dt")}
    meta.update(extra)
    ctx.store.write(ds, "meta.json", {k: v for k, v in meta.items() if v is not None})


def write(ds, result, ctx):
    store, now = ctx.store, ctx.now
    meta = {}
    latest = {"v": 1, "id": ds["id"], "kind": ds["kind"], "t": result.get("newest")}
    if "series" in result:
        s = result["series"]
        validate.series(s, now, allow_future="f" in ds.get("rules", []))
        span = raw_span(ds, s.get("dt"))
        # A derived series of a grid (example: the daily fire count) keeps 2 y.
        keep = retention(ds, "r") or (2 * 365 * DAY if ds.get("kind") == "grid" else None)
        t_range = store.merge_series(ds, "r", s["rows"], s["cols"], s.get("dt"), span,
                                     window_start=now - keep if keep else None)
        if t_range:
            rollup.update(store, ds, s["cols"], *t_range, last=s.get("last", False), dt=s.get("dt"))
        store.prune_tier(ds, "r", span, keep)
        for tier in rollup.tiers_for(ds):
            store.prune_tier(ds, tier, SUMMARY_TIERS[tier][1], retention(ds, tier))
        meta.update({"cols": meta_cols(s["cols"]), "span": span, "summary_last": s.get("last", False)})
        last = {}
        for t in sorted(s["rows"]):
            for c, v in zip(s["cols"], s["rows"][t]):
                if v is not None:
                    last[c["name"]] = [t, v]
        old = store.read(ds, "latest.json") or {}
        merged = dict(old.get("last") or {})
        for k, tv in last.items():
            if k not in merged or tv[0] >= merged[k][0]:
                merged[k] = tv
        latest["last"] = merged
    if "forecast" in result:
        f = result["forecast"]
        validate.series({"rows": f["rows"], "cols": f["cols"]}, now, allow_future=True)
        latest["issued"] = f.get("issued")
        latest["series"] = encode_series(ds["id"], f["rows"], f["cols"])
        meta["cols"] = meta_cols(f["cols"])
    if "record" in result:
        latest["record"] = result["record"]
    if "events" in result:
        ev = result["events"]
        ev["items"] = [compact(e) for e in ev["items"]]
        validate.events(ev["items"], allow_empty="g" in ds.get("rules", []) or ev.get("allow_empty", False))
        keep = event_keep(ds)
        span = "year" if "record" in (ds.get("retention") or {}) else "month"
        store.merge_events(ds, ev["items"], keep, span=span, keep_fn=event_filter(ds, ctx.now))
        if ev.get("active", True):
            store.write(ds, "active.json", {"v": 1, "id": ds["id"],
                                            "events": sorted(ev["items"], key=lambda e: -(e["t_start"] or 0))})
        latest["count"] = len(ev["items"])
        if ev["items"]:
            top = max(ev["items"], key=lambda e: (e.get("sev") or 0, e["t_start"]))
            latest["top"] = top
            latest["newest_event"] = max(ev["items"], key=lambda e: e["t_start"])
    if "text" in result:
        issue = result["text"]
        validate.text(issue)
        store.merge_text(ds, issue, retention(ds, "text", 90 * DAY))
        latest["issue"] = issue
    if "grid" in result:
        write_grid(ds, result["grid"], ctx, latest, meta)
    if latest.get("t") is None:
        old = store.read(ds, "latest.json") or {}
        latest["t"] = old.get("t")
    store.write(ds, "latest.json", latest)
    write_meta(ds, ctx, meta)


def write_grid(ds, g, ctx, latest, meta):
    store = ctx.store
    lo, hi = g.get("range", (None, None))
    validate.grid(g["values"], g["grid"], lo, hi)
    snap = gridlib.snapshot(ds["id"], g["t"], g["grid"], g["values"], g["q"], g.get("fill"))
    every = retention(ds, "snap_every", DAY)
    keep = retention(ds, "snap", 7 * DAY)
    if g["t"] <= ctx.now - keep:
        return    # older than the snapshot window: nothing to keep
    day = store.merge_grid_snapshot(ds, snap, every, keep)
    latest.update({k: snap[k] for k in ("grid", "enc", "q", "fill", "data")})
    latest["extra"] = g.get("extra") or {}
    meta.update({"unit": g.get("unit"), "grid": g["grid"], "q": g["q"], "fill": g.get("fill"),
                 "snap_every": every})
    shard = store.read(ds, f"{day}.json")
    ret = ds.get("retention") or {}
    if "d1_peak" in ret:
        vals = [gridlib.values_of(shard, s["data"]) for s in shard["snaps"]]
        peak = gridlib.combine(vals, "max")
        t0 = common.parse_iso(day)
        store.write(ds, f"d1/{day}.json", gridlib.snapshot(ds["id"], t0, g["grid"], peak, g["q"], g.get("fill")))
        prune_grid_tier(ds, store, "d1", common.duration(ret["d1_peak"]), DAY)
    for key, how in (("w1_mean", "mean"), ("w1_sum", "sum")):
        if key in ret:
            write_week(ds, store, g, common.parse_iso(day), how)
            prune_grid_tier(ds, store, "w1", common.duration(ret[key]), 7 * DAY)


def write_week(ds, store, g, t, how):
    """Weekly mean or sum of the daily snapshots (plan 6.2). The key is the Monday."""
    w0 = common.week_start(t)
    grids = []
    for i in range(7):
        shard = store.read(ds, f"{common.ymd(w0 + i * DAY)}.json")
        if shard and shard["snaps"]:
            grids.append(gridlib.values_of(shard, shard["snaps"][-1]["data"]))
    if not grids:
        return
    out = gridlib.combine(grids, how)
    snap = gridlib.snapshot(ds["id"], w0, g["grid"], out, g["q"], g.get("fill"))
    snap["days"] = len(grids)
    store.write(ds, f"w1/{common.ymd(w0)}.json", snap)


def prune_grid_tier(ds, store, tier, keep, span_seconds):
    if not keep:
        return
    cutoff = store.clock.now() - keep
    for k in store.list(ds, tier):
        if common.parse_iso(k) + span_seconds <= cutoff:
            store.remove(ds, f"{tier}/{k}.json")
