"""Manifest and size budget (plan 5.6, 9.1 step 11, 9.3).

The page reads data/manifest.json first. For each dataset the manifest gives
the folder, the status, the times, the size, a content hash, and the list of
files in each tier. The page fetches only files that the manifest lists.
"""
import hashlib
import os

from . import common
from .common import DAY, TIER_SECONDS

MB = 1024 * 1024
STATUSES = ("ok", "stale", "degraded", "error")


def list_files(store, ds):
    """Return {tier: [file keys]} and the total size of the dataset folder."""
    base = store.dir_for(ds)
    files, total = {}, 0
    if not os.path.isdir(base):
        return files, 0
    for dirpath, dirnames, names in os.walk(base):
        dirnames.sort()
        rel = os.path.relpath(dirpath, base)
        tier = "" if rel == "." else rel.replace(os.sep, "/")
        for n in sorted(names):
            if n.startswith(".") or not n.endswith(".json"):
                continue
            total += os.path.getsize(os.path.join(dirpath, n))
            files.setdefault(tier or "root", []).append(n[:-5])
    return files, total


def content_hash(store, ds):
    """A short hash of all files of a dataset. The page fetches again when it changes."""
    h = hashlib.sha256()
    base = store.dir_for(ds)
    for dirpath, dirnames, names in sorted(os.walk(base)):
        dirnames.sort()
        for n in sorted(names):
            if n.startswith("."):
                continue
            p = os.path.join(dirpath, n)
            h.update(os.path.relpath(p, base).encode())
            with open(p, "rb") as f:
                h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()[:16]


def stale_limit(ds):
    """Seconds after which the data is stale (rule 9.4e)."""
    if ds.get("max_age_days"):
        return ds["max_age_days"] * DAY
    return 10 * TIER_SECONDS.get(ds.get("tier"), 3600)


def status_for(entry, ds, now):
    """Final status: error and degraded stay; else ok or stale by data age."""
    st = entry.get("status") or "error"
    if st in ("error", "degraded"):
        return st
    ref = entry.get("newest")
    if ds.get("kind") in ("forecast", "record") or (ds.get("kind") == "events" and not ds.get("max_age_days")):
        ref = entry.get("last_ok")
    if ref is None:
        return "error"
    return "stale" if now - ref > stale_limit(ds) else "ok"


def build(store, registry, previous, outcomes, now, version):
    """Make the manifest dict. outcomes: {id: dict} for datasets that ran now."""
    prev = (previous or {}).get("datasets", {})
    datasets = {}
    warnings = []
    total = 0
    for ds in registry["datasets"]:
        sid = ds["id"]
        entry = dict(prev.get(sid) or {})
        entry.update({
            "title": ds["title"], "domain": ds["domain"], "kind": ds["kind"], "class": ds.get("class"),
            "tier": ds["tier"], "path": store.rel_dir(ds), "attribution": ds.get("attribution"),
            "license": ds.get("license"), "budget_mb": ds.get("budget_mb"),
            "max_age_days": ds.get("max_age_days"), "retention": ds.get("retention"),
        })
        if ds.get("dt"):
            entry["dt"] = ds["dt"]
        out = outcomes.get(sid)
        if out:
            entry["status"] = out["status"]
            entry["message"] = out.get("message")
            entry["last_fetch"] = now
            if out["status"] in ("ok", "degraded"):
                entry["last_ok"] = now
            if out.get("changed"):
                entry["last_change"] = now
            if out.get("newest") is not None:
                entry["newest"] = out["newest"]
            entry["degraded"] = bool(out.get("degraded"))
        if out is None and "status" not in entry:
            entry["status"] = "error"
            entry["message"] = "not fetched yet"
        files, size = list_files(store, ds)
        entry["files"] = files
        entry["bytes"] = size
        entry["hash"] = content_hash(store, ds) if size else None
        entry["status"] = status_for(entry, ds, now)
        if ds.get("budget_mb") and size > 2 * ds["budget_mb"] * MB:
            warnings.append(f"{sid}: {size / MB:.2f} MB is more than 2 x the budget of {ds['budget_mb']} MB")
        if ds.get("sunset"):
            left = common.parse_iso(ds["sunset"]) - now
            if left < 60 * DAY:
                warnings.append(f"{sid}: the source stops on {ds['sunset']} (sunset)")
        datasets[sid] = {k: v for k, v in entry.items() if v is not None}
        total += size
    budget = registry.get("budget_total_mb", 150)
    hard = registry.get("hard_stop_mb", 300)
    stop = total > hard * MB
    if stop:
        warnings.append(f"store size {total / MB:.1f} MB is more than the hard stop of {hard} MB: deploy stopped")
    elif total > budget * MB:
        warnings.append(f"store size {total / MB:.1f} MB is more than the budget of {budget} MB")
    counts = {s: 0 for s in STATUSES}
    for e in datasets.values():
        counts[e["status"]] = counts.get(e["status"], 0) + 1
    return {
        "v": 1, "version": version, "generated": common.iso(now), "t": now,
        "budget_mb": budget, "hard_stop_mb": hard, "site_limit_mb": 1024,
        "total_bytes": total, "deploy": not stop, "warnings": warnings,
        "counts": counts, "datasets": datasets,
    }


def budget_stop(total_bytes, hard_stop_mb):
    """True if the deploy must stop (plan 5.6 size stop)."""
    return total_bytes > hard_stop_mb * MB


def summary_markdown(man, registry):
    """Run summary for GITHUB_STEP_SUMMARY: each dataset against its budget."""
    lines = [f"## Pipeline run {man['generated']}", "",
             f"Total: **{man['total_bytes'] / MB:.2f} MB** of {man['budget_mb']} MB budget "
             f"(hard stop {man['hard_stop_mb']} MB). Deploy: {'yes' if man['deploy'] else 'NO'}.", "",
             "Status: " + ", ".join(f"{k} {v}" for k, v in man["counts"].items()), ""]
    if man["warnings"]:
        lines.append("### Warnings")
        lines += [f"- {w}" for w in man["warnings"]]
        lines.append("")
    by_class = {}
    for ds in registry["datasets"]:
        e = man["datasets"].get(ds["id"], {})
        c = by_class.setdefault(ds.get("class") or "-", [0, 0.0])
        c[0] += e.get("bytes", 0)
        c[1] += ds.get("budget_mb") or 0
    lines += ["### Size by class", "", "| Class | MB | Budget MB |", "| --- | --- | --- |"]
    lines += [f"| {k} | {v[0] / MB:.2f} | {v[1]:.1f} |" for k, v in sorted(by_class.items())]
    lines += [f"| **Total** | **{man['total_bytes'] / MB:.2f}** | {man['budget_mb']} |", "", "### Datasets", ""]
    lines += ["| Dataset | Status | MB | Budget MB | Use | Message |", "| --- | --- | --- | --- | --- | --- |"]
    for ds in registry["datasets"]:
        e = man["datasets"].get(ds["id"], {})
        mb = e.get("bytes", 0) / MB
        bud = ds.get("budget_mb") or 0
        use = f"{100 * mb / bud:.0f} %" if bud else "-"
        msg = (e.get("message") or "").replace("|", "/")[:120]
        lines.append(f"| {ds['id']} | {e.get('status')} | {mb:.3f} | {bud} | {use} | {msg} |")
    return "\n".join(lines) + "\n"
