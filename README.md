# Public Data Dashboard

One page that shows the state of the planet and near space. The page shows global trends and large global events from free public data services: space weather, earthquakes and other hazards, storms and fires, the ocean, and climate records.

This dashboard is not an official warning service. Each alert links to the official issuer.

## How it works

1. A scheduled GitHub Actions workflow (`.github/workflows/run.yml`) runs every 30 minutes.
2. The workflow runs `fetch/run.py`. The script fetches each dataset in `sources.json` on its tier (30 min, 1 h, 1 d, or 1 w).
3. The script keeps a rolling store of quantized JSON files in `data/`. Each dataset has a fixed retention window. Old files are deleted.
4. The store lives in the GitHub Actions cache, not in git. The repository holds code only.
5. The workflow publishes `index.html`, `static/`, and `data/` to GitHub Pages.
6. The page (`index.html`) reads only files from the same site. It does not connect to external APIs.

```
[Source APIs] -> [fetch/run.py in Actions] <-> [Actions cache: store]
                          |
                          v
               [upload-pages-artifact] -> [deploy-pages]
                          |
                          v
[Browser: index.html] <- same-origin JSON <- <user>.github.io/<repo>/
```

## Widgets

| ID | Widget | Data |
| --- | --- | --- |
| W1 | Scale badges | NOAA R, S, G: now, 24 h maximum, 3-day forecast |
| W2 | Time series | Any series dataset. Log axis, thresholds, min/max band for summary tiers |
| W3 | Kp bars | Planetary Kp in G-level colors, forecast hatched |
| W4 | Solar wind stack | Bz (southward shaded), Bt, speed, density |
| W5 | Aurora polar view | OVATION 2 degree grid, both hemispheres, 7-day slider |
| W6 | World event map | Earthquakes, GDACS, cyclone tracks, EONET, tsunami messages, fire density, night side. Zoom and pan; click or tap an event for its details |
| W7 | Event list | Sorted by severity, then time. A click shows the event on the map. When the map is zoomed in, the list shows only the events in the map view |
| W8 | Event timeline | One lane for each event type |
| W9 | Calendar heat map | Daily maximum Kp, M4.5+ count, fire count |
| W10 | Climate trend | Full record, 12-month mean, trend line, seasonal overlay |
| W11 | Big number | Value, sparkline, change from 24 h and 1 y, percentile |
| W12 | Text | SWPC discussion, forecasts, and alerts |
| W13 | Data health | Status, age, size, and budget of each dataset |
| W14 | Near-Earth objects | Close approaches in lunar distances, Sentry list |
| W15 | Solar cycle | Sunspot number and F10.7 with the prediction |
| W16 | Ocean anomaly map | SST or sea level anomaly, Nino 3.4 box, time slider. Zoom and pan |

Presets: Overview (default), Space Weather, Earth Events, Ocean and Climate. Drag the grip to move a widget, drag the corner to resize it, or use Alt + arrow keys (Alt + Shift + arrow keys to resize). Open **Widgets** to add or remove widgets, and to export or import the layout. Drag on the time strip below the header to select a time window. Double-click it to return to live mode.

Maps: scroll the mouse wheel, double-click, or use the + and − buttons to zoom. Drag to pan. On a phone or tablet, pinch with two fingers to zoom and pan; one finger scrolls the page. With the keyboard, select the map and use + and − to zoom, the arrow keys to pan, and 0 to show the whole world. Click or tap an event to show its details and a link to the official source.

## Setup

The owner does some steps by hand: turn on GitHub Pages, give the workflow write access, add the API key as a repository secret, and start the first run. See [`docs/OPERATIONS.md`](docs/OPERATIONS.md), section 0.

Both keys are optional:

| Secret name | Without the key |
| --- | --- |
| `NASA_API_KEY` | The pipeline uses `DEMO_KEY` (10 requests each hour). The DONKI datasets show status "degraded". |
| `FIRMS_MAP_KEY` | The pipeline uses the no-key 24-hour fire file. No data is lost. The status stays "ok". |

## Repository layout

| Path | Content |
| --- | --- |
| `index.html` | The dashboard page (one file, no libraries) |
| `sources.json` | The registry of datasets: URL, adapter, tier, retention, budget, rules |
| `fetch/run.py` | The scheduler. It runs the tiers that are due. |
| `fetch/lib/` | HTTP client, store, summaries, grids, checks, manifest, the procedure for one dataset |
| `fetch/adapters/` | One adapter for each source family |
| `fetch/tests/` | Tests. They read `fixtures/` only and need no network. |
| `fixtures/` | Real source responses from the Phase 0 audit (trimmed) |
| `static/coast-110m.json` | Natural Earth coastlines, quantized (`tools/make_coast.py`) |
| `tools/audit/` | The Phase 0 endpoint audit (`audit.yml`) |
| `tools/sources_md.py` | Writes `docs/SOURCES.md` from `sources.json` |
| `tools/serve.py` | Development server with fixture data |
| `tools/check_page.js` | Development check of the page with a headless browser |
| `docs/SOURCES.md` | Attribution and license for each dataset |
| `KEEPALIVE.txt` | One line each month. It keeps the schedule active. |

## Run it on your computer

You need Python 3.11 or later. No packages.

```sh
# Run all tests (no network)
python3 -m unittest discover -s fetch/tests

# Fill data/ from the fixtures, with a frozen clock
python3 fetch/run.py --tier all --offline fixtures --now 2026-10-20T18:00:00Z

# Fetch from the real sources (network)
python3 fetch/run.py --tier all --backfill
```

Open the page with fixture data:

```sh
python3 tools/serve.py
# then open http://localhost:8000/?now=2026-10-20T18:00:00Z
```

The page parameter `?now=` freezes the page clock. The fixtures are from 2026-10-20, so without it the page shows the data as stale.

Optional page check with a headless browser (needs Node.js and Playwright, for development only):

```sh
node tools/check_page.js http://localhost:8000/ page-check
```

It checks for console errors, the first load size, and that the CSP blocks external requests. It writes screenshots at 360, 1280, and 1920 px width.

Options of `fetch/run.py`:

| Option | Effect |
| --- | --- |
| `--tier {auto,all,30m,1h,1d,1w}` | `auto` runs 30m and each slower tier that is due. |
| `--backfill` | Read the longest source windows (plan 4.4). |
| `--only <prefixes>` | Run only datasets whose ID starts with one of the comma-separated prefixes. |
| `--offline <dir>` | Read each dataset from its fixture file, not from the network. |
| `--now <ISO time>` | Freeze the clock (for tests). |
| `--data <dir>` | Store folder (default `data/`). |

## Limits

| Item | Value |
| --- | --- |
| Store size budget | 150 MB raw. The run writes a warning above it. |
| Hard stop | 300 MB. The run stops the deploy above it. |
| Run time | 8 minutes maximum for the fetch step |
| Requests | 2 parallel requests to one host, 30 s timeout, retries after 5, 20, and 60 s |

## Operations

See [`docs/OPERATIONS.md`](docs/OPERATIONS.md): how to read the data health widget, how to replace a broken URL with `audit.yml`, and how to rotate a key.

## Data sources

See [`docs/SOURCES.md`](docs/SOURCES.md). Some sources need attribution (WDC Kyoto, SILSO, GDACS, BoM). The page shows it.

## Version

The version is in `VERSION`, in `<meta name="version">` of `index.html`, and in the page footer.
