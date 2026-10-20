#!/usr/bin/env python3
"""Write docs/SOURCES.md from sources.json (plan 14.5).

Run this after each change to sources.json:
    python3 tools/sources_md.py
A test checks that docs/SOURCES.md agrees with sources.json.
"""
import json
import os
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS = [("space", "Space weather and near space"), ("geo", "Geohazards"),
           ("weather", "Global weather events"), ("ocean", "Global ocean"), ("climate", "Climate records")]
NOTE_L = "Not a US Government license. The page shows the attribution in the widget and in the footer."


def host(url):
    return urllib.parse.urlparse(url).netloc


def render(reg):
    out = ["# Data sources, attribution, and licenses", "",
           f"This file comes from `sources.json` v{reg['version']}. Do not edit it by hand. "
           "Run `python3 tools/sources_md.py`.", "",
           "This dashboard is not an official warning service. Each alert links to the official issuer.", "",
           "The pipeline uses data services only. It sends the User-Agent "
           "`public-data-dashboard/<VERSION> (+<repository URL>)` and obeys rate limits, `Retry-After`, and cache "
           "headers. Two sources use a free key. The keys are GitHub secrets (`NASA_API_KEY`, `FIRMS_MAP_KEY`). "
           "No file contains a key.", "",
           "Legend: [L] = the license is not a US Government license. Show the attribution.", ""]
    for dom, title in DOMAINS:
        rows = [d for d in reg["datasets"] if d["domain"] == dom]
        if not rows:
            continue
        out += [f"## {title}", "", "| Dataset | ID | Source | Attribution | License | Tier | Status |",
                "| --- | --- | --- | --- | --- | --- | --- |"]
        for d in rows:
            lic = d.get("license") or ""
            mark = "" if lic == "US Government work" else " [L]"
            key = f" (key: `{d['key_secret']}`)" if d.get("key_secret") else ""
            out.append(f"| {d['title']}{mark} | `{d['id']}` | {host(d['url'])}{key} | {d.get('attribution', '')} "
                       f"| {lic} | {d['tier']} | {d.get('status')} |")
        out.append("")
    out += ["## Static files", "", "| File | Source | License |", "| --- | --- | --- |"]
    for s in reg.get("static", []):
        out.append(f"| `{s['target']}` | {host(s['url'])} | {s['license']} |")
    out += ["", "## Notes on terms", "",
            f"- WDC for Geomagnetism, Kyoto (Dst): non-commercial use, attribution required. {NOTE_L}",
            f"- SILSO, Royal Observatory of Belgium: CC BY-NC 4.0. {NOTE_L}",
            f"- GDACS (EC JRC, UN OCHA): attribution required. {NOTE_L}",
            f"- Australian Bureau of Meteorology (MJO): attribution required. {NOTE_L}",
            "- This project is non-commercial (plan 17, Q5).", ""]
    return "\n".join(out)


def main():
    with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as f:
        reg = json.load(f)
    text = render(reg)
    path = os.path.join(ROOT, "docs", "SOURCES.md")
    if "--check" in sys.argv:
        with open(path, encoding="utf-8") as f:
            ok = f.read() == text
        print("docs/SOURCES.md is up to date." if ok else "docs/SOURCES.md is out of date. Run tools/sources_md.py.")
        return 0 if ok else 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
