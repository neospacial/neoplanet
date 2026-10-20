"""NOAA NDBC DART tsunami buoys (plan 8.3, rule d).

Read activestations.xml once each day and use the stations with type="dart".
Skip a station after a 404 or when its newest row is more than 2 days old.
The skip list lives in data/_state/dart.json until the next station list.
"""
import os
import re
import xml.etree.ElementTree as ET

from lib import common
from lib.http import FetchError
from lib.validate import ParseError

from .base import col, num

DT = 900          # 15-minute slots; 1-minute event data goes to its slot
STALE = 2 * 86400


def stations(xml):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise ParseError(f"station list: {e}") from None
    return [{"id": s.get("id"), "lat": num(s.get("lat")), "lon": num(s.get("lon")), "name": (s.get("name") or "").strip()}
            for s in root.iter("station") if s.get("type") == "dart"]


_ROW = re.compile(r"^(\d{4}) (\d\d) (\d\d) (\d\d) (\d\d) (\d\d) (\d) +(\d+\.\d+)")


def parse_dart(text):
    out = {}
    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if m:
            y, mo, d, hh, mi, ss, _, h = m.groups()
            out[common.epoch(int(y), int(mo), int(d), int(hh), int(mi), int(ss))] = float(h)
    return out


def ndbc_dart(ds, ctx):
    now, store = ctx.now, ctx.store
    state_path = os.path.join(store.root, "_state", "dart.json")
    st = common.read_json(state_path, {}) or {}
    if not st.get("stations") or now - st.get("t", 0) >= 86400:
        resp = ctx.client.get(ds["station_list"], conditional=False)
        st = {"t": now, "stations": stations(resp.body), "skip": {}}
    rows, fresh, skipped = {}, [], []
    for s in st["stations"]:
        sid = s["id"]
        if sid in st["skip"]:
            continue
        url, _ = common.expand_url(ds["url"], now, ctx.env, {"STATION": sid})
        try:
            resp = ctx.client.get(url, conditional=False)
        except FetchError as e:
            if e.status == 404 or ctx.offline:
                st["skip"][sid] = "404" if e.status == 404 else "no fixture"
            continue
        data = parse_dart(resp.body.decode("latin-1"))
        if not data or now - max(data) > STALE:
            st["skip"][sid] = "stale"
            skipped.append(sid)
            continue
        fresh.append(s)
        k = len(fresh) - 1
        for t, h in data.items():
            if t >= now - 7 * 86400:
                rows.setdefault(t - t % DT, {})[k] = h
    common.write_json(state_path, st)
    if not fresh:
        raise FetchError(f"no fresh DART station ({len(st['skip'])} skipped: 404 or older than 2 days)")
    cols = [col(f"h_{s['id']}", "m", 1000, lo=0, hi=12000, label=f"{s['id']} {s['name']}", auto_off=True) for s in fresh]
    full = {t: [v.get(k) for k in range(len(fresh))] for t, v in rows.items()}
    return {"series": {"cols": cols, "rows": full, "dt": DT, "last": False},
            "record": {"stations": [{k: s[k] for k in ("id", "lat", "lon", "name")} for s in fresh],
                       "skipped": len(st["skip"])},
            "newest": max(full), "message": f"{len(fresh)} fresh stations, {len(st['skip'])} skipped"}
