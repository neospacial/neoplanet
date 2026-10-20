"""Summary tiers: 5-minute, hourly, daily (plan 5.3).

Each summary column keeps min, mean, and max. Min and max keep the peaks.
Some datasets also keep "last". The run makes the summaries from the raw
tier before the prune (plan 5.6).
"""
from .store import SUMMARY_TIERS, raw_span

STATS = ("min", "mean", "max")


def stats_for(bucket, dt, last=False):
    """The statistics of a summary tier.

    If the bucket is not longer than the raw step, a bucket holds one value.
    Then min, mean, and max are equal, and the tier keeps the mean only
    (plan 7.2: do not store duplicate data).
    """
    if dt and bucket <= dt:
        return ("mean",)
    return STATS + (("last",) if last else ())


def summary_cols(cols, stats=STATS):
    out = []
    for c in cols:
        for s in stats:
            out.append({"name": f"{c['name']}.{s}", "unit": c.get("unit"), "q": c.get("q")})
    return out


def summarize(rows, ncols, bucket, stats=STATS):
    """Make one summary row for each bucket.

    rows: {t: [v0, v1, ...]}. Return {bucket_start: [c0.min, c0.mean, c0.max, c1.min, ...]}
    with the statistics in the order of 'stats'.
    """
    acc = {}
    for t in sorted(rows):
        b = t - t % bucket
        slot = acc.setdefault(b, [[None, 0.0, 0, None, None] for _ in range(ncols)])
        for i, v in enumerate(rows[t]):
            if v is None:
                continue
            a = slot[i]
            a[0] = v if a[0] is None or v < a[0] else a[0]
            a[1] += v
            a[2] += 1
            a[3] = v if a[3] is None or v > a[3] else a[3]
            a[4] = v
    out = {}
    for b, slot in acc.items():
        vals = []
        for a in slot:
            got = {"min": a[0], "mean": a[1] / a[2] if a[2] else None, "max": a[3], "last": a[4]}
            vals.extend(got[s] for s in stats)
        out[b] = vals
    return out


def tiers_for(ds):
    """Return the summary tiers of a dataset, in the order to build them."""
    ret = ds.get("retention") or {}
    return [t for t in ("m5", "h1", "d1") if t in ret]


def update(store, ds, cols, t_min, t_max, last=False, dt=None):
    """Rebuild the summary buckets that touch [t_min, t_max] from the raw tier.

    A column with "summary": False stays in the raw tier only.
    """
    cols = [c for c in cols if c.get("summary", True)]
    names = [c["name"] for c in cols]
    span = raw_span(ds, dt)
    for tier in tiers_for(ds):
        bucket, tspan = SUMMARY_TIERS[tier]
        stats = stats_for(bucket, dt or ds.get("dt"), last)
        a = t_min - t_min % bucket
        b = t_max - t_max % bucket + bucket - 1
        raw = store.load_rows(ds, "r", span, names, a, b)
        rows = summarize(raw, len(cols), bucket, stats)
        store.merge_series(ds, tier, rows, summary_cols(cols, stats), bucket, tspan)
