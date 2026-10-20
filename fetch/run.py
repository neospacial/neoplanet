#!/usr/bin/env python3
"""Pipeline scheduler (plan 9 and 10).

Examples:
    python fetch/run.py                     # the 30m tier and each slower tier that is due
    python fetch/run.py --tier all --backfill
    python fetch/run.py --tier all --offline fixtures --now 2026-10-20T18:00:00Z
    python fetch/run.py --only space.kp,space.xray

The run writes data/, data/manifest.json, and data/_state/. It writes the
outputs 'changed', 'deploy', and 'size_mb' to GITHUB_OUTPUT when that is set.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import common, manifest as manifestlib, pipeline   # noqa: E402
from lib.common import DAY, TIER_SECONDS                     # noqa: E402
from lib.http import HttpClient, OfflineClient               # noqa: E402
from lib.store import Store                                  # noqa: E402
import adapters                                              # noqa: E402

TIERS = ("30m", "1h", "1d", "1w")
MAX_RUN_SECONDS = 8 * 60       # plan 9.2
WORKERS = 6
MB = 1024 * 1024


def load_registry(path=None):
    with open(path or os.path.join(common.ROOT, "sources.json"), encoding="utf-8") as f:
        return json.load(f)


def due_tiers(last, now):
    """Return the tiers to run in an automatic run (plan 10.1)."""
    out = ["30m"]
    if now - (last.get("1h") or 0) >= 55 * 60:
        out.append("1h")
    d0 = common.day_start(now)
    if now >= d0 + 5 * 3600 and (last.get("1d") or 0) < d0 + 5 * 3600:
        out.append("1d")
    w0 = common.week_start(now) + 5 * 3600
    if now >= w0 and (last.get("1w") or 0) < w0:
        out.append("1w")
    return out


def select(registry, tiers, only=None):
    prefixes = [p.strip() for p in (only or "").split(",") if p.strip()]
    out = []
    for ds in registry["datasets"]:
        if ds["tier"] not in tiers:
            continue
        if prefixes and not any(ds["id"].startswith(p) for p in prefixes):
            continue
        out.append(ds)
    return out


def fixture_map(registry, now, env):
    """URL -> fixture path, for --offline."""
    m = {}
    for ds in registry["datasets"]:
        if not ds.get("fixture"):
            continue
        extra = {}
        if ds.get("observatories"):
            extra["OBS"] = ds["observatories"][0]     # the fixture is from the first observatory
        station = re.search(r"-(\w+)\.\w+$", ds["fixture"]) if "{STATION}" in ds["url"] else None
        if station:
            extra["STATION"] = station.group(1)       # example: fixtures/ndbc.dart-21414.txt
        for key in ("url", "alt_url", "backfill_url", "backfill_url_2"):
            if ds.get(key):
                m[common.expand_url(ds[key], now, env, extra)[0]] = ds["fixture"]
        if ds.get("station_list") and ds.get("station_list_fixture"):
            m[ds["station_list"]] = ds["station_list_fixture"]
    for st in registry.get("static", []):
        if st.get("fixture"):
            m[st["url"]] = st["fixture"]
    return m


def restore_from_site(base_url, data_dir, ua, log=print):
    """Plan 4.3: download data/ from the live site when the cache is empty."""
    base = base_url.rstrip("/") + "/data/"

    def get(rel):
        req = urllib.request.Request(base + rel, headers={"User-Agent": ua})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()

    try:
        man = json.loads(get("manifest.json"))
    except Exception as e:
        log(f"restore: no manifest on the live site ({type(e).__name__}). Start with an empty store.")
        return 0
    count = 0
    for sid, e in man.get("datasets", {}).items():
        for tier, names in (e.get("files") or {}).items():
            for n in names:
                rel = f"{e['path']}/{'' if tier == 'root' else tier + '/'}{n}.json"
                try:
                    common.atomic_write_bytes(os.path.join(data_dir, rel), get(urllib.parse.quote(rel)))
                    count += 1
                except Exception as ex:
                    log(f"restore: {rel} failed ({type(ex).__name__})")
    common.atomic_write_bytes(os.path.join(data_dir, "manifest.json"), json.dumps(man).encode())
    log(f"restore: {count} files from {base}")
    return count


def write_outputs(values):
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        for k, v in values.items():
            f.write(f"{k}={v}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Public Data Dashboard pipeline")
    ap.add_argument("--tier", default="auto", choices=("auto", "all") + TIERS,
                    help="auto = 30m and each slower tier that is due")
    ap.add_argument("--backfill", action="store_true", help="read the longest windows (plan 4.4)")
    ap.add_argument("--only", default="", help="comma-separated dataset ID prefixes")
    ap.add_argument("--offline", metavar="DIR", help="read fixtures from DIR, not the network")
    ap.add_argument("--now", help="freeze the clock (ISO time, UTC)")
    ap.add_argument("--data", default=os.path.join(common.ROOT, "data"), help="store folder")
    ap.add_argument("--sources", default=None, help="path of sources.json")
    ap.add_argument("--restore-from", default="", help="live site URL for the fallback store (plan 4.3)")
    args = ap.parse_args(argv)

    start = time.monotonic()
    clock = common.Clock(common.parse_iso(args.now) if args.now else None)
    now = clock.now()
    registry = load_registry(args.sources)
    version = common.read_version()
    state_dir = os.path.join(args.data, "_state")
    http_state = common.read_json(os.path.join(state_dir, "http.json"), {})
    run_state = common.read_json(os.path.join(state_dir, "run.json"), {"last": {}})

    if args.restore_from and not os.path.exists(os.path.join(args.data, "manifest.json")):
        restore_from_site(args.restore_from, args.data, common.user_agent(registry.get("user_agent")))

    if args.offline:
        client = OfflineClient(args.offline, fixture_map(registry, now, os.environ))
    else:
        client = HttpClient(http_state, common.user_agent(registry.get("user_agent")),
                            deadline=time.monotonic() + MAX_RUN_SECONDS)
    store = Store(args.data, clock)
    ctx = pipeline.Context(clock, client, store, offline=bool(args.offline), backfill=args.backfill)

    if args.tier == "all":
        tiers = list(TIERS)
    elif args.tier == "auto":
        tiers = due_tiers(run_state.get("last", {}), now)
    else:
        tiers = [args.tier]
    chosen = select(registry, tiers, args.only)
    print(f"public-data-dashboard {version}: run at {common.iso(now)}, tiers {','.join(tiers)}, "
          f"{len(chosen)} datasets{' (offline)' if args.offline else ''}{' (backfill)' if args.backfill else ''}")

    previous = common.read_json(os.path.join(args.data, "manifest.json"), {})
    outcomes = {}
    workers = 1 if args.offline else WORKERS
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for ds in chosen:
            futures[pool.submit(_run_one, ds, ctx, start, args.offline)] = ds
        for fut in cf.as_completed(futures):
            ds = futures[fut]
            out = fut.result()
            if out is None:
                print(f"  {ds['id']:<28} skipped: run time limit")
                continue
            outcomes[ds["id"]] = out
            msg = f" ({out['message']})" if out.get("message") else ""
            print(f"  {ds['id']:<28} {out['status']}{msg}")

    man = manifestlib.build(store, registry, previous, outcomes, now, version)
    status_changed = any((previous.get("datasets", {}).get(k, {}).get("status") != v["status"])
                         for k, v in man["datasets"].items())
    common.write_json(os.path.join(args.data, "manifest.json"), man)
    if not args.offline:
        common.write_json(os.path.join(state_dir, "http.json"), client.state)
    last = run_state.setdefault("last", {})
    for t in tiers:
        last[t] = now
    common.write_json(os.path.join(state_dir, "run.json"), run_state)

    total = man["total_bytes"]
    changed = bool(store.changed) or status_changed
    print(f"Total store size: {total / MB:.2f} MB ({total} bytes). Budget {man['budget_mb']} MB, "
          f"hard stop {man['hard_stop_mb']} MB.")
    print("Status: " + ", ".join(f"{k} {v}" for k, v in man["counts"].items()))
    for w in man["warnings"]:
        print(f"WARNING: {w}")
    if not man["deploy"]:
        print("STOP: the store is larger than the hard stop. The deploy does not run.")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(manifestlib.summary_markdown(man, registry))
            for sid, out in outcomes.items():
                if out.get("sample"):
                    f.write(f"\nSample for {sid}: `{out['sample']}`\n")
    write_outputs({"changed": str(changed).lower(), "deploy": str(man["deploy"] and changed).lower(),
                   "size_mb": f"{total / MB:.2f}"})
    return 0


def _run_one(ds, ctx, start, offline):
    if not offline and time.monotonic() - start > MAX_RUN_SECONDS:
        return None
    return pipeline.process(ds, adapters, ctx)


if __name__ == "__main__":
    sys.exit(main())
