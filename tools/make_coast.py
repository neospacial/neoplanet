#!/usr/bin/env python3
"""Make static/coast-110m.json from the Natural Earth 110m coastline (public domain).

    python3 tools/make_coast.py              # from fixtures/static.ne-110m-coastline.json
    python3 tools/make_coast.py --fetch      # from the URL in sources.json (network)

Format: {"v": 1, "scale": 10, "lines": [[lon0, lat0, dlon1, dlat1, ...], ...]}
Values are integers: degrees x scale. Each point after the first is a delta.
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 10      # 0.1 degree: more than enough for a 110m map


def quantize(geo, scale=SCALE):
    lines = []
    for f in geo["features"]:
        g = f["geometry"]
        parts = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        for part in parts:
            out, px, py = [], None, None
            for lon, lat in part:
                x, y = int(round(lon * scale)), int(round(lat * scale))
                if px is None:
                    out += [x, y]
                elif (x, y) != (px, py):
                    out += [x - px, y - py]
                px, py = x, y
            if len(out) >= 4:
                lines.append(out)
    return {"v": 1, "src": "Natural Earth 110m coastline (public domain)", "scale": scale, "lines": lines}


def main():
    with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
        st = json.load(f)["static"][0]
    if "--fetch" in sys.argv:
        req = urllib.request.Request(st["url"], headers={"User-Agent": "public-data-dashboard (+repository)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            geo = json.load(r)
    else:
        with open(os.path.join(ROOT, st["fixture"]), encoding="utf-8") as f:
            geo = json.load(f)
    out = quantize(geo)
    path = os.path.join(ROOT, st["target"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {path}: {len(out['lines'])} lines, {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main()
