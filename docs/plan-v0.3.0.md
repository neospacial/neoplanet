# Public Data Dashboard - Implementation Plan v0.3.0

Oct 20, 2026 · Ryan

The dashboard keeps a rolling history of global public data in approx. 126 MB (measured in Phase 0). Data is never committed to git, thus the repository stays small. Phase 0 is done; Phase 1 is next. Written in ASD-STE100 Simplified Technical English.

## Changes from 0.2.2

- Phase 0 is complete. 81 of 90 candidate endpoints work (audit v0.1.1, 2026-10-20). Section 18 gives the results.
- All [V] marks are removed. Section 8 now gives the verified URL and the status of each source.
- Aurora grid: 2 degree cells and one snapshot each hour. The size goes from 33.9 MB to 4.6 MB (section 6).
- New grids from the audit: sea level anomaly (ERDDAP `nesdisSSH1day`) and coral bleaching alert (ERDDAP `NOAA_DHW`).
- Replaced URLs: SWPC solar wind, SWPC 45-day forecast, GDACS, USGS volcano, NSIDC sea ice, NDBC DART.
- Removed sources: Smithsonian GVP (403 for automated requests), CCMC Kauai DONKI copy (connection reset).
- Section 6.4 now uses measured sizes. The total is approx. 126 MB against the 150 MB budget.
- Section 9 adds five adapter rules that the audit found.
- Section 10.4 tells where to enter the two API keys as GitHub secrets.
- New files for the build: `sources.json` v0.3.0 and `fixtures/`.

**Legend for section 8**

| Status | Meaning |
| --- | --- |
| OK | Verified by the audit on 2026-10-20. |
| Key | Works only with a free key in GitHub Secrets. The pipeline uses a fallback until you add the key. |
| Runner | Failed from the audit workspace (cloud IP). Test again on the GitHub runner. The pipeline marks the dataset "error" if it fails there too. |
| [L] | The license is not a US Government license. Show the attribution. |

## 1. Scope

1. One page (`index.html`) shows public data from many domains.
2. The page does not connect to external APIs.
3. GitHub Actions fetches the data and publishes it as static files.
4. The dashboard shows global trends and large global events. It does not show local weather.
5. No images. The page draws all visuals from data.
6. The dashboard keeps recent history only. Each dataset has a fixed retention window. Data older than the window is deleted.

## 2. Decisions

| Item | Decision |
| --- | --- |
| Host | GitHub Pages. Public repository. |
| Page file | `index.html`. Version in `<meta name="version">`, in the file `VERSION`, and in the page footer. |
| Fetch cadence | 30 min, 1 h, 1 d, or 1 w. The source update rate sets the cadence (section 8). |
| Retention | A fixed window for each dataset (section 6). Long windows are kept only as summaries. |
| Excluded | No images. No push notifications. No local weather. |
| Sources | All sources that are free of cost. Two sources use a free key (NASA, FIRMS). |
| Keys | GitHub repository secrets only (section 10.4). Never in a file. |
| Page code | No libraries. No build step. |
| Fetch scripts | Python 3, standard library only. ERDDAP gives CSV and JSON, thus no GRIB or NetCDF decoder is necessary. |
| Aurora grid | 2 degree cells, one snapshot each hour, 7 days. Daily peak at 2 degrees for 90 days. |
| Language | Documents, comments, and page text use ASD-STE100 Simplified Technical English. |

## 3. The real limits

The 1 GB published site is the limit that applies to the data. The repository limit is not a problem if data is never committed.

| Limit | Value | Effect on this plan |
| --- | --- | --- |
| Repository size | 1 GB recommended | Git keeps each old version of a committed file. Thus never commit data. The repository stays less than 5 MB. |
| Published site | 1 GB maximum | Budget 150 MB raw (15 %). Hard stop 300 MB. Each deploy uploads the full site. A deploy stops after 10 min. |
| Bandwidth | 100 GB each month (soft) | Visitors use it. The workflow must not use it (section 4). |
| Schedule interval | 5 min minimum | This plan uses 30 min. Do not use minute 0. Runs can start late or be dropped. |
| Inactivity | 60 days | GitHub disables schedules in a public repository with no activity. A monthly keep-alive commit prevents this (10.5). |

**Bandwidth calculation**

- GitHub Pages sends JSON with gzip. Quantized integer JSON compresses approx. 3 to 5 times. Verify in Phase 0.
- First page load target: less than 300 KB transferred. 100 GB / 300 KB = approx. 330,000 first loads each month.
- An open tab polls the manifest once each 30 minutes. With ETag, an unchanged file costs approx. 0.3 KB. One tab for 24 hours: approx. 1 MB.
- Conclusion: bandwidth is safe if the page fetches only the data for the visible widgets and the selected time range.

## 4. Where the data lives

The data store lives in the GitHub Actions cache. Branch `main` holds code only.

### 4.1 Branch main (code only)

```
index.html
VERSION
sources.json            Registry of datasets (9.3)
KEEPALIVE.txt           One line each month (10.5)
README.md
docs/
  plan.md               This plan
  SOURCES.md            Attribution and license for each source
fetch/
  run.py                Scheduler. Runs the tiers that are due.
  lib/http.py           Conditional GET, User-Agent, backoff, retry on parse error
  lib/store.py          Merge, prune, quantize, atomic write
  lib/rollup.py         Make 5-min, hourly, daily, weekly tiers
  lib/grid.py           Regrid, quantize, sparse encode
  lib/validate.py       Schema and range checks
  lib/manifest.py       Manifest and size budget
  adapters/<name>.py    One adapter for each source family
  tests/                One test for each adapter
fixtures/               Real source responses from the Phase 0 audit (trimmed)
static/coast-110m.json  Natural Earth coastlines (public domain), quantized
tools/audit/            Phase 0 audit tool (audit.py, endpoints.json)
.github/workflows/      run.yml, test.yml, audit.yml
```

### 4.2 Primary state store: Actions cache

1. Each run restores the newest cache entry with the key prefix `store-`.
2. The run merges new data and prunes old data.
3. The run saves the store as a new entry `store-<run_id>`. Cache entries cannot be changed, thus each save is a new entry.
4. The run deletes old `store-` entries. It keeps the 3 newest.

Limit: 10 GB for each repository. Entries that are not used for 7 days are removed. The 30-minute runs use the newest entry, thus it stays.

### 4.3 Fallback state store: the live site

If no cache entry exists, the run downloads `data/` from the live Pages site one time. This uses approx. 40 MB of bandwidth (gzip). Use it only as a fallback.

### 4.4 Recovery

If the cache and the site are both lost, run the backfill procedure. It reads the longest windows that each source gives (example: SWPC 7-day files, USGS 30-day feed, full climate records). Some history is then lost. This is acceptable for a rolling store.

### 4.5 Data flow

```
[Source APIs] -> [run.py in Actions] <-> [Actions cache: store]
                         |
                         v
              [upload-pages-artifact] -> [deploy-pages]
                         |
                         v
[Browser: index.html] <- same-origin JSON <- <user>.github.io/<repo>/
```

## 5. Data store format

All data is quantized integer JSON in small shards. Raw files are split by day, so pruning is a file delete.

### 5.1 Layout

```
data/
  manifest.json
  _state/http.json          ETag and Last-Modified for each URL (not published)
  <domain>/<dataset>/
    meta.json               Units, columns, scales, source, license, cadence, retention
    latest.json             Last values and status
    r/<YYYY-MM-DD>.json     Raw resolution, one file each day
    m5/<YYYY-MM>.json       5-minute summary (fast series only)
    h1/<YYYY-MM>.json       Hourly summary
    d1/all.json             Daily summary, one file
    w1/all.json             Weekly summary (grids only)
  events/<dataset>/
    active.json
    <YYYY-MM>.json
  grids/<dataset>/
    latest.json
    <YYYY-MM-DD>.json       All snapshots of one day
```

### 5.2 Time series shard

```json
{
  "v": 1, "id": "space.goes.xray",
  "t0": 1792108800, "dt": 60, "n": 1440,
  "cols": { "short": [ ... ], "long": [ ... ] },
  "q": { "short": { "type": "log10", "scale": 1000 },
         "long":  { "type": "log10", "scale": 1000 } }
}
```

- `t0` is Unix seconds, UTC. Value i is at `t0 + i * dt`.
- A missing value is `null`. Do not interpolate.
- Irregular series: add `"t"` with delta-encoded seconds.
- Quantize to integers. Use the smallest scale that keeps the instrument precision. Examples: Kp x 100, Bz nT x 10, speed km/s x 1, density x 10.
- Values over many decades: `round(log10(value) x 1000)`.

### 5.3 Summary shards (m5, h1, d1)

- Columns for each variable: min, mean, max. Add "last" where the current value is important (example: Kp).
- Min and max keep the peaks. A flare or a storm stays visible in the summary.

### 5.4 Grid shard

```json
{
  "v": 1, "id": "ocean.sst.anom", "t": 1792108800,
  "grid": { "lat0": -89.5, "lon0": -179.5, "d": 1.0, "nlat": 180, "nlon": 360 },
  "enc": "sparse-rle", "q": { "scale": 100 },
  "data": [ ... ]
}
```

- Grids are regridded to 1 degree or coarser.
- Encoding: run-length for long runs (land, zero values), then values. Land cells and zero aurora cells cost almost nothing.

### 5.5 Event record

```json
{ "id", "t_start", "t_end", "lat", "lon", "type", "sev", "mag", "title", "src", "url", "extra": { } }
```

`sev` is a normalized severity from 0 to 5. Each adapter maps its source scale (GDACS, PAGER, Saffir-Simpson, NOAA R/S/G) to `sev`.

### 5.6 Rules

| Rule | Procedure |
| --- | --- |
| Merge | Each fetch reads a window of at least 4 x cadence. New values replace old values at the same timestamp. A late or dropped run thus causes no gap. |
| Prune | After the merge, delete files older than the retention window of each tier. Make the summaries before the prune, so that data goes into the next tier before the raw file is deleted. |
| Never shrink | A new shard must contain all old timestamps that are still inside the window. If not, do not write it. Set status "error". |
| Atomic write | Write to a temporary file, then rename it. |
| Size stop | If the store is more than 300 MB, stop the deploy and set a global warning. |

## 6. Retention and storage budget

The measured store is approx. 126 MB raw (approx. 35 to 40 MB gzip). This is 84 % of the 150 MB budget and 13 % of the 1 GB site limit. The weekly ocean summaries are the largest item.

### 6.1 Retention classes

| Class | Data type | Raw | 5-min | Hourly | Daily |
| --- | --- | --- | --- | --- | --- |
| A | Fast physical series (1-minute data) | 7 d | 30 d | 1 y | 5 y |
| B | Slow indices (Kp, Dst, F10.7, hemispheric power) | 2 y | - | - | 5 y |
| C | Global grids | see 6.2 | | | |
| D | Events | see 6.3 | | | |
| E | Climate records | Full record (fixed, small) | | | |
| F | Text products | 90 d | | | |

Reasons for these windows:

- 7 days of 1-minute data shows each flare, shock, and storm in detail. SWPC gives 7-day files, thus a gap can be filled.
- 30 days at 5 minutes covers one solar rotation (approx. 27 days). You can see if an active region or a coronal hole returns.
- 1 year hourly shows the seasonal pattern and all storms of the year with their peaks.
- 5 years daily covers half a solar cycle at a small cost (approx. 1,800 rows for each column).

### 6.2 Grid retention

| Grid | Cell size | Snapshots | Summary |
| --- | --- | --- | --- |
| Aurora (OVATION) | 2 deg (max of the 4 source cells) | Each hour, 7 d | Daily peak, 90 d |
| SST anomaly (OISST v2.1 NRT) | 1 deg (ERDDAP stride 4) | Daily, 90 d | Weekly mean, 2 y |
| Sea level anomaly (nesdisSSH1day) | 1 deg (ERDDAP stride 4) | Daily, 90 d | Weekly mean, 2 y |
| Coral bleaching alert, 7-day max (NOAA_DHW) | 2 deg (ERDDAP stride 40) | Daily, 90 d | - |
| Fire density (FIRMS VIIRS) | 1 deg cell counts | Daily, 90 d | Weekly sum, 2 y |

Aurora rule: each 2 degree cell keeps the maximum of its four 1 degree source cells. The maximum keeps the edge of the oval visible. The pipeline also keeps the hemispheric power series (class B, 2 y), so the hourly grid loses almost no information.

### 6.3 Event retention

| Event set | Window |
| --- | --- |
| Earthquakes M2.5+ | 1 year |
| Earthquakes M4.5+ | 5 years |
| GDACS, EONET, cyclone tracks | 2 years |
| Tsunami and volcano messages | 2 years |
| SWPC alerts | 1 year |
| DONKI CME, flare, SEP, storms | 2 years |
| NEO close approaches | -30 d to +60 d (moving window) |
| Fireballs, Sentry list | Full list (small) |

### 6.4 Size table (measured 2026-10-20, raw JSON, quantized integers)

| Item | Raw MB | Basis |
| --- | --- | --- |
| SST + sea level weekly mean, 2 y | 41.1 | 43,063 + 35,890 ocean cells x 104 weeks |
| SST anomaly, daily, 90 d | 19.4 | 43,063 cells measured |
| Sea level anomaly, daily, 90 d | 16.2 | 35,890 cells measured |
| Earthquakes (M2.5+ 1 y, M4.5+ 5 y) | 7.1 | 6.1 and 2.6 KB/day measured |
| Fire density, daily 90 d + weekly 2 y | 5.9 | 3,860 cells/day measured |
| Class A hourly min/mean/max, 1 y | 5.5 | from the measured raw rate |
| Coral bleaching alert, 2 deg, 90 d | 4.8 | estimate (host blocked in the audit workspace) |
| Aurora grid, 2 deg, hourly, 7 d | 4.6 | 5,415 non-zero cells measured (was 33.9 MB at 1 deg, 30 min) |
| GDACS, EONET, cyclones, DONKI, 2 y | 3.5 | measured, DONKI estimated |
| Climate records (full) | 3.0 | measured row counts |
| Aurora grid, 2 deg, daily peak, 90 d | 2.4 | 5,415 cells x 90 |
| Class B indices, 2 y | 2.4 | hemispheric power is 2.1 of this |
| Class A raw, 7 d | 2.1 | solar wind, X-ray, particles, magnetometers, 3 ground stations, DART |
| SWPC alerts, flares, solar regions | 1.9 | measured |
| Class A 5-min, 30 d | 1.8 | from the measured raw rate |
| Text products, 90 d | 1.5 | measured |
| Class A daily min/mean/max, 5 y | 1.1 | from the measured raw rate |
| NEO, fireballs, Sentry | 0.8 | measured |
| index.html, coastlines, manifest | 0.4 | coastlines 137 KB raw |
| **Total** | **approx. 126** | 150 MB budget, 300 MB hard stop |

### 6.5 Use of the headroom

Approx. 24 MB stays free. Use it in this order. Do not go past 150 MB without a new plan version.

1. Longer Class A raw window: 14 d (+2 MB).
2. Longer aurora hourly window: 14 d (+4.6 MB).
3. More DART stations (each fresh station adds approx. 0.03 MB for 7 d).

## 7. Information value for each byte

Indices, events, and climate records give the most information for the least space. Grids cost the most.

### 7.1 Rank of datasets

| Rank | Dataset | Cost | Why it is valuable |
| --- | --- | --- | --- |
| 1 | NOAA R/S/G scales, alerts | Tiny | One look gives the space weather state. |
| 2 | Kp, Dst, F10.7, sunspots | Tiny | Main global indices. |
| 3 | Climate records (CO2, sea ice, ENSO, temp. anomaly) | Small | Long trends. A full record for less than 3 MB. |
| 4 | Earthquakes, GDACS, EONET, cyclones, tsunami, volcano | Small | All large global hazards, with location. |
| 5 | Solar wind, X-ray, protons (1-min) | Small | Cause of storms. 1-min data is cheap. |
| 6 | Fire density grid | Small | Sparse. Strong seasonal signal. |
| 7 | SST and sea level anomaly | Medium | Global ocean state: El Nino, marine heat waves. |
| 8 | Aurora grid | Medium | Visual. The hemispheric power series gives most of the information. |

### 7.2 Rules that increase information for each byte

- Quantize to the instrument precision. Do not store float text.
- Keep min and max in summaries. Peaks are the important events.
- Regrid fields to 1 or 2 degrees. The dashboard is global. Finer cells add bytes but no visible detail.
- Sparse-encode grids. Aurora and fire grids are mostly empty.
- Store derived scalars next to grids (examples: global mean SST anomaly, Nino 3.4 box mean, total fire count, hemispheric power). A scalar series is very cheap and shows the trend.
- Do not store data that the page can calculate (day/night line, sun position, moon phase).
- Do not store duplicate data. Example: keep the 1-minute Kp estimate for 7 d only. Keep the official 3-hour Kp for 2 y.

## 8. Data sources and fetch tiers

The audit verified 81 endpoints. This section lists the sources that the pipeline uses. `sources.json` v0.3.0 holds the same list in machine form. Tiers: 30m, 1h, 1d, 1w. Class: see 6.1.

### 8.1 Space weather: NOAA SWPC (services.swpc.noaa.gov, no key)

| Dataset | Path | Tier | Class | Status |
| --- | --- | --- | --- | --- |
| NOAA scales R/S/G | `products/noaa-scales.json` | 30m | B | OK |
| Alerts, watches, warnings | `products/alerts.json` | 30m | D | OK |
| Planetary Kp (3 h) | `products/noaa-planetary-k-index.json` | 30m | B | OK |
| Estimated Kp, 1-min | `json/planetary_k_index_1m.json` | 30m | A (7 d) | OK |
| Kp forecast | `products/noaa-planetary-k-index-forecast.json` | 1h | Latest only | OK |
| GOES X-ray, 1-min | `json/goes/primary/xrays-1-day.json` (backfill `xrays-7-day.json`) | 30m | A | OK |
| GOES X-ray flare list | `json/goes/primary/xray-flares-7-day.json` | 1h | D | OK |
| GOES integral protons, 5-min | `json/goes/primary/integral-protons-1-day.json` | 30m | A | OK (retry rule 9.4) |
| GOES integral electrons, 5-min | `json/goes/primary/integral-electrons-1-day.json` | 30m | A | OK |
| GOES magnetometer, 1-min | `json/goes/primary/magnetometers-1-day.json` | 30m | A | OK |
| Solar wind plasma, 1-min | `json/rtsw/rtsw_wind_1m.json` | 30m | A | OK (filter rule 9.4) |
| Solar wind magnetic field, 1-min | `json/rtsw/rtsw_mag_1m.json` | 30m | A | OK (filter rule 9.4) |
| OVATION aurora grid | `json/ovation_aurora_latest.json` | 1h | C | OK |
| Hemispheric power | `text/aurora-nowcast-hemi-power.txt` | 30m | B | OK |
| Dst (WDC Kyoto via SWPC) [L] | `products/kyoto-dst.json` | 1h | B | OK |
| WSA-Enlil time series | `json/enlil_time_series.json` | 1h | Latest only | OK |
| 3-day forecast | `text/3-day-forecast.txt` | 1h | F | OK |
| Forecast discussion | `text/discussion.txt` | 1h | F | OK |
| 27-day outlook | `text/27-day-outlook.txt` | 1d | F | OK |
| F10.7 cm flux | `products/10cm-flux-30-day.json` | 1d | B | OK |
| 45-day Ap and F10.7 forecast | `json/45-day-forecast.json` | 1d | Latest only | OK |
| Flare probabilities | `json/solar_probabilities.json` | 1d | Latest only | OK |
| Solar regions | `json/solar_regions.json` | 1d | D | OK |
| Solar cycle observed | `json/solar-cycle/observed-solar-cycle-indices.json` | 1w | E | OK |
| Solar cycle predicted | `json/solar-cycle/predicted-solar-cycle.json` | 1w | Latest only | OK |

### 8.2 Space and near-Earth: other

| Dataset | Source | Tier | Class | Status |
| --- | --- | --- | --- | --- |
| NASA DONKI CME, FLR, GST, notifications | `api.nasa.gov/DONKI/...&api_key={NASA_API_KEY}` | 1h | D | Key (DEMO_KEY allows 10 requests/hour) |
| JPL close approaches | `ssd-api.jpl.nasa.gov/cad.api` | 1d | D | OK |
| JPL fireballs | `ssd-api.jpl.nasa.gov/fireball.api` | 1d | E | OK |
| JPL Sentry | `ssd-api.jpl.nasa.gov/sentry.api` | 1d | E | OK |
| USGS Geomagnetism, BOU + FRD + HON, 1-min | `geomag.usgs.gov/ws/data/?id=<obs>&elements=H,D,Z&sampling_period=60&type=variation&format=json` | 1h | A | OK (BOU verified) |
| SILSO daily sunspot number [L] | `www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv` | 1w | E | OK |
| SILSO estimated daily number [L] | `www.sidc.be/SILSO/DATA/EISN/EISN_current.csv` | 1d | B | OK |

### 8.3 Geohazards (global)

| Dataset | Source | Tier | Class | Status |
| --- | --- | --- | --- | --- |
| USGS earthquakes M2.5+ | `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson` (backfill `2.5_month`, `4.5_month`) | 30m | D | OK |
| Tsunami messages NTWC, PTWC | `www.tsunami.gov/events/xml/PAAQAtom.xml`, `PHEBAtom.xml` | 30m | D | OK |
| GDACS events [L] | `www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ;TC;FL;VO;DR;WF` | 30m | D | OK |
| NASA EONET v3 | `eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30` | 1h | D | OK |
| USGS elevated volcanoes | `volcanoes.usgs.gov/hans-public/api/volcano/getElevatedVolcanoes` | 1d | D | OK |
| NDBC DART stations | `www.ndbc.noaa.gov/activestations.xml` (type `dart`), then `data/realtime2/<id>.dart` | 30m | A (7 d) | OK (station rule 9.4) |

### 8.4 Global weather events

| Dataset | Source | Tier | Class | Status |
| --- | --- | --- | --- | --- |
| NHC/CPHC active storms | `www.nhc.noaa.gov/CurrentStorms.json` | 30m | D | OK (empty list when no storm) |
| IBTrACS active tracks | `www.ncei.noaa.gov/.../ibtracs.ACTIVE.list.v04r01.csv` | 1h | D | OK |
| FIRMS VIIRS fires, 24 h | `firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv` | 1h | C | OK (no key, 8 MB) |
| FIRMS area API | `firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/world/1` | 1h | C | Key (optional; the no-key file is the default) |

### 8.5 Global ocean and climate

| Dataset | Source | Tier | Class | Status |
| --- | --- | --- | --- | --- |
| SST anomaly, OISST v2.1 NRT | `coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21NrtAgg.csv?anom[(last)][(0.0)][(-89.875):4:(89.875)][(0.125):4:(359.875)]` | 1d | C | OK (1 to 2 days latency) |
| Sea level anomaly | `coastwatch.pfeg.noaa.gov/erddap/griddap/nesdisSSH1day.csv?sla[(last)][(-89.875):4:(89.875)][(-179.875):4:(179.875)]` | 1d | C | OK (approx. 3 weeks latency) |
| Coral bleaching alert, 7-day max | `coastwatch.pfeg.noaa.gov/erddap/griddap/NOAA_DHW.csv?CRW_BAA_7D_MAX[(last)][(89.975):40:(-89.975)][(-179.975):40:(179.975)]` | 1d | C | Runner (302 to `pae-paha.pacioos.hawaii.edu`) |
| Global temp. anomaly, monthly | `www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/tavg/land_ocean/1/0/1850-{Y}/data.json` | 1w | E | OK |
| NASA GISTEMP, monthly | `data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv` | 1w | E | OK |
| CO2 daily and monthly (Mauna Loa) | `gml.noaa.gov/webdata/ccgg/trends/co2/co2_daily_mlo.csv`, `co2_mm_mlo.csv` | 1d | E | OK |
| CO2, CH4, N2O, SF6 global monthly | `gml.noaa.gov/webdata/ccgg/trends/<gas>/<gas>_mm_gl.csv` | 1w | E | OK (1 to 4 months latency) |
| Sea ice extent, both poles | `noaadata.apps.nsidc.org/NOAA/G02135/{north,south}/daily/data/{N,S}_seaice_extent_daily_v4.0.csv` | 1d | E | OK |
| ENSO ONI | `www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` | 1w | E | OK |
| Weekly Nino indices | `www.cpc.ncep.noaa.gov/data/indices/wksst9120.for` (fixed width) | 1w | E | OK |
| Daily AO, NAO, AAO, PNA | `ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.<idx>.cdas.<lev>.<start>_current.csv` | 1d | E | OK |
| Ozone hole (seasonal) | `ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone/to3areas_{Y}_toms+omi+omps.txt` | 1d | E | OK (Aug to Dec) |
| MJO RMM (BoM) [L] | `www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt` | 1d | E | Runner (403 in the audit) |
| Global mean sea level | `www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/slr/slr_sla_gbl_free_ref_90.csv` | 1w | E | Runner (connection reset). Fallback: area-weighted mean of the sea level grid |

The SST grid also gives the global mean SST anomaly and the Nino 3.4 box mean as derived scalars (7.2). The sea level grid gives the global mean sea level anomaly the same way.

### 8.6 Static, removed, and not used

- Static: Natural Earth 110m coastlines (`raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_coastline.geojson`). Public domain. Quantize and store in `static/`.
- Removed after the audit: Smithsonian GVP weekly report (403 for automated requests), CCMC Kauai DONKI copy (connection reset), SWPC `products/solar-wind/` (removed by SWPC), NSIDC v3.0 files (404).
- Not used: `api.weather.gov`, NCEI CDO, and USGS water (US local data). EIA grid demand is US only; optional later.

## 9. Fetch pipeline

Each dataset goes through the same 11 steps. A failure keeps the last good data.

### 9.1 Procedure for each dataset

1. Read the entry in `sources.json`.
2. Send GET with User-Agent `public-data-dashboard/<VERSION> (+<repo URL>)`, `Accept-Encoding: gzip`, `If-None-Match`, and `If-Modified-Since`.
3. If the response is 304: set status "ok". Stop.
4. If the response is 429 or 5xx: try again 3 times (5 s, 20 s, 60 s). Obey `Retry-After`.
5. Parse and validate fields, types, and ranges. If the parse fails, fetch again (rule 9.4a).
6. If validation still fails: keep the last good data. Set status "error". Write a sample to the run summary.
7. Normalize: UTC seconds, units, quantize, regrid.
8. Merge (5.6). Update `latest.json`.
9. Update the summary tiers for the changed range.
10. Prune old files (5.6).
11. Write the manifest entry: hash, size, times, status.

### 9.2 Rules

- Timeout: 30 s for each request. Maximum 2 parallel requests to one host.
- Maximum run time: 8 minutes.
- Do not poll faster than the source updates. Obey `Expires` and `Cache-Control`.
- Use data services only. Do not scrape HTML.
- Mask keys in logs and in all written files.

### 9.3 sources.json entry

```json
{
  "id": "space.goes.xray",
  "title": "GOES X-ray flux",
  "domain": "space",
  "tier": "30m",
  "url": "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json",
  "backfill_url": "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json",
  "adapter": "swpc_goes",
  "kind": "series",
  "class": "A",
  "retention": { "r": "7d", "m5": "30d", "h1": "1y", "d1": "5y" },
  "dt": 60,
  "max_age_days": 1,
  "budget_mb": 0.5,
  "key_secret": null,
  "license": "US Government work",
  "attribution": "NOAA SWPC",
  "status": "ok",
  "fixture": "fixtures/swpc.xray-1d.json",
  "rules": [],
  "sunset": null
}
```

If a dataset uses more than 2 x its `budget_mb`, the run writes a warning to the manifest.

### 9.4 Adapter rules from the Phase 0 audit

| Rule | Sources | Procedure |
| --- | --- | --- |
| a. Retry on parse error | All JSON; SWPC protons seen | SWPC sometimes sends a truncated body (2 of 3 requests in one test). If the parse fails, wait 3 s and fetch again, maximum 2 times. |
| b. Change detection without headers | 20 sources (JPL, GDACS, EONET, USGS geomag, USGS volcano, NCEI CAG, ERDDAP info) | These send no ETag or Last-Modified. Compare a SHA-256 of the body with the stored hash. If equal, stop. |
| c. Active spacecraft filter | SWPC `rtsw_wind_1m`, `rtsw_mag_1m` | Each minute has rows from 2 spacecraft. Keep only rows with `active = true`. Store `source` as a small code column. |
| d. DART station selection | NDBC | Read `activestations.xml` once each day. Use stations with `type="dart"`. Skip a station after a 404 or when its newest row is more than 2 days old. |
| e. Freshness by dataset | Monthly climate files, sea level grid | Use `max_age_days` from `sources.json` for the stale check, not the tier default. GML global monthly files lag 1 to 4 months. The sea level grid lags approx. 3 weeks. |
| f. Forecast rows | Kp forecast, Enlil, cycle predicted, 45-day, ozone | Future times are normal. Store only the newest issue (latest only). |
| g. Empty lists | NHC, tsunami | An empty list is valid. Do not set status "error". |

## 10. GitHub Actions workflow

One workflow runs every 30 minutes and runs the slower tiers when they are due. Thus there is one deploy and no conflicts.

### 10.1 run.yml

```yaml
on:
  schedule:
    - cron: "13,43 * * * *"
  workflow_dispatch:
    inputs:
      tier:      # all | 30m | 1h | 1d | 1w
      backfill:  # true | false
```

- Each run does the 30m tier.
- `run.py` reads `last_run` for each tier from the store. It also runs 1h, 1d, and 1w when they are due.
- Daily tier: first run after 05:00 UTC. Weekly tier: Monday.

### 10.2 Job steps

1. Check out `main`.
2. Restore the newest cache entry `store-`. If none exists: download `data/` from the live site (4.3).
3. Run `python fetch/run.py`.
4. If no file changed: no cache save, no deploy. Stop.
5. Save the cache `store-<run_id>`. Delete old `store-` entries (keep 3).
6. Copy `index.html`, `static/`, and `data/` (without `_state/`) to `_site/`.
7. Run `actions/upload-pages-artifact`, then `actions/deploy-pages`.

### 10.3 Settings

| Item | Value |
| --- | --- |
| Concurrency | Group "pipeline", `cancel-in-progress: false` |
| Permissions | `contents: write` (keep-alive only), `pages: write`, `id-token: write`, `actions: write` (cache delete) |
| Secrets | `NASA_API_KEY`, `FIRMS_MAP_KEY` (both optional, see 10.4) |
| Tests | `test.yml` runs all adapter tests on each push and pull request |
| Audit | `audit.yml` runs the Phase 0 audit by hand (tools/audit) |
| Runner time | Approx. 1 to 2 min each run, 48 runs each day. Standard runners are free for public repositories. |

### 10.4 API keys (secrets)

The code never contains a key. The workflow reads each key from a GitHub repository secret and passes it to the scripts as an environment variable:

```yaml
env:
  NASA_API_KEY: ${{ secrets.NASA_API_KEY }}
  FIRMS_MAP_KEY: ${{ secrets.FIRMS_MAP_KEY }}
```

| Secret | Where to get it | If it is not set |
| --- | --- | --- |
| `NASA_API_KEY` | https://api.nasa.gov (free, email only) | The pipeline uses `DEMO_KEY`. It allows 10 requests each hour, so DONKI updates are slow and can fail. |
| `FIRMS_MAP_KEY` | https://firms.modaps.eosdis.nasa.gov/api/map_key/ (free, email only) | The pipeline uses the no-key 24-hour file. No data is lost. |

Where to enter a key, after the code is on `main`:

1. Open the repository on github.com.
2. Click **Settings** (top bar of the repository).
3. In the left menu, open **Secrets and variables**, then click **Actions**.
4. On the **Secrets** tab, click **New repository secret**.
5. Name: `NASA_API_KEY`. Secret: paste the key. Click **Add secret**.
6. Do steps 4 and 5 again for `FIRMS_MAP_KEY`.

After you save a secret, nobody can read it again, also not you. GitHub masks it in all logs. Workflows from forks do not get it. The next scheduled run uses the key automatically. To use it at once, open **Actions**, select **run**, and click **Run workflow**.

### 10.5 Keep-alive

On the first run of each month, the job adds one line (date and store size) to `KEEPALIVE.txt` on `main` and pushes it. This makes 12 small commits each year. The repository does not grow in a significant way.

## 11. Dashboard page (index.html)

The page is one file of less than 35 KB gzip. It loads only the data for the visible widgets.

### 11.1 File rules

- One file. Inline CSS and JS. No libraries. System fonts.
- Size target: less than 120 KB, less than 35 KB with gzip.
- CSP: `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; worker-src blob:; img-src 'none'`

### 11.2 Start sequence

1. Draw the shell and the layout from `localStorage` (or a preset).
2. Fetch `data/manifest.json`.
3. For each visible widget: fetch `latest.json` and draw it. Then fetch the shards for the selected range.
4. Load widgets out of view when they come into view.
5. Fetch the manifest again at the next expected update time (approx. each 30 minutes) and when the tab becomes visible. Use the browser cache with ETag. Fetch only datasets with a changed hash.

### 11.3 Data layer

- A Web Worker decodes shards: dequantize, decode grids, M4 downsample.
- The page picks the smallest tier that gives not more than 2 points for each pixel:

| Range | Tier |
| --- | --- |
| Up to 7 d | raw |
| Up to 30 d | m5 |
| Up to 1 y | h1 |
| Longer | d1 |

- The range buttons show only ranges inside the retention of the dataset.
- LRU cache: approx. 50 MB.

### 11.4 Layout

- CSS grid: 12 columns on desktop, 4 columns on mobile. Row height 80 px.
- Sizes: S 3x2, M 6x2, L 6x4, XL 12x4. Resize snaps to the grid.
- Move with Pointer Events on the header grip. Resize grip at the corner. Keyboard: Alt + arrow keys.
- Catalog panel from the manifest. Presets: Overview, Space Weather, Earth Events, Ocean and Climate, Custom.
- Layout in `localStorage`. Export and import as JSON.

### 11.5 Time controls

- Range buttons: 6h, 24h, 7d, 30d, 1y, 5y.
- Brush on an overview strip. Shared crosshair for all series.
- Live mode follows the current time.
- UTC by default. A switch shows local time.

### 11.6 Rendering

- Canvas 2D for each widget, scaled for `devicePixelRatio`.
- Draw only after a change. Join changes with `requestAnimationFrame`.
- Cache static layers (axes, coastlines) on an offscreen canvas.
- Dark theme (default) and light theme from CSS variables.

## 12. Widget types

| ID | Widget | Content |
| --- | --- | --- |
| W1 | Scale badges | R, S, G: now, 24 h maximum, 3-day forecast |
| W2 | Time series | Many lines, log axis, threshold bands, event marks |
| W3 | Kp bars | G-level colors, hatched forecast bars |
| W4 | Solar wind stack | Bz, Bt, speed, density. Southward Bz shaded |
| W5 | Aurora polar view | Both hemispheres, coastlines, hemispheric power, time slider over 7 d |
| W6 | World event map | Earthquakes, cyclone tracks, GDACS and EONET events, fire density, volcano and tsunami alerts, day/night line |
| W7 | Event list | Sorted by severity, then time. A click moves the map and the time cursor |
| W8 | Event timeline | One lane for each event type |
| W9 | Calendar heat map | Daily max Kp, daily M4.5+ count, daily fires |
| W10 | Climate trend | Anomaly, 12-month mean, trend line, seasonal overlay (one line each year) |
| W11 | Big number | Value, sparkline, change from 24 h and 1 y, percentile against stored history |
| W12 | Text | Forecast discussion and alerts, scale levels colored |
| W13 | Data health | Status, age, size, and budget use of each dataset. Total size against 150 MB budget and 1 GB limit |
| W14 | Near-Earth objects | Close approaches, distance in lunar distances |
| W15 | Solar cycle | Sunspot number and F10.7 with predicted range |
| W16 | Ocean anomaly map | SST or sea level anomaly, diverging colors, time slider (90 d daily, 2 y weekly), Nino 3.4 box marked |

## 13. Visualization rules

1. Each widget shows title, units, source, data time, and data age.
2. Stale data: age more than 3 x cadence = amber. Age more than 10 x cadence = red.
3. If the manifest is older than 2 hours, show a banner on the page.
4. Use official scales and colors: NOAA R/S/G, PAGER, GDACS, Saffir-Simpson.
5. Show missing data as a gap. Do not interpolate.
6. Use a log axis for values over many decades.
7. Show forecasts dashed or hatched. Show a "now" line.
8. Tooltips show the exact value, units, UTC time, and quality flag.
9. Use colorblind-safe palettes. Use a diverging palette for anomalies, centered on zero. Do not use color only; also use shape.
10. Show the percentile against stored history, with the window length (example: "98th percentile of 1 year").
11. For summary tiers, draw the min/max band and the mean line. The user then sees that the data is a summary.
12. Each widget has an "i" button with one short paragraph about the quantity.

## 14. Compliance and attribution

1. Use data services only. Do not scrape HTML.
2. Send a User-Agent with the repository URL on all requests. Do not put an email in it.
3. Obey rate limits, `Retry-After`, and cache headers.
4. Keep keys in GitHub Secrets only. Never put keys in data files or logs.
5. Record the terms of each source in `docs/SOURCES.txt`.
6. Sources with other terms \[L\]: WDC Kyoto, SILSO (CC BY-NC), GDACS, BoM, Smithsonian GVP. Show the attribution in the widget and in the footer.
7. Show this disclaimer: "This dashboard is not an official warning service." Link each alert to the official issuer.
8. Keep jobs short. Follow the GitHub Acceptable Use Policies.

## 15. Failure procedures

| Failure | Procedure |
| --- | --- |
| Source is down | Keep the last good data. Status "error". The widget shows the age. |
| Truncated body | Retry (rule 9.4a). Then status "error" if it still fails. |
| Schema change | Validation fails. Status "error". Sample in the run summary. Update the adapter and fixture. |
| Endpoint retirement | `sunset` field. Warning 60 days before the date. Run `audit.yml` to find a replacement. |
| Key missing or rate limited | Use the fallback (10.4). Status "degraded" on the data health widget. |
| Late or dropped run | The overlap windows fill the gap. |
| Cache lost | Fallback to the live site (4.3). |
| Cache and site lost | Backfill (4.4). |
| Store too large | The deploy stops at 300 MB. W13 shows the dataset that is over its budget. |
| Schedule disabled | Keep-alive (10.5) prevents it. The page shows a banner (section 13, rule 3). |

## 16. Build phases

| Phase | Work | Widgets | Status |
| --- | --- | --- | --- |
| 0. Endpoint audit | Audit tool, 93 then 90 endpoints, sizes, replacements. | - | Done (2026-10-20) |
| 1. Pipeline core | `run.py`, `lib/*`, manifest, cache store, live-site fallback, all SWPC adapters, `run.yml`, Pages deploy, keep-alive, `test.yml`. | - | Next |
| 2. Page shell | Grid layout, move, resize, manifest load, tier choice. | W1, W2, W3, W13 | |
| 3. Space weather | DONKI, JPL, USGS Geomagnetism, SILSO. | W4, W5, W11, W12, W14, W15 | |
| 4. Earth events | Earthquakes, GDACS, EONET, NHC, IBTrACS, tsunami, volcano, FIRMS, DART. Coastlines. | W6, W7, W8, W9 | |
| 5. Ocean and climate | ERDDAP grids, climate records, derived scalars. | W10, W16 | |
| 6. Hardening | Tests, size and speed budgets, accessibility, documents. | - | |

## 17. Decisions on the open questions

All questions are closed.

| ID | Question | Decision |
| --- | --- | --- |
| Q1 | Retention windows (section 6) | Agreed: 7 d raw, 30 d 5-min, 1 y hourly, 5 y daily. |
| Q2 | Size budget | Agreed: 150 MB raw target, 300 MB hard stop. |
| Q3 | User-Agent contact | Repository URL only. No email. |
| Q4 | Default preset on first load | Overview. |
| Q5 | Non-commercial license use | Yes, the use is non-commercial. SILSO (CC BY-NC) and WDC Kyoto data are allowed. Keep the attribution. |
| Q6 | Aurora grid size (2026-10-20) | 2 degree cells and one snapshot each hour. 33.9 MB becomes 4.6 MB. |
| Q7 | API keys (2026-10-20) | Placeholders in code. The owner enters the keys as repository secrets (10.4). |

## 18. Phase 0 audit results (2026-10-20)

Audit v0.1.1 ran 90 endpoints from a cloud workspace. The full report is `phase0-audit-report-v0.1.1.md`.

| Result | Count |
| --- | --- |
| Endpoints that work | 81 |
| Failed: needs a key (DONKI with DEMO_KEY rate limit) | 4 |
| Failed: blocked from the audit workspace (BoM, STAR, coral redirect host) | 3 |
| Failed: replaced by a working URL (NSIDC v3.0) | 2 |
| Skipped: no key (FIRMS API) | 1 |
| Sources with ETag or Last-Modified | 60 of 80 |
| 304 confirmed | 52 |
| Server gzip | 50 of 80 |

Main findings:

- SWPC removed `products/solar-wind/`. The replacement is `json/rtsw/`.
- SWPC sometimes sends a truncated JSON body (rule 9.4a).
- The 1 degree, 30-minute aurora grid was 34 MB. The decision (Q6) reduces it to 4.6 MB.
- Fire points (100,913 in 24 h, 8 MB) fall in only approx. 3,860 one-degree cells. Cell counts are approx. 19 KB each day.
- The measured total is approx. 126 MB, inside the 150 MB budget.

## 19. References (checked 2026-10-20)

- [SWPC data access](https://www.swpc.noaa.gov/content/data-access)
- [SWPC JSON format changes (2026-03-31)](https://www.swpc.noaa.gov/news/scn-upcoming-json-modifications-and-changes)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [GitHub Actions schedule event](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows)
- [GitHub Actions secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [NASA API keys](https://api.nasa.gov)
- [FIRMS MAP_KEY](https://firms.modaps.eosdis.nasa.gov/api/map_key/)
- [ERDDAP OISST v2.1 (CoastWatch)](https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg.html)
- [ERDDAP griddap stride documentation](https://coastwatch.noaa.gov/erddap/griddap/documentation.html)
- [CoastWatch data catalog](https://coastwatch.pfeg.noaa.gov/data.html)
- [USGS WaterServices decommission](https://waterdata.usgs.gov/blog/api-waterservices-decom/)

