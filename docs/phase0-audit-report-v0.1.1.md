# Phase 0 endpoint audit

Audit version 0.1.1 · run 2026-10-20 17:53 UTC · local · Python 3.13.16

## Summary

- Endpoints: 90. OK: 80. Failed: 9. Parse errors: 0. Skipped (no secret): 1.
- Conditional GET headers (ETag or Last-Modified): 60 of 80. 304 confirmed: 52.
- Server sends gzip: 50 of 80.
- Estimated raw-window store for the measured datasets: 81.3 MB (plan budget 150 MB). Summary tiers are not included.

## Action items

| ID | Problem | URL |
| --- | --- | --- |
| swpc.alerts | newest data is 1.4 days old (limit 1 d for tier 30m) | https://services.swpc.noaa.gov/products/alerts.json |
| swpc.protons-1d | note: server sometimes sends a truncated body; the adapter must retry on a parse error | https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json |
| swpc.rtsw-wind-1m | note: contains rows from 2 spacecraft; keep rows with active = true | https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json |
| swpc.rtsw-mag-1m | note: contains rows from 2 spacecraft; keep rows with active = true | https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json |
| nasa.donki-cme | note: DEMO_KEY allows 10 requests/hour per IP; set the NASA_API_KEY secret; HTTP 429 | https://api.nasa.gov/DONKI/CME?startDate=2026-09-20&endDate=2026-10-20&api_key=DEMO_KEY |
| nasa.donki-flr | note: DEMO_KEY allows 10 requests/hour per IP; set the NASA_API_KEY secret; HTTP 429 | https://api.nasa.gov/DONKI/FLR?startDate=2026-09-20&endDate=2026-10-20&api_key=DEMO_KEY |
| nasa.donki-gst | note: DEMO_KEY allows 10 requests/hour per IP; set the NASA_API_KEY secret; HTTP 429 | https://api.nasa.gov/DONKI/GST?startDate=2026-09-20&endDate=2026-10-20&api_key=DEMO_KEY |
| nasa.donki-notifications | note: DEMO_KEY allows 10 requests/hour per IP; set the NASA_API_KEY secret; HTTP 429 | https://api.nasa.gov/DONKI/notifications?startDate=2026-10-13&endDate=2026-10-20&type=all&api_key=DEMO_KEY |
| jpl.cad | no ETag or Last-Modified: compare a hash to detect change | https://ssd-api.jpl.nasa.gov/cad.api?date-min=now&date-max=%2B60&dist-max=0.05&diameter=true |
| jpl.fireball | no ETag or Last-Modified: compare a hash to detect change | https://ssd-api.jpl.nasa.gov/fireball.api |
| jpl.sentry | no ETag or Last-Modified: compare a hash to detect change | https://ssd-api.jpl.nasa.gov/sentry.api |
| usgs.geomag-bou | no ETag or Last-Modified: compare a hash to detect change | https://geomag.usgs.gov/ws/data/?id=BOU&elements=H,D,Z&sampling_period=60&type=variation&format=json |
| gdacs.events | no ETag or Last-Modified: compare a hash to detect change | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ;TC;FL;VO;DR;WF |
| gdacs.rss | conditional GET gave 0, not 304 | https://www.gdacs.org/xml/rss.xml |
| nasa.eonet | no ETag or Last-Modified: compare a hash to detect change | https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30 |
| usgs.volcano-elevated | no ETag or Last-Modified: compare a hash to detect change | https://volcanoes.usgs.gov/hans-public/api/volcano/getElevatedVolcanoes |
| usgs.volcano-elevated-vsc | no ETag or Last-Modified: compare a hash to detect change | https://volcanoes.usgs.gov/vsc/api/volcanoApi/elevated |
| ndbc.dart-21414 | note: 21413 is offline (404) and 21414 is 40 days old; the adapter must read activestations.xml (76 DART stations) and use only fresh stations; newest data is 40.0 days old (limit 1 d for tier 30m) | https://www.ndbc.noaa.gov/data/realtime2/21414.dart |
| firms.viirs-24h-nokey | conditional GET gave 200, not 304 | https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv |
| firms.viirs-api | secret FIRMS_MAP_KEY not set | https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/world/1 |
| erddap.sla-anom | note: NRT altimetry lags approx. 3 weeks | https://coastwatch.pfeg.noaa.gov/erddap/griddap/nesdisSSH1day.csv?sla%5B(last)%5D%5B(-89.875):4:(89.875)%5D%5B(-179.875) |
| erddap.crw-baa | note: ERDDAP redirects (302) to pae-paha.pacioos.hawaii.edu (dataset dhw_5km); no connection: URLError: <urlopen error Tunnel connection failed: 403 Forbidden> | https://coastwatch.pfeg.noaa.gov/erddap/griddap/NOAA_DHW.csv?CRW_BAA_7D_MAX%5B(last)%5D%5B(89.975):20:(-89.975)%5D%5B(-1 |
| ncei.cag-global-a | no ETag or Last-Modified: compare a hash to detect change | https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/land_ocean/1/0/1850-2026/data.j |
| ncei.cag-global-b | no ETag or Last-Modified: compare a hash to detect change | https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/tavg/land_ocean/1/0/1850-2026/d |
| giss.gistemp | conditional GET gave 0, not 304 | https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv |
| nsidc.north-v3 | HTTP 404 | https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v3.0.csv |
| nsidc.south-v3 | HTTP 404 | https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v3.0.csv |
| bom.mjo-rmm | note: 403 from a cloud IP in the first test; test again on the GitHub runner; HTTP 403 | https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt |
| star.gmsl | note: connection reset from a cloud IP; test on the GitHub runner. Fallback: global mean of the ERDDAP sea level grid; no connection: URLError: <urlopen error [Errno 104] Connection reset by peer> | https://www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/slr/slr_sla_gbl_free_ref_90.csv |
| nasa.ozone-hole | note: file has empty rows for the rest of the year; the season is Aug to Dec | https://ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone/to3areas_2026_toms+omi+omps.txt |

## Results by domain

### space

| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| swpc.scales | 200 | 916 | 1.1 | 0.2 | ELCX | 304 | 5 | 2026-10-22 00:00 | 24.0 h | - | - |
| swpc.alerts | 200 | 1008 | 53 | 5.1 | ELCX | 200 (data changed) | 83 | 2026-10-19 09:09 | 2.4 h | 0.4 | 0.13 |
| swpc.kp | 200 | 856 | 4.6 | 0.4 | ELCX | 304 | 61 | 2026-10-20 12:00 | 3.0 h | 0.1 | 0.09 |
| swpc.kp-1m | 200 | 952 | 27 | 1.4 | ELCX | 304 | 358 | 2026-10-20 17:49 | 60 s | 14 | 0.1 |
| swpc.kp-forecast | 200 | 1193 | 6.7 | 0.5 | ELCX | 304 | 81 | 2026-10-23 00:00 | 3.0 h | 0.0 | - |
| swpc.xray-1d | 200 | 672 | 640 | 101 | ELCX | 304 | 2872 | 2026-10-20 17:50 | 60 s | 14 | 0.1 |
| swpc.xray-7d | 200 | 238 | 4484 | 711 | ELCX | 304 | 20142 | 2026-10-20 17:50 | 60 s | 14 | - |
| swpc.xray-flares-7d | 200 | 189 | 29 | 5.0 | ELCX | 304 | 79 | 2026-10-20 13:46 | 96 min | 1.4 | 1.04 |
| swpc.xray-flares-latest | 200 | 373 | 0.4 | 0.2 | ELCX | 304 | 1 | 2026-10-20 17:50 | - | - | - |
| swpc.protons-1d | 200 | 397 | 237 | 31 | ELCX | 304 | 2296 | 2026-10-20 17:45 | 5 min | 11 | 0.08 |
| swpc.electrons-1d | 200 | 157 | 29 | 3.7 | ELCX | 200 (data changed) | 287 | 2026-10-20 17:45 | 5 min | 1.4 | 0.01 |
| swpc.magnetometers-1d | 200 | 153 | 256 | 56 | ELCX | 304 | 1436 | 2026-10-20 17:51 | 60 s | 21 | 0.15 |
| swpc.rtsw-wind-1m | 200 | 512 | 2544 | 87 | ELCX | 304 | 3522 | 2026-10-20 17:47 | 57 s | 52 | 0.37 |
| swpc.rtsw-mag-1m | 200 | 170 | 1493 | 144 | ELCX | 304 | 3628 | 2026-10-20 17:48 | 59 s | 71 | 0.51 |
| swpc.ovation | 200 | 231 | 903 | 147 | ELCX | 304 | 65160 | 2026-10-20 17:43 | - | 4730 | 33.9 |
| swpc.hemi-power | 200 | 303 | 12 | 1.9 | ELCX | 304 | 215 | 2026-10-20 17:50 | 5 min | 2.8 | 2.11 |
| swpc.dst | 200 | 225 | 7.3 | 0.8 | ELCX | 304 | 168 | 2026-10-20 17:00 | 60 min | 0.1 | 0.09 |
| swpc.enlil | 200 | 208 | 1481 | 152 | ELCX | 304 | 4356 | 2026-10-25 00:01 | 2 min | 27 | - |
| swpc.3day-forecast | 200 | 139 | 1.7 | 0.7 | ELCX | 304 | 51 | 2026-10-20 12:30 | - | - | - |
| swpc.discussion | 200 | 208 | 2.8 | 1.3 | ELCX | 200 (data changed) | 71 | 2026-10-20 12:30 | - | - | - |
| swpc.27day-outlook | 200 | 409 | 1.6 | 0.5 | ELCX | 304 | 39 | 2026-10-19 01:41 | - | - | - |
| swpc.f107-30d | 200 | 205 | 1.3 | 0.2 | ELCX | 304 | 30 | 2026-10-19 20:00 | 24.0 h | 0.0 | 0.0 |
| swpc.45day-json | 200 | 180 | 6.1 | 0.7 | ELCX | 304 | 90 | 2026-12-03 00:00 | 24.0 h | 0.0 | - |
| swpc.solar-probabilities | 200 | 146 | 8.9 | 0.5 | ELCX | 304 | 30 | 2026-10-20 00:00 | 24.0 h | - | - |
| swpc.solar-regions | 200 | 376 | 127 | 6.9 | ELCX | 304 | 226 | 2026-10-20 00:00 | 24.0 h | 0.9 | 0.68 |
| swpc.cycle-observed | 200 | 575 | 500 | 34 | ELCX | 304 | 3333 | 2026-09-15 00:00 | 31.0 d | 0.0 | - |
| swpc.cycle-predicted | 200 | 691 | 17 | 2.8 | ELCX | 304 | 57 | 2030-12-15 00:00 | 31.0 d | 0.0 | - |
| nasa.donki-cme | 429 | 538 | 0.2 | 0.2 | - | - | - | - | - | - | - |
| nasa.donki-flr | 429 | 1167 | 0.2 | 0.2 | - | - | - | - | - | - | - |
| nasa.donki-gst | 429 | 697 | 0.2 | 0.2 | - | - | - | - | - | - | - |
| nasa.donki-notifications | 429 | 1087 | 0.2 | 0.2 | - | - | - | - | - | - | - |
| jpl.cad | 200 | 675 | 7.5 | 3.2 | - | - | 40 | 2026-12-18 06:29 | 22.3 h | 0.1 | 0.01 |
| jpl.fireball | 200 | 551 | 75 | 20 | - | - | 1074 | 2026-10-04 03:14 | 7.7 d | 0.0 | - |
| jpl.sentry | 200 | 1417 | 569 | 131 | - | - | 2223 | 2026-10-20 00:00 | 2.0 d | - | - |
| usgs.geomag-bou | 200 | 1526 | 77 | 13 | C | - | 1440 | 2026-10-20 23:59 | 60 s | 21 | 0.15 |
| silso.daily | 200 | 1148 | 2829 | 566 | EL | 304 | 76244 | 2026-09-30 00:00 | 24.0 h | 0.0 | - |
| silso.eisn | 200 | 396 | 0.9 | 0.3 | EL | 304 | 20 | 2026-10-20 00:00 | 24.0 h | 0.0 | - |
| silso.monthly | 200 | 787 | 124 | 31 | EL | 304 | 3333 | 2026-09-15 00:00 | 31.0 d | 0.0 | - |

### geo

| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| usgs.quakes-2.5-day | 200 | 153 | 35 | 5.2 | LCX | 304 | 50 | 2026-10-20 17:05 | 21 min | 6.1 | 2.29 |
| usgs.quakes-4.5-month | 200 | 279 | 447 | 53 | LCX | 304 | 655 | 2026-10-20 17:05 | 41 min | 2.6 | 4.81 |
| usgs.quakes-2.5-month | 200 | 517 | 1310 | 168 | LCX | 304 | 1901 | 2026-10-20 17:05 | 15 min | 7.4 | - |
| tsunami.ntwc | 200 | 339 | 1.9 | 0.9 | L | 304 | 1 | 2026-10-20 10:45 | - | - | - |
| tsunami.ptwc | 200 | 506 | 1.9 | 0.8 | L | 304 | 1 | 2026-10-20 04:31 | - | - | - |
| gdacs.events | 200 | 844 | 121 | 13 | - | - | 86 | 2026-10-20 12:00 | 3.0 d | 0.0 | 0.02 |
| gdacs.rss | 200 | 985 | 757 | 42 | EL | - | 253 | 2026-10-20 15:17 | 2 min | 0.1 | - |
| nasa.eonet | 200 | 637 | 130 | 10 | C | - | 52 | 2026-10-20 06:00 | 13.3 h | 0.2 | 0.15 |
| usgs.volcano-elevated | 200 | 695 | 2.6 | 0.5 | - | - | 4 | 2026-10-19 20:01 | 46.2 h | 0.1 | 0.09 |
| usgs.volcano-elevated-vsc | 200 | 521 | 3.5 | 0.9 | - | - | 4 | 2026-10-19 20:01 | 46.2 h | 0.1 | - |
| ndbc.dart-21414 | 200 | 438 | 276 | 38 | ELC | 304 | 9126 | 2026-09-10 18:00 | 60 s | 1.9 | 0.01 |

### weather

| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nhc.current-storms | 200 | 142 | 0.0 | 0.0 | ELCX | 304 | 1 | - | - | - | - |
| ibtracs.active | 200 | 429 | 157 | 13 | EL | 304 | 340 | 2026-10-20 00:00 | 3.0 h | 2.6 | 1.92 |
| firms.viirs-24h-nokey | 200 | 602 | 8000 | 1787 | EL | 200 | 100913 | 2026-10-20 00:00 | 24.0 h | 19 | 1.74 |
| firms.viirs-api | skip | - | - | - | - | - | - | - | - | - | - |

### ocean

| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| erddap.oisst-nrt-anom | 200 | 785 | 2839 | 257 | L | 200 (data changed) | 64800 | 2026-10-19 12:00 | - | 210 | 19.38 |
| erddap.sla-anom | 200 | 1397 | 2804 | 301 | L | 200 (data changed) | 64800 | 2026-09-28 00:00 | - | 175 | 16.15 |
| erddap.crw-baa | 0 | 2043 | 0.0 | - | - | - | - | - | - | - | - |

### climate

| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ncei.cag-global-a | 200 | 254 | 59 | 8.2 | CX | - | 2121 | 2026-09-01 00:00 | 31.0 d | 0.0 | - |
| ncei.cag-global-b | 200 | 299 | 59 | 8.2 | CX | - | 2121 | 2026-09-01 00:00 | 31.0 d | 0.0 | - |
| giss.gistemp | 200 | 9004 | 13 | 3.8 | EL | - | 147 | 2026-01-01 00:00 | 365.0 d | 0.0 | - |
| gml.co2-daily-mlo | 200 | 369 | 423 | 117 | EL | 304 | 16007 | 2026-10-19 00:00 | 24.0 h | 0.0 | - |
| gml.co2-monthly-mlo | 200 | 347 | 38 | 12 | EL | 304 | 823 | 2026-09-15 00:00 | 31.0 d | 0.0 | - |
| gml.co2-monthly-gl | 200 | 338 | 24 | 7.4 | EL | 304 | 571 | 2026-07-15 00:00 | 31.0 d | 0.0 | - |
| gml.ch4-monthly-gl | 200 | 490 | 23 | 8.3 | EL | 304 | 516 | 2026-06-15 00:00 | 31.0 d | 0.0 | - |
| gml.n2o-monthly-gl | 200 | 873 | 14 | 4.4 | EL | 304 | 306 | 2026-06-15 00:00 | 31.0 d | 0.0 | - |
| gml.sf6-monthly-gl | 200 | 339 | 15 | 4.5 | EL | 304 | 348 | 2026-06-15 00:00 | 31.0 d | 0.0 | - |
| nsidc.north-v3 | 404 | 466 | 0.1 | 0.1 | - | - | - | - | - | - | - |
| nsidc.south-v3 | 404 | 333 | 0.1 | 0.1 | - | - | - | - | - | - | - |
| nsidc.north-v4 | 200 | 460 | 1862 | 195 | EL | 304 | 15873 | 2026-10-17 00:00 | 24.0 h | 0.0 | - |
| nsidc.south-v4 | 200 | 480 | 1791 | 194 | EL | 304 | 15873 | 2026-10-17 00:00 | 24.0 h | 0.0 | - |
| cpc.oni | 200 | 275 | 22 | 5.6 | LCX | 304 | 920 | 2026-08-15 00:00 | 31.0 d | 0.0 | - |
| cpc.nino-weekly | 200 | 384 | 145 | 29 | LCX | 304 | 2359 | - | - | - | - |
| cpc.ao-daily | 200 | 344 | 808 | 327 | LC | 304 | 28050 | 2026-10-18 00:00 | 24.0 h | 0.0 | - |
| cpc.nao-daily | 200 | 284 | 810 | 225 | LC | 304 | 28050 | 2026-10-18 00:00 | 24.0 h | 0.0 | - |
| cpc.aao-daily | 200 | 490 | 501 | 203 | LC | 304 | 17458 | 2026-10-18 00:00 | 24.0 h | 0.0 | - |
| cpc.pna-daily | 200 | 331 | 809 | 225 | LC | 304 | 28050 | 2026-10-18 00:00 | 24.0 h | 0.0 | - |
| bom.mjo-rmm | 403 | 371 | 1.4 | 0.7 | CX | - | - | - | - | - | - |
| star.gmsl | 0 | 12135 | 0.0 | - | - | - | - | - | - | - | - |
| nasa.ozone-hole | 200 | 308 | 28 | 5.1 | EL | 304 | 370 | 2026-12-31 00:00 | 24.0 h | 0.0 | - |

### static

| ID | HTTP | ms | KB | gzip KB | Cache | 304 | Records | Newest | Step | Est. KB/day | Est. MB (window) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| static.ne-110m-coastline | 200 | 165 | 137 | 52 | ECX | 304 | 134 | - | - | - | - |

Cache: E = ETag, L = Last-Modified, C = Cache-Control, X = Expires. KB = decompressed body. gzip KB = body after local gzip -6.

## Dataset details

### swpc.scales

- URL: `https://services.swpc.noaa.gov/products/noaa-scales.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:05 GMT.
- Shape: object of 5 objects
- Time (column 'DateStamp'): 2026-10-19 00:00 to 2026-10-22 00:00 UTC, span 3.0 d, step 24.0 h, age of newest -30.1 h

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| DateStamp | time | 0.0 | "2026-10-20" |
| TimeStamp | string | 0.0 | "17:52:00" |
| R | nested | 0.0 | {"Scale": "0", "Text": "none", "MinorPro |
| S | nested | 0.0 | {"Scale": "0", "Text": "none", "Prob": n |
| G | nested | 0.0 | {"Scale": "0", "Text": "none"} |
| _key | number | 0.0 | "0" |

### swpc.alerts

- URL: `https://services.swpc.noaa.gov/products/alerts.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:24 GMT.
- Shape: list of objects
- Time (column 'issue_datetime'): 2026-09-21 18:32 to 2026-10-19 09:09 UTC, span 27.609 d, step 2.4 h, age of newest 32.7 h
- Estimate basis: 3.0 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| product_id | string | 0.0 | "BHIS" |
| issue_datetime | time | 0.0 | "2026-10-19 09:09:16.063" |
| message | string | 0.0 | "Space Weather Message Code: SUM10R\r\nS |

Issues: newest data is 1.4 days old (limit 1 d for tier 30m)

### swpc.kp

- URL: `https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:17 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-13 00:00 to 2026-10-20 12:00 UTC, span 7.5 d, step 3.0 h, age of newest 5.9 h
- Estimate basis: 8 rows/day x 3 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-13T00:00:00" |
| Kp | number | 0.0 | 3.33 |
| a_running | number | 0.0 | 18 |
| station_count | number | 0.0 | 8 |

### swpc.kp-1m

- URL: `https://services.swpc.noaa.gov/json/planetary_k_index_1m.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:28 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-20 11:52 to 2026-10-20 17:49 UTC, span 0.248 d, step 60 s, age of newest 0.1 h
- Estimate basis: 1444 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-20T11:52:00" |
| kp_index | number | 0.0 | 2 |
| estimated_kp | number | 0.0 | 2.0 |
| kp | string | 0.0 | "2Z" |

### swpc.kp-forecast

- URL: `https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:16 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-13 00:00 to 2026-10-23 00:00 UTC, span 10.0 d, step 3.0 h, age of newest -54.1 h
- Estimate basis: 8 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-13T00:00:00" |
| kp | number | 0.0 | 3.33 |
| observed | string | 0.0 | "observed" |
| noaa_scale | string | 95.1 | "G1" |

### swpc.xray-1d

- URL: `https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:40 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-19 17:53 to 2026-10-20 17:50 UTC, span 0.998 d, step 60 s, age of newest 0.1 h
- Estimate basis: 2878 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-19T17:53:00Z" |
| satellite | number | 0.0 | 18 |
| flux | number | 0.0 | 4.2051531146114485e-09 |
| observed_flux | number | 0.0 | 2.3683254468664927e-08 |
| electron_correction | number | 0.0 | 1.947810090996427e-08 |
| electron_contaminaton | string | 0.0 | true |
| energy | string | 0.0 | "0.05-0.4nm" |

### swpc.xray-7d

- URL: `https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:00 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-13 17:53 to 2026-10-20 17:50 UTC, span 6.998 d, step 60 s, age of newest 0.1 h
- Estimate basis: 2878 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-13T17:53:00Z" |
| satellite | number | 0.0 | 18 |
| flux | number | 0.0 | 5.079023868148624e-09 |
| observed_flux | number | 0.0 | 1.6370641731100477e-08 |
| electron_correction | number | 0.0 | 1.1291618307041063e-08 |
| electron_contaminaton | string | 0.0 | true |
| energy | string | 0.0 | "0.05-0.4nm" |

### swpc.xray-flares-7d

- URL: `https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:53:56 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-13 21:42 to 2026-10-20 13:46 UTC, span 6.669 d, step 96 min, age of newest 4.1 h
- Estimate basis: 11.8 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-13T21:42:00Z" |
| begin_time | time | 0.0 | "2026-10-13T21:42:00Z" |
| begin_class | string | 0.0 | "B5.8" |
| max_time | time | 2.5 | "2026-10-13T21:50:00Z" |
| max_class | string | 2.5 | "B9.9" |
| max_xrlong | number | 2.5 | 9.990017133532092e-07 |
| max_ratio | number | 27.8 | 0.547092824703622 |
| max_ratio_time | time | 27.8 | "2026-10-14T00:50:12Z" |
| current_int_xrlong | number | 1.3 | 0.0007018041214905679 |
| end_time | time | 0.0 | "2026-10-13T21:55:00Z" |
| end_class | string | 0.0 | "B7.9" |
| satellite | number | 0.0 | 18 |

### swpc.xray-flares-latest

- URL: `https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:08 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-20 17:50 to 2026-10-20 17:50 UTC, span 0.0 d, step -, age of newest 0.1 h

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-20T17:50:00Z" |
| satellite | number | 0.0 | 18 |
| current_class | string | 0.0 | "B5.1" |
| current_ratio | number | 0.0 | 0.0019409259026776924 |
| current_int_xrlong | number | 0.0 | 0.0018398636020720005 |
| begin_time | time | 0.0 | "2026-10-20T13:46:00Z" |
| begin_class | string | 0.0 | "B8.3" |
| max_time | time | 0.0 | "2026-10-20T13:56:00Z" |
| max_class | string | 0.0 | "C2.8" |
| max_xrlong | number | 0.0 | 2.8829883831349434e-06 |
| end_time | time | 0.0 | "2026-10-20T14:02:00Z" |
| max_ratio_time | time | 0.0 | "2026-10-20T13:55:44Z" |
| max_ratio | number | 0.0 | 0.10958043877671882 |
| end_class | string | 0.0 | "C1.8" |

### swpc.protons-1d

- URL: `https://services.swpc.noaa.gov/json/goes/primary/integral-protons-1-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:26 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-19 17:55 to 2026-10-20 17:45 UTC, span 0.993 d, step 5 min, age of newest 0.1 h
- Estimate basis: 2312 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-19T17:55:00Z" |
| satellite | number | 0.0 | 18 |
| flux | number | 0.0 | 6.02785587310791 |
| energy | string | 0.0 | ">=1 MeV" |

Issues: note: server sometimes sends a truncated body; the adapter must retry on a parse error

### swpc.electrons-1d

- URL: `https://services.swpc.noaa.gov/json/goes/primary/integral-electrons-1-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:36 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-19 17:55 to 2026-10-20 17:45 UTC, span 0.993 d, step 5 min, age of newest 0.1 h
- Estimate basis: 289 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-19T17:55:00Z" |
| satellite | number | 0.0 | 19 |
| flux | number | 0.0 | 350.05596923828125 |
| energy | string | 0.0 | ">=2 MeV" |

### swpc.magnetometers-1d

- URL: `https://services.swpc.noaa.gov/json/goes/primary/magnetometers-1-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:11 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-19 17:53 to 2026-10-20 17:51 UTC, span 0.999 d, step 60 s, age of newest 0.0 h
- Estimate basis: 1437 rows/day x 3 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-19T17:53:00Z" |
| satellite | number | 0.0 | 19 |
| He | number | 0.0 | 30.507644653320312 |
| Hp | number | 0.0 | 111.9083251953125 |
| Hn | number | 0.0 | -1.2421249151229858 |
| total | number | 0.0 | 115.99967956542969 |
| arcjet_flag | string | 0.0 | false |

### swpc.rtsw-wind-1m

- URL: `https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:40 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-19 17:53 to 2026-10-20 17:47 UTC, span 0.996 d, step 57 s, age of newest 0.1 h
- Estimate basis: 3536 rows/day x 3 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-20T17:47:00" |
| active | string | 0.0 | true |
| source | string | 0.0 | "SOLAR1" |
| proton_speed | number | 0.0 | 381.4 |
| proton_temperature | number | 0.0 | 153579 |
| proton_density | number | 0.0 | 6.78 |
| proton_vx_gse | number | 70.3 | -377.0 |
| proton_vy_gse | number | 70.3 | 57.0 |
| proton_vz_gse | number | 70.3 | -10.7 |
| proton_vx_gsm | number | 70.3 | -377.0 |
| proton_vy_gsm | number | 70.3 | 50.8 |
| proton_vz_gsm | number | 70.3 | -28.0 |
| proton_sample_size | number | 0.0 | 1 |
| alpha_speed | empty | 100.0 |  |
| alpha_temperature | empty | 100.0 |  |
| alpha_density | empty | 100.0 |  |
| alpha_vx_gse | empty | 100.0 |  |
| alpha_vy_gse | empty | 100.0 |  |
| alpha_vz_gse | empty | 100.0 |  |
| alpha_vx_gsm | empty | 100.0 |  |
| alpha_vy_gsm | empty | 100.0 |  |
| alpha_vz_gsm | empty | 100.0 |  |
| alpha_sample_size | empty | 100.0 |  |
| max_convergence_flag | number | 0.0 | 0 |
| max_data_flag | number | 0.0 | 0 |
| max_error_count_flag | number | 0.0 | 0 |
| max_processing_flag | number | 0.0 | 0 |
| max_range_flag | number | 0.0 | 0 |
| max_sample_count_flag | number | 0.0 | 0 |
| max_telemetry_flag | number | 0.0 | 0 |
| ... 1 more | | | |

Issues: note: contains rows from 2 spacecraft; keep rows with active = true

### swpc.rtsw-mag-1m

- URL: `https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:10 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-19 17:52 to 2026-10-20 17:48 UTC, span 0.997 d, step 59 s, age of newest 0.1 h
- Estimate basis: 3639 rows/day x 4 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-20T17:48:00" |
| active | string | 0.0 | true |
| source | string | 0.0 | "SOLAR1" |
| range | empty | 100.0 |  |
| scale | empty | 100.0 |  |
| sensitivity | empty | 100.0 |  |
| manual_mode | string | 0.0 | false |
| sample_size | number | 0.0 | 60 |
| bt | number | 0.0 | 6.72 |
| bx_gse | number | 0.0 | -5.89 |
| by_gse | number | 0.0 | 2.72 |
| bz_gse | number | 0.0 | -1.66 |
| theta_gse | number | 0.0 | -14.25 |
| phi_gse | number | 0.0 | 155.17 |
| bx_gsm | number | 0.0 | -5.89 |
| by_gsm | number | 0.0 | 2.07 |
| bz_gsm | number | 0.0 | -2.44 |
| theta_gsm | number | 0.0 | -21.2 |
| phi_gsm | number | 0.0 | 160.74 |
| max_telemetry_flag | number | 0.0 | 0 |
| max_data_flag | number | 65.0 | 0 |
| overall_quality | number | 0.0 | 0 |

Issues: note: contains rows from 2 spacecraft; keep rows with active = true

### swpc.ovation

- URL: `https://services.swpc.noaa.gov/json/ovation_aurora_latest.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:53:52 GMT.
- Shape: grid points [lon, lat, value], 65160 x 3
- Time (key 'Observation Time'): 2026-10-20 17:43 to 2026-10-20 17:43 UTC, span 0.0 d, step -, age of newest 0.2 h
- Grid: last column: 20180 of 65160 cells non-zero (31.0 %)
- Value range: 0.0 to 37.0
- Metadata: Observation Time = 2026-10-20T17:43:00Z; Forecast Time = 2026-10-20T18:57:00Z; Data Format = [Longitude, Latitude, Aurora]; type = MultiPoint
- Estimate basis: 20180 cells x 5 B x 48 snapshots/day

### swpc.hemi-power

- URL: `https://services.swpc.noaa.gov/text/aurora-nowcast-hemi-power.txt`
- Content-Type: text/plain. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:53:58 GMT.
- Shape: whitespace table, 4 columns
- Time (column 'c0'): 2026-10-20 00:00 to 2026-10-20 17:50 UTC, span 0.743 d, step 5 min, age of newest 0.1 h
- Estimate basis: 289 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| c0 | time | 0.0 | "2026-10-20_00:00" |
| c1 | time | 0.0 | "2026-10-20_01:10" |
| c2 | number | 0.0 | "11" |
| c3 | number | 0.0 | "11" |

### swpc.dst

- URL: `https://services.swpc.noaa.gov/products/kyoto-dst.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:04 GMT.
- License note: WDC Kyoto (non-commercial)
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-13 18:00 to 2026-10-20 17:00 UTC, span 6.958 d, step 60 min, age of newest 0.9 h
- Estimate basis: 24 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-13T18:00:00" |
| dst | number | 0.0 | -16 |

### swpc.enlil

- URL: `https://services.swpc.noaa.gov/json/enlil_time_series.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:53:53 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-10-18 00:01 to 2026-10-25 00:01 UTC, span 7.0 d, step 2 min, age of newest -102.1 h
- Estimate basis: 622 rows/day x 9 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-10-25T00:01:36" |
| earth_particles_per_cm3 | number | 0.0 | 7.091 |
| temperature | number | 0.0 | 32720.969 |
| v_r | number | 0.0 | 369.342 |
| v_theta | number | 0.0 | 23.623 |
| v_phi | number | 0.0 | 10.189 |
| b_r | number | 0.0 | 5.285 |
| b_theta | number | 0.0 | 0.357 |
| b_phi | number | 0.0 | -5.382 |
| polarity | number | 0.0 | -0.646 |
| cloud | empty | 100.0 |  |

### swpc.3day-forecast

- URL: `https://services.swpc.noaa.gov/text/3-day-forecast.txt`
- Content-Type: text/plain. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:00 GMT.
- Shape: text, 51 lines
- Time (Issued line): 2026-10-20 12:30 to 2026-10-20 12:30 UTC, span 0.0 d, step -, age of newest 5.4 h
- Issued: 2026 Oct 20 1230 UTC
- First lines: :Product: 3-Day Forecast / :Issued: 2026 Oct 20 1230 UTC / # Prepared by the U.S. Dept. of Commerce, NOAA, Space Weather Prediction Center

### swpc.discussion

- URL: `https://services.swpc.noaa.gov/text/discussion.txt`
- Content-Type: text/plain. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:50 GMT.
- Shape: text, 71 lines
- Time (Issued line): 2026-10-20 12:30 to 2026-10-20 12:30 UTC, span 0.0 d, step -, age of newest 5.4 h
- Issued: 2026 Oct 20 1230 UTC
- First lines: :Product: Forecast Discussion / :Issued: 2026 Oct 20 1230 UTC / # Prepared by the U.S. Dept. of Commerce, NOAA, Space Weather Prediction Center

### swpc.27day-outlook

- URL: `https://services.swpc.noaa.gov/text/27-day-outlook.txt`
- Content-Type: text/plain. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:06 GMT.
- Shape: text, 39 lines
- Time (Issued line): 2026-10-19 01:41 to 2026-10-19 01:41 UTC, span 0.0 d, step -, age of newest 40.2 h
- Issued: 2026 Oct 19 0141 UTC
- First lines: :Product: 27-day Space Weather Outlook Table 27DO.txt / :Issued: 2026 Oct 19 0141 UTC / # Prepared by the US Dept. of Commerce, NOAA, Space Weather Prediction Center

### swpc.f107-30d

- URL: `https://services.swpc.noaa.gov/products/10cm-flux-30-day.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:03 GMT.
- Shape: list of objects
- Time (column 'time_tag'): 2026-09-20 20:00 to 2026-10-19 20:00 UTC, span 29.0 d, step 24.0 h, age of newest 21.9 h
- Estimate basis: 1 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time_tag | time | 0.0 | "2026-09-20T20:00:00" |
| flux | number | 0.0 | 101 |

### swpc.45day-json

- URL: `https://services.swpc.noaa.gov/json/45-day-forecast.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:53 GMT.
- Shape: object, list in key 'data': list of objects
- Time (column 'time'): 2026-10-20 00:00 to 2026-12-03 00:00 UTC, span 44.0 d, step 24.0 h, age of newest -1038.1 h
- Top keys: type, issued, product, source, version, contact, issuance, metadata, units, data
- Estimate basis: 2 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time | time | 0.0 | "2026-10-20T00:00:00Z" |
| metric | string | 0.0 | "ap" |
| value | number | 0.0 | 22 |

### swpc.solar-probabilities

- URL: `https://services.swpc.noaa.gov/json/solar_probabilities.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:53:55 GMT.
- Shape: list of objects
- Time (column 'date'): 2026-09-21 00:00 to 2026-10-20 00:00 UTC, span 29.0 d, step 24.0 h, age of newest 17.9 h

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| date | time | 0.0 | "2026-10-20T00:00:00" |
| c_class_1_day | number | 0.0 | 85 |
| c_class_2_day | number | 0.0 | 85 |
| c_class_3_day | number | 0.0 | 85 |
| m_class_1_day | number | 0.0 | 25 |
| m_class_2_day | number | 0.0 | 25 |
| m_class_3_day | number | 0.0 | 25 |
| x_class_1_day | number | 0.0 | 5 |
| x_class_2_day | number | 0.0 | 5 |
| x_class_3_day | number | 0.0 | 5 |
| 10mev_protons_1_day | number | 0.0 | 5 |
| 10mev_protons_2_day | number | 0.0 | 5 |
| 10mev_protons_3_day | number | 0.0 | 5 |
| polar_cap_absorption | string | 0.0 | "green" |

### swpc.solar-regions

- URL: `https://services.swpc.noaa.gov/json/solar_regions.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:52 GMT.
- Shape: list of objects
- Time (column 'observed_date'): 2026-09-21 00:00 to 2026-10-20 00:00 UTC, span 29.0 d, step 24.0 h, age of newest 17.9 h
- Estimate basis: 7.8 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| observed_date | time | 0.0 | "2026-10-20" |
| region | number | 0.0 | 4556 |
| latitude | number | 0.0 | 3 |
| longitude | number | 0.0 | -41 |
| location | string | 0.0 | "N03W41" |
| carrington_longitude | number | 0.0 | 71 |
| old_carrington_longitude | number | 11.1 | 71 |
| area | number | 33.2 | 10 |
| spot_class | string | 33.2 | "Bxo" |
| extent | number | 33.2 | 1 |
| number_spots | number | 33.2 | 2 |
| mag_class | string | 33.2 | "B" |
| mag_string | empty | 100.0 |  |
| status | string | 3.1 | "f" |
| c_xray_events | number | 0.0 | 0 |
| m_xray_events | number | 0.0 | 0 |
| x_xray_events | number | 0.0 | 0 |
| proton_events | empty | 100.0 |  |
| s_flares | number | 0.0 | 0 |
| impulse_flares_1 | number | 0.0 | 0 |
| impulse_flares_2 | number | 0.0 | 0 |
| impulse_flares_3 | number | 0.0 | 0 |
| impulse_flares_4 | number | 0.0 | 0 |
| protons | number | 70.4 | 0 |
| c_flare_probability | number | 0.0 | 1 |
| m_flare_probability | number | 0.0 | 1 |
| x_flare_probability | number | 0.0 | 1 |
| proton_probability | number | 0.0 | 1 |
| first_date | time | 0.0 | "2026-10-13T17:22:52" |

### swpc.cycle-observed

- URL: `https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:46 GMT.
- Shape: list of objects
- Time (column 'time-tag'): 1749-01-15 00:00 to 2026-09-15 00:00 UTC, span 101415.0 d, step 31.0 d, age of newest 857.9 h
- Estimate basis: 0 rows/day x 6 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time-tag | time | 0.0 | "1749-01" |
| ssn | number | 0.0 | 96.7 |
| smoothed_ssn | number | 0.0 | -1.0 |
| observed_swpc_ssn | number | 0.0 | -1.0 |
| smoothed_swpc_ssn | number | 0.0 | -1.0 |
| f10.7 | number | 0.0 | -1.0 |
| smoothed_f10.7 | number | 0.0 | -1.0 |

### swpc.cycle-predicted

- URL: `https://services.swpc.noaa.gov/json/solar-cycle/predicted-solar-cycle.json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: Tue, 20 Oct 2026 17:54:54 GMT.
- Shape: list of objects
- Time (column 'time-tag'): 2026-04-15 00:00 to 2030-12-15 00:00 UTC, span 1705.0 d, step 31.0 d, age of newest -36390.1 h
- Estimate basis: 0 rows/day x 14 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time-tag | time | 0.0 | "2026-04" |
| predicted_ssn | number | 0.0 | 92.3 |
| high25_ssn | number | 0.0 | 98.3 |
| high_ssn | number | 0.0 | 102.1 |
| high75_ssn | number | 0.0 | 105.7 |
| low25_ssn | number | 0.0 | 87.6 |
| low_ssn | number | 0.0 | 83.0 |
| low75_ssn | number | 0.0 | 77.7 |
| predicted_f10.7 | number | 0.0 | 133.4 |
| high25_f10.7 | number | 0.0 | 137.9 |
| high_f10.7 | number | 0.0 | 140.8 |
| high75_f10.7 | number | 0.0 | 143.5 |
| low25_f10.7 | number | 0.0 | 129.9 |
| low_f10.7 | number | 0.0 | 126.4 |
| low75_f10.7 | number | 0.0 | 122.5 |

### jpl.cad

- URL: `https://ssd-api.jpl.nasa.gov/cad.api?date-min=now&date-max=%2B60&dist-max=0.05&diameter=true`
- Content-Type: application/json. Cache-Control: -. Expires: -.
- Shape: object with fields + data rows
- Time (column 'cd'): 2026-10-20 05:06 to 2026-12-18 06:29 UTC, span 59.058 d, step 22.3 h, age of newest -1404.6 h
- Estimate basis: 0.7 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| des | string | 0.0 | "2026 TD2" |
| orbit_id | number | 0.0 | "10" |
| jd | number | 0.0 | "2461333.712795270" |
| cd | time | 0.0 | "2026-Oct-20 05:06" |
| dist | number | 0.0 | "0.0186216759072865" |
| dist_min | number | 0.0 | "0.0185612591195495" |
| dist_max | number | 0.0 | "0.0186820919554431" |
| v_rel | number | 0.0 | "12.2940554820264" |
| v_inf | number | 0.0 | "12.2824114299445" |
| t_sigma_f | string | 0.0 | "< 00:01" |
| h | number | 0.0 | "24.56" |
| diameter | empty | 100.0 |  |
| diameter_sigma | empty | 100.0 |  |

Issues: no ETag or Last-Modified: compare a hash to detect change

### jpl.fireball

- URL: `https://ssd-api.jpl.nasa.gov/fireball.api`
- Content-Type: application/json. Cache-Control: -. Expires: -.
- Shape: object with fields + data rows
- Time (column 'date'): 1988-04-15 03:03 to 2026-10-04 03:14 UTC, span 14051.008 d, step 7.7 d, age of newest 398.7 h
- Estimate basis: 0.1 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| date | time | 0.0 | "2026-10-04 03:14:45" |
| energy | number | 0.0 | "5.4" |
| impact-e | number | 0.0 | "0.18" |
| lat | number | 17.3 | "41.8" |
| lat-dir | string | 17.3 | "S" |
| lon | number | 17.3 | "173.1" |
| lon-dir | string | 17.3 | "W" |
| alt | number | 43.9 | "26.9" |
| vel | number | 66.2 | "13.8" |

Issues: no ETag or Last-Modified: compare a hash to detect change

### jpl.sentry

- URL: `https://ssd-api.jpl.nasa.gov/sentry.api`
- Content-Type: application/json. Cache-Control: -. Expires: -.
- Shape: object, list in key 'data': list of objects
- Time (column 'last_obs'): 1979-12-15 00:00 to 2026-10-20 00:00 UTC, span 17111.0 d, step 2.0 d, age of newest 17.9 h
- Top keys: signature, data, count

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| des | string | 0.0 | "2011 TO" |
| ps_cum | number | 0.0 | "-6.15" |
| diameter | number | 0.0 | "0.018" |
| fullname | string | 0.0 | "(2011 TO)" |
| n_imp | number | 0.0 | 1 |
| ps_max | number | 0.0 | "-6.15" |
| v_inf | number | 0.2 | "8.55" |
| h | number | 0.0 | "26.32" |
| ts_max | number | 0.1 | "0" |
| ip | number | 0.0 | "2.937e-06" |
| range | string | 0.0 | "2064-2064" |
| id | string | 0.0 | "bK11T00O" |
| last_obs_jd | number | 0.0 | "2456304.5" |
| last_obs | time | 0.0 | "2013-01-12" |

Issues: no ETag or Last-Modified: compare a hash to detect change

### usgs.geomag-bou

- URL: `https://geomag.usgs.gov/ws/data/?id=BOU&elements=H,D,Z&sampling_period=60&type=variation&format=json`
- Content-Type: application/json. Cache-Control: max-age=60. Expires: -.
- Shape: object with times + values arrays
- Time (column 'time'): 2026-10-20 00:00 to 2026-10-20 23:59 UTC, span 0.999 d, step 60 s, age of newest -6.1 h
- Estimate basis: 1441 rows/day x 3 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time | time | 0.0 | "2026-10-20T00:00:00.000Z" |
| H | number | 25.5 | 20670.923 |
| D | number | 25.6 | 3.5419999999999994 |
| Z | number | 25.5 | 46638.156 |

Issues: no ETag or Last-Modified: compare a hash to detect change

### silso.daily

- URL: `https://www.sidc.be/SILSO/DATA/SN_d_tot_V2.0.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- License note: SILSO CC BY-NC 4.0
- Shape: CSV, 8 columns
- Time (columns [0, 1, 2]): 1818-01-01 00:00 to 2026-09-30 00:00 UTC, span 76243.0 d, step 24.0 h, age of newest 497.9 h
- Estimate basis: 1 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| c0 | number | 0.0 | "1818" |
| c1 | number | 0.0 | "01" |
| c2 | number | 0.0 | "01" |
| c3 | number | 0.0 | "1818.001" |
| c4 | number | 0.0 | "-1" |
| c5 | number | 0.0 | "-1.0" |
| c6 | number | 0.0 | "0" |
| c7 | number | 0.0 | "1" |

### silso.eisn

- URL: `https://www.sidc.be/SILSO/DATA/EISN/EISN_current.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- License note: SILSO CC BY-NC 4.0
- Shape: CSV, 9 columns
- Time (columns [0, 1, 2]): 2026-10-01 00:00 to 2026-10-20 00:00 UTC, span 19.0 d, step 24.0 h, age of newest 17.9 h
- Estimate basis: 1 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| c0 | number | 0.0 | "2026" |
| c1 | number | 0.0 | "10" |
| c2 | number | 0.0 | "01" |
| c3 | number | 0.0 | "2026.749" |
| c4 | number | 0.0 | "28" |
| c5 | number | 0.0 | "6.1" |
| c6 | number | 0.0 | "32" |
| c7 | number | 0.0 | "40" |
| c8 | empty | 100.0 |  |

### silso.monthly

- URL: `https://www.sidc.be/SILSO/DATA/SN_m_tot_V2.0.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- License note: SILSO CC BY-NC 4.0
- Shape: CSV, 7 columns
- Time (columns [0, 1]): 1749-01-15 00:00 to 2026-09-15 00:00 UTC, span 101415.0 d, step 31.0 d, age of newest 857.9 h
- Estimate basis: 0 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| c0 | number | 0.0 | "1749" |
| c1 | number | 0.0 | "01" |
| c2 | number | 0.0 | "1749.042" |
| c3 | number | 0.0 | "96.7" |
| c4 | number | 0.0 | "-1.0" |
| c5 | number | 0.0 | "-1" |
| c6 | number | 0.0 | "1" |

### usgs.quakes-2.5-day

- URL: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson`
- Content-Type: application/json; charset=utf-8. Cache-Control: public, max-age=60. Expires: Tue, 20 Oct 2026 17:54:26 GMT.
- Shape: GeoJSON, 50 features, geometry {'Point': 50}
- Time (column 'time'): 2026-10-19 18:11 to 2026-10-20 17:05 UTC, span 0.955 d, step 21 min, age of newest 0.8 h
- Metadata: generated = 1792518806000; url = https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.; title = USGS Magnitude 2.5+ Earthquakes, Past Day; status = 200; api = 2.7.0; count = 50
- Estimate basis: 52.4 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| mag | number | 0.0 | 5.4 |
| place | string | 0.0 | "192 km S of Burica, Panama" |
| time | number | 0.0 | 1792515948338 |
| updated | number | 0.0 | 1792517006040 |
| tz | empty | 100.0 |  |
| url | string | 0.0 | "https://earthquake.usgs.gov/earthquakes |
| detail | string | 0.0 | "https://earthquake.usgs.gov/earthquakes |
| felt | number | 92.0 | 1 |
| cdi | number | 92.0 | 1 |
| mmi | number | 92.0 | 4.123 |
| alert | string | 94.0 | "green" |
| status | string | 0.0 | "reviewed" |
| tsunami | number | 0.0 | 0 |
| sig | number | 0.0 | 449 |
| net | string | 0.0 | "us" |
| code | string | 0.0 | "6000u3nl" |
| ids | string | 0.0 | ",us6000u3nl," |
| sources | string | 0.0 | ",us," |
| types | string | 0.0 | ",moment-tensor,origin,phase-data," |
| nst | number | 0.0 | 94 |
| dmin | number | 0.0 | 2.997 |
| rms | number | 0.0 | 0.56 |
| gap | number | 0.0 | 126 |
| magType | string | 0.0 | "mww" |
| type | string | 0.0 | "earthquake" |
| title | string | 0.0 | "M 5.4 - 192 km S of Burica, Panama" |

### usgs.quakes-4.5-month

- URL: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson`
- Content-Type: application/json; charset=utf-8. Cache-Control: public, max-age=60. Expires: Tue, 20 Oct 2026 17:54:56 GMT.
- Shape: GeoJSON, 655 features, geometry {'Point': 655}
- Time (column 'time'): 2026-09-20 20:41 to 2026-10-20 17:05 UTC, span 29.85 d, step 41 min, age of newest 0.8 h
- Metadata: generated = 1792518836000; url = https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.; title = USGS Magnitude 4.5+ Earthquakes, Past Month; status = 200; api = 2.7.0; count = 655
- Estimate basis: 21.9 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| mag | number | 0.0 | 5.4 |
| place | string | 0.0 | "192 km S of Burica, Panama" |
| time | number | 0.0 | 1792515948338 |
| updated | number | 0.0 | 1792517006040 |
| tz | empty | 100.0 |  |
| url | string | 0.0 | "https://earthquake.usgs.gov/earthquakes |
| detail | string | 0.0 | "https://earthquake.usgs.gov/earthquakes |
| felt | number | 82.9 | 3 |
| cdi | number | 82.9 | 3.3 |
| mmi | number | 91.1 | 4.123 |
| alert | string | 91.9 | "green" |
| status | string | 0.0 | "reviewed" |
| tsunami | number | 0.0 | 0 |
| sig | number | 0.0 | 449 |
| net | string | 0.0 | "us" |
| code | string | 0.0 | "6000u3nl" |
| ids | string | 0.0 | ",us6000u3nl," |
| sources | string | 0.0 | ",us," |
| types | string | 0.0 | ",moment-tensor,origin,phase-data," |
| nst | number | 0.0 | 94 |
| dmin | number | 0.0 | 2.997 |
| rms | number | 0.0 | 0.56 |
| gap | number | 0.0 | 126 |
| magType | string | 0.0 | "mww" |
| type | string | 0.0 | "earthquake" |
| title | string | 0.0 | "M 5.4 - 192 km S of Burica, Panama" |

### usgs.quakes-2.5-month

- URL: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson`
- Content-Type: application/json; charset=utf-8. Cache-Control: public, max-age=60. Expires: Tue, 20 Oct 2026 17:54:56 GMT.
- Shape: GeoJSON, 1901 features, geometry {'Point': 1901}
- Time (column 'time'): 2026-09-20 18:19 to 2026-10-20 17:05 UTC, span 29.949 d, step 15 min, age of newest 0.8 h
- Metadata: generated = 1792518836000; url = https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.; title = USGS Magnitude 2.5+ Earthquakes, Past Month; status = 200; api = 2.7.0; count = 1901
- Estimate basis: 63.5 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| mag | number | 0.0 | 5.4 |
| place | string | 0.0 | "192 km S of Burica, Panama" |
| time | number | 0.0 | 1792515948338 |
| updated | number | 0.0 | 1792517006040 |
| tz | empty | 100.0 |  |
| url | string | 0.0 | "https://earthquake.usgs.gov/earthquakes |
| detail | string | 0.0 | "https://earthquake.usgs.gov/earthquakes |
| felt | number | 84.0 | 1 |
| cdi | number | 84.0 | 1 |
| mmi | number | 91.7 | 4.123 |
| alert | string | 96.8 | "green" |
| status | string | 0.0 | "reviewed" |
| tsunami | number | 0.0 | 0 |
| sig | number | 0.0 | 449 |
| net | string | 0.0 | "us" |
| code | string | 0.0 | "6000u3nl" |
| ids | string | 0.0 | ",us6000u3nl," |
| sources | string | 0.0 | ",us," |
| types | string | 0.0 | ",moment-tensor,origin,phase-data," |
| nst | number | 0.0 | 94 |
| dmin | number | 0.2 | 2.997 |
| rms | number | 0.0 | 0.56 |
| gap | number | 0.1 | 126 |
| magType | string | 0.0 | "mww" |
| type | string | 0.0 | "earthquake" |
| title | string | 0.0 | "M 5.4 - 192 km S of Burica, Panama" |

### tsunami.ntwc

- URL: `https://www.tsunami.gov/events/xml/PAAQAtom.xml`
- Content-Type: text/xml. Cache-Control: -. Expires: -.
- Shape: XML feed <feed>, 1 items
- Time (item date): 2026-10-20 10:45 to 2026-10-20 10:45 UTC, span 0.0 d, step -, age of newest 7.1 h

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| title | string | 0 | "45 miles SE of Sand Point, Alaska" |
| updated | string | 0 | "2026-10-20T10:45:01Z" |
| lat | string | 0 | "54.634" |
| long | string | 0 | "-160.218" |
| summary | string | 0 | "" |
| id | string | 0 | "urn:uuid:96108cb5-71e9-41a1-b3ae-bf20c0 |
| link | string | 0 | "" |

### tsunami.ptwc

- URL: `https://www.tsunami.gov/events/xml/PHEBAtom.xml`
- Content-Type: text/xml. Cache-Control: -. Expires: -.
- Shape: XML feed <feed>, 1 items
- Time (item date): 2026-10-20 04:31 to 2026-10-20 04:31 UTC, span 0.0 d, step -, age of newest 13.4 h

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| title | string | 0 | "VANUATU" |
| updated | string | 0 | "2026-10-20T04:31:12Z" |
| lat | string | 0 | "-13.869" |
| long | string | 0 | "165.713" |
| summary | string | 0 | "" |
| id | string | 0 | "urn:uuid:00551658-d438-4b4a-8a1c-42d070 |
| link | string | 0 | "" |

### gdacs.events

- URL: `https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=EQ;TC;FL;VO;DR;WF`
- Content-Type: application/json; charset=utf-8. Cache-Control: -. Expires: -.
- License note: GDACS (EU JRC / UN OCHA)
- Shape: GeoJSON, 86 features, geometry {'Point': 86}
- Time (column 'todate'): 2025-10-23 00:00 to 2026-10-20 12:00 UTC, span 362.5 d, step 3.0 d, age of newest 5.9 h
- Estimate basis: 0.2 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| eventtype | string | 0.0 | "TC" |
| eventid | number | 0.0 | 1001338 |
| episodeid | number | 0.0 | 25 |
| eventname | string | 62.8 | "CHAMPI-26" |
| glide | string | 29.1 | "TC-2026-000192-GUM" |
| name | string | 0.0 | "Tropical Cyclone CHAMPI-26" |
| description | string | 0.0 | "Tropical Cyclone CHAMPI-26" |
| htmldescription | string | 0.0 | "Red Tropical Cyclone CHAMPI-26 in Guam, |
| icon | string | 0.0 | "https://www.gdacs.org/images/gdacs_icon |
| iconoverall | string | 0.0 | "https://www.gdacs.org/images/gdacs_icon |
| url | nested | 0.0 | {"geometry": "https://www.gdacs.org/gdac |
| alertlevel | string | 0.0 | "Red" |
| alertscore | number | 0.0 | 3 |
| episodealertlevel | string | 0.0 | "Green" |
| episodealertscore | number | 0.0 | 1.0 |
| istemporary | string | 0.0 | "false" |
| iscurrent | string | 0.0 | "true" |
| country | string | 0.0 | "Guam, Northern Mariana Islands, Japan" |
| fromdate | time | 0.0 | "2026-10-14T12:00:00" |
| todate | time | 0.0 | "2026-10-20T12:00:00" |
| datemodified | time | 0.0 | "2026-10-20T15:00:49" |
| iso3 | string | 1.2 | "GUM" |
| source | string | 0.0 | "JTWC" |
| sourceid | empty | 100.0 |  |
| polygonlabel | string | 0.0 | "Centroid" |
| Class | string | 0.0 | "Point_Centroid" |
| countryonland | empty | 100.0 |  |
| affectedcountries | nested | 0.0 | [{"iso2": "GU", "iso3": "GUM", "countryn |
| severitydata | nested | 0.0 | {"severity": 287.0352, "severitytext": " |

Issues: no ETag or Last-Modified: compare a hash to detect change

### gdacs.rss

- URL: `https://www.gdacs.org/xml/rss.xml`
- Content-Type: application/xml. Cache-Control: -. Expires: -.
- License note: GDACS (EU JRC / UN OCHA)
- Shape: XML feed <rss>, 253 items
- Time (item date): 2026-02-04 09:58 to 2026-10-20 15:17 UTC, span 258.222 d, step 2 min, age of newest 2.6 h
- Estimate basis: 1.0 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| title | string | 0 | "Green earthquake (Magnitude 6.3M, Depth |
| description | string | 0 | "On 10/20/2026 4:20:38 AM, an earthquake |
| enclosure | string | 0 | "" |
| temporary | string | 0 | "false" |
| link | string | 0 | "https://www.gdacs.org/report.aspx?event |
| pubDate | string | 0 | "Tue, 20 Oct 2026 04:31:52 GMT" |
| dateadded | string | 0 | "Tue, 20 Oct 2026 04:31:52 GMT" |
| datemodified | string | 0 | "Tue, 20 Oct 2026 07:53:43 GMT" |
| iscurrent | string | 0 | "true" |
| fromdate | string | 0 | "Tue, 20 Oct 2026 04:20:38 GMT" |
| todate | string | 0 | "Tue, 20 Oct 2026 04:20:38 GMT" |
| durationinweek | string | 0 | "0" |

Issues: conditional GET gave 0, not 304

### nasa.eonet

- URL: `https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30`
- Content-Type: application/rss+xml; charset=utf-8. Cache-Control: no-cache, private. Expires: -.
- Shape: object, list in key 'events': list of objects
- Time (last item of 'geometry', key 'date'): 2026-09-20 17:32 to 2026-10-20 06:00 UTC, span 29.519 d, step 13.3 h, age of newest 11.9 h
- Top keys: title, description, link, events
- Estimate basis: 1.8 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| id | string | 0.0 | "EONET_25457" |
| title | string | 0.0 | "Tropical Cyclone 02S" |
| description | string | 69.2 | "4 Miles S from Yorkville, CA" |
| link | string | 0.0 | "https://eonet.gsfc.nasa.gov/api/v3/even |
| closed | empty | 100.0 |  |
| categories | nested | 0.0 | [{"id": "severeStorms", "title": "Severe |
| sources | nested | 0.0 | [{"id": "JTWC", "url": "https://www.meto |
| geometry | nested | 0.0 | [{"magnitudeValue": 35.0, "magnitudeUnit |

Issues: no ETag or Last-Modified: compare a hash to detect change

### usgs.volcano-elevated

- URL: `https://volcanoes.usgs.gov/hans-public/api/volcano/getElevatedVolcanoes`
- Content-Type: application/json. Cache-Control: -. Expires: -.
- Shape: list of objects
- Time (column 'sent_unixtime'): 2026-10-15 23:34 to 2026-10-19 20:01 UTC, span 3.853 d, step 46.2 h, age of newest 21.9 h
- Estimate basis: 1.0 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| obs_fullname | string | 0.0 | "Alaska Volcano Observatory" |
| obs_abbr | string | 0.0 | "avo" |
| volcano_name | string | 0.0 | "Great Sitkin" |
| vnum | number | 0.0 | "311120" |
| notice_type_cd | string | 0.0 | "DU" |
| notice_identifier | string | 0.0 | "DOI-USGS-AVO-2026-10-19T19:13:14+00:00" |
| sent_utc | time | 0.0 | "2026-10-19 20:01:42" |
| sent_unixtime | number | 0.0 | 1792440102 |
| color_code | string | 0.0 | "ORANGE" |
| alert_level | string | 0.0 | "WATCH" |
| notice_url | string | 0.0 | "https://volcanoes.usgs.gov/hans-public/ |
| notice_data | string | 0.0 | "https://volcanoes.usgs.gov/hans-public/ |

Issues: no ETag or Last-Modified: compare a hash to detect change

### usgs.volcano-elevated-vsc

- URL: `https://volcanoes.usgs.gov/vsc/api/volcanoApi/elevated`
- Content-Type: text/html; charset=UTF-8. Cache-Control: -. Expires: -.
- Shape: list of objects
- Time (column 'alertDate'): 2026-10-15 23:34 to 2026-10-19 20:01 UTC, span 3.853 d, step 46.2 h, age of newest 21.9 h
- Estimate basis: 1.0 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| noticeId | string | 0.0 | "DOI-USGS-AVO-2026-10-19T19:13:14+00:00" |
| vName | string | 0.0 | "Great Sitkin" |
| vnum | number | 0.0 | "311120" |
| volcanoCd | string | 0.0 | "ak111" |
| nvewsThreat | string | 0.0 | "High Threat" |
| lat | number | 0.0 | 52.0765 |
| long | number | 0.0 | -176.1109 |
| noticeSynopsis | string | 0.0 | "AVO Great Sitkin ORANGE/WATCH - Slow er |
| obs | string | 0.0 | "avo" |
| alertLevel | string | 0.0 | "WATCH" |
| colorCode | string | 0.0 | "ORANGE" |
| sentUtc | time | 0.0 | "2026-10-19 20:01:42" |
| alertDate | time | 0.0 | "2026-10-19 20:01:42" |
| newDate | time | 0.0 | "Oct 19, 2026" |
| newTime | string | 0.0 | "20:01" |
| alertLevelPrev | string | 0.0 | "ADVISORY" |
| colorCodePrev | string | 0.0 | "YELLOW" |
| codeChangeDate | time | 0.0 | "2021-07-23 22:25:55" |
| noticeUrl | string | 0.0 | "https://volcanoes.usgs.gov/hans2/view/n |
| noticeData | string | 0.0 | "https://volcanoes.usgs.gov/vsc/api/hans |
| noticeSectionData | string | 0.0 | "https://volcanoes.usgs.gov/vsc/api/hans |

Issues: no ETag or Last-Modified: compare a hash to detect change

### ndbc.dart-21414

- URL: `https://www.ndbc.noaa.gov/data/realtime2/21414.dart`
- Content-Type: text/plain; charset=ISO-8859-1. Cache-Control: max-age=600, must-revalidate. Expires: -.
- Shape: whitespace table, 8 columns
- Time (columns [0, 1, 2, 3, 4, 5]): 2026-07-27 00:00 to 2026-09-10 18:00 UTC, span 45.75 d, step 60 s, age of newest 959.9 h
- Estimate basis: 199 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| c0 | number | 0.0 | "2026" |
| c1 | number | 0.0 | "09" |
| c2 | number | 0.0 | "10" |
| c3 | number | 0.0 | "18" |
| c4 | number | 0.0 | "00" |
| c5 | number | 0.0 | "00" |
| c6 | number | 0.0 | "1" |
| c7 | number | 0.0 | "5421.034" |

Issues: note: 21413 is offline (404) and 21414 is 40 days old; the adapter must read activestations.xml (76 DART stations) and use only fresh stations; newest data is 40.0 days old (limit 1 d for tier 30m)

### nhc.current-storms

- URL: `https://www.nhc.noaa.gov/CurrentStorms.json`
- Content-Type: application/json. Cache-Control: max-age=300. Expires: Tue, 20 Oct 2026 17:57:11 GMT.
- Shape: object
- Top keys: activeStorms

### ibtracs.active

- URL: `https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.ACTIVE.list.v04r01.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 174 columns
- Time (column 'ISO_TIME'): 2026-10-04 12:00 to 2026-10-20 00:00 UTC, span 15.5 d, step 3.0 h, age of newest 17.9 h
- Estimate basis: 21.9 events/day x 120 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| SID | string | 0.0 | "2026278N11168" |
| SEASON | number | 0.0 | "2026" |
| NUMBER | number | 0.0 | "79" |
| BASIN | string | 0.0 | "WP" |
| SUBBASIN | string | 0.0 | "MM" |
| NAME | string | 0.0 | "KOGUMA" |
| ISO_TIME | time | 0.0 | "2026-10-05 00:00:00" |
| NATURE | string | 0.0 | "NR" |
| LAT | number | 0.0 | "10.5" |
| LON | number | 0.0 | "168.0" |
| WMO_WIND | empty | 100.0 |  |
| WMO_PRES | empty | 100.0 |  |
| WMO_AGENCY | empty | 100.0 |  |
| TRACK_TYPE | string | 0.0 | "PROVISIONAL" |
| DIST2LAND | number | 0.0 | "2262" |
| LANDFALL | number | 1.8 | "2262" |
| IFLAG | string | 0.0 | "O______________" |
| USA_AGENCY | string | 49.1 | "tcvitals" |
| USA_ATCF_ID | string | 0.0 | "WP272026" |
| USA_LAT | number | 0.0 | "10.5" |
| USA_LON | number | 0.0 | "168.0" |
| USA_RECORD | empty | 100.0 |  |
| USA_STATUS | string | 50.0 | "DB" |
| USA_WIND | number | 0.0 | "29" |
| USA_PRES | number | 4.1 | "1002" |
| USA_SSHS | number | 0.0 | "-1" |
| USA_R34_NE | number | 29.7 | "70" |
| USA_R34_SE | number | 29.7 | "50" |
| USA_R34_SW | number | 29.7 | "60" |
| USA_R34_NW | number | 30.0 | "70" |
| ... 144 more | | | |

### firms.viirs-24h-nokey

- URL: `https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 13 columns
- Time (column 'acq_date'): 2026-10-19 00:00 to 2026-10-20 00:00 UTC, span 1.0 d, step 24.0 h, age of newest 17.9 h
- Grid: 100913 points fall in 3859 cells of 1 deg
- Estimate basis: 3859 cells x 5 B x 1 snapshots/day

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| latitude | number | 0.0 | "39.89833" |
| longitude | number | 0.0 | "28.87409" |
| bright_ti4 | number | 0.0 | "295.87" |
| scan | number | 0.0 | "0.43" |
| track | number | 0.0 | "0.38" |
| acq_date | time | 0.0 | "2026-10-19" |
| acq_time | number | 0.0 | "0001" |
| satellite | string | 0.0 | "N" |
| confidence | string | 0.0 | "nominal" |
| version | string | 0.0 | "2.0NRT" |
| bright_ti5 | number | 0.0 | "276.71" |
| frp | number | 0.0 | "0.42" |
| daynight | string | 0.0 | "N" |

Issues: conditional GET gave 200, not 304

### erddap.oisst-nrt-anom

- URL: `https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21NrtAgg.csv?anom%5B(last)%5D%5B(0.0)%5D%5B(-89.875):4:(89.875)%5D%5B(0.125):4:(359.875)%5D`
- Content-Type: text/csv;charset=ISO-8859-1. Cache-Control: -. Expires: -.
- Shape: ERDDAP grid CSV, 180 lat x 360 lon, variable 'anom' (degree_C)
- Time (grid time): 2026-10-19 12:00 to 2026-10-19 12:00 UTC, span 0.0 d, step -, age of newest 29.9 h
- Grid: 43063 of 64800 cells have a value (66.5 %)
- Value range: -5.16 to 7.67
- Estimate basis: 43063 cells x 5 B x 1 snapshots/day

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time |  | 0 | 2026-10-19T12:00:00Z |
| zlev |  | 0 | 0.0 |
| latitude |  | 0 | -89.875 |
| longitude |  | 0 | 0.125 |
| anom |  | 0 | NaN |

### erddap.sla-anom

- URL: `https://coastwatch.pfeg.noaa.gov/erddap/griddap/nesdisSSH1day.csv?sla%5B(last)%5D%5B(-89.875):4:(89.875)%5D%5B(-179.875):4:(179.875)%5D`
- Content-Type: text/csv;charset=ISO-8859-1. Cache-Control: -. Expires: -.
- Shape: ERDDAP grid CSV, 180 lat x 360 lon, variable 'sla' (m)
- Time (grid time): 2026-09-28 00:00 to 2026-09-28 00:00 UTC, span 0.0 d, step -, age of newest 545.9 h
- Grid: 35890 of 64800 cells have a value (55.4 %)
- Value range: -1.366 to 2.012
- Estimate basis: 35890 cells x 5 B x 1 snapshots/day

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| time |  | 0 | 2026-09-28T00:00:00Z |
| latitude |  | 0 | -89.875 |
| longitude |  | 0 | -179.875 |
| sla |  | 0 | NaN |

Issues: note: NRT altimetry lags approx. 3 weeks

### ncei.cag-global-a

- URL: `https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/land_ocean/1/0/1850-2026/data.json`
- Content-Type: application/json. Cache-Control: no-store, no-cache, must-revalidate. Expires: Thu, 19 Nov 1981 08:52:00 GMT.
- Shape: object, key 'data' maps 2121 keys to records
- Time (column '_key' (%Y%m)): 1850-01-01 00:00 to 2026-09-01 00:00 UTC, span 64526.0 d, step 31.0 d, age of newest 1193.9 h
- Top keys: description, data
- Estimate basis: 0 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| departure | number | 0.0 | -0.43 |
| _key | number | 0.0 | "185001" |

Issues: no ETag or Last-Modified: compare a hash to detect change

### ncei.cag-global-b

- URL: `https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/tavg/land_ocean/1/0/1850-2026/data.json`
- Content-Type: application/json. Cache-Control: no-store, no-cache, must-revalidate. Expires: Thu, 19 Nov 1981 08:52:00 GMT.
- Shape: object, key 'data' maps 2121 keys to records
- Time (column '_key' (%Y%m)): 1850-01-01 00:00 to 2026-09-01 00:00 UTC, span 64526.0 d, step 31.0 d, age of newest 1193.9 h
- Top keys: description, data
- Estimate basis: 0 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| departure | number | 0.0 | -0.43 |
| _key | number | 0.0 | "185001" |

Issues: no ETag or Last-Modified: compare a hash to detect change

### giss.gistemp

- URL: `https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 19 columns
- Time (column 'Year' (%Y)): 1880-01-01 00:00 to 2026-01-01 00:00 UTC, span 53326.0 d, step 365.0 d, age of newest 7025.9 h
- Estimate basis: 0 rows/day x 18 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| Year | number | 0.0 | "1880" |
| Jan | number | 0.0 | "-.19" |
| Feb | number | 0.0 | "-.25" |
| Mar | number | 0.0 | "-.09" |
| Apr | number | 0.0 | "-.16" |
| May | number | 0.0 | "-.10" |
| Jun | number | 0.0 | "-.21" |
| Jul | number | 0.0 | "-.19" |
| Aug | number | 0.0 | "-.10" |
| Sep | number | 0.0 | "-.15" |
| Oct | number | 0.0 | "-.23" |
| Nov | number | 0.0 | "-.22" |
| Dec | number | 0.0 | "-.18" |
| J-D | number | 0.0 | "-.17" |
| D-N | number | 0.0 | "***" |
| DJF | number | 0.0 | "***" |
| MAM | number | 0.0 | "-.12" |
| JJA | number | 0.0 | "-.17" |
| SON | number | 0.0 | "-.20" |

Issues: conditional GET gave 0, not 304

### gml.co2-daily-mlo

- URL: `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_daily_mlo.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 5 columns
- Time (columns [0, 1, 2]): 1974-05-19 00:00 to 2026-10-19 00:00 UTC, span 19146.0 d, step 24.0 h, age of newest 41.9 h
- Estimate basis: 1 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| c0 | number | 0.0 | "1974" |
| c1 | number | 0.0 | "5" |
| c2 | number | 0.0 | "19" |
| c3 | number | 0.0 | "1974.3781" |
| c4 | number | 0.0 | "333.46" |

### gml.co2-monthly-mlo

- URL: `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 8 columns
- Time (columns [0, 1]): 1958-03-15 00:00 to 2026-09-15 00:00 UTC, span 25021.0 d, step 31.0 d, age of newest 857.9 h
- Estimate basis: 0 rows/day x 6 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1958" |
| month | number | 0.0 | "3" |
| decimal date | number | 0.0 | "1958.2027" |
| average | number | 0.0 | "315.71" |
| deseasonalized | number | 0.0 | "314.44" |
| ndays | number | 0.0 | "-1" |
| sdev | number | 0.0 | "-9.99" |
| unc | number | 0.0 | "-0.99" |

### gml.co2-monthly-gl

- URL: `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 7 columns
- Time (columns [0, 1]): 1979-01-15 00:00 to 2026-07-15 00:00 UTC, span 17348.0 d, step 31.0 d, age of newest 2345.9 h
- Estimate basis: 0 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1979" |
| month | number | 0.0 | "1" |
| decimal | number | 0.0 | "1979.042" |
| average | number | 0.0 | "336.56" |
| average_unc | number | 0.0 | "0.10" |
| trend | number | 0.0 | "335.92" |
| trend_unc | number | 0.0 | "0.09" |

### gml.ch4-monthly-gl

- URL: `https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 7 columns
- Time (columns [0, 1]): 1983-07-15 00:00 to 2026-06-15 00:00 UTC, span 15676.0 d, step 31.0 d, age of newest 3065.9 h
- Estimate basis: 0 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1983" |
| month | number | 0.0 | "7" |
| decimal | number | 0.0 | "1983.542" |
| average | number | 0.0 | "1625.96" |
| average_unc | number | 0.0 | "2.25" |
| trend | number | 0.0 | "1635.11" |
| trend_unc | number | 0.0 | "1.50" |

### gml.n2o-monthly-gl

- URL: `https://gml.noaa.gov/webdata/ccgg/trends/n2o/n2o_mm_gl.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 7 columns
- Time (columns [0, 1]): 2001-01-15 00:00 to 2026-06-15 00:00 UTC, span 9282.0 d, step 31.0 d, age of newest 3065.9 h
- Estimate basis: 0 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "2001" |
| month | number | 0.0 | "1" |
| decimal | number | 0.0 | "2001.042" |
| average | number | 0.0 | "316.30" |
| average_unc | number | 0.0 | "0.14" |
| trend | number | 0.0 | "316.03" |
| trend_unc | number | 0.0 | "0.13" |

### gml.sf6-monthly-gl

- URL: `https://gml.noaa.gov/webdata/ccgg/trends/sf6/sf6_mm_gl.csv`
- Content-Type: text/csv. Cache-Control: -. Expires: -.
- Shape: CSV, 7 columns
- Time (columns [0, 1]): 1997-07-15 00:00 to 2026-06-15 00:00 UTC, span 10562.0 d, step 31.0 d, age of newest 3065.9 h
- Estimate basis: 0 rows/day x 5 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1997" |
| month | number | 0.0 | "7" |
| decimal | number | 0.0 | "1997.542" |
| average | number | 0.0 | "4.00" |
| average_unc | number | 0.0 | "0.01" |
| trend | number | 0.0 | "4.01" |
| trend_unc | number | 0.0 | "0.00" |

### nsidc.north-v4

- URL: `https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv`
- Content-Type: application/octet-stream. Cache-Control: -. Expires: -.
- Shape: CSV, 6 columns
- Time (columns [0, 1, 2]): 1978-10-26 00:00 to 2026-10-17 00:00 UTC, span 17523.0 d, step 24.0 h, age of newest 89.9 h
- Estimate basis: 1 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| Year | number | 0.0 | "1978" |
| Month | number | 0.0 | "10" |
| Day | number | 0.0 | "26" |
| Extent | number | 0.0 | "10.231" |
| Missing | number | 0.0 | "0.000" |
| Source Data | string | 0.0 | "['/ecs/DP1/PM/NSIDC-0051.001/1978.10.26 |

### nsidc.south-v4

- URL: `https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v4.0.csv`
- Content-Type: application/octet-stream. Cache-Control: -. Expires: -.
- Shape: CSV, 6 columns
- Time (columns [0, 1, 2]): 1978-10-26 00:00 to 2026-10-17 00:00 UTC, span 17523.0 d, step 24.0 h, age of newest 89.9 h
- Estimate basis: 1 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| Year | number | 0.0 | "1978" |
| Month | number | 0.0 | "10" |
| Day | number | 0.0 | "26" |
| Extent | number | 0.0 | "17.624" |
| Missing | number | 0.0 | "0.000" |
| Source Data | string | 0.0 | "['/ecs/DP1/PM/NSIDC-0051.001/1978.10.26 |

### cpc.oni

- URL: `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`
- Content-Type: text/plain; charset=utf-8. Cache-Control: max-age=0, no-store, no-cache, must-revalidate. Expires: 0.
- Shape: whitespace table, 4 columns
- Time (season column 0 + year column 1): 1950-01-15 00:00 to 2026-08-15 00:00 UTC, span 27971.0 d, step 31.0 d, age of newest 1601.9 h
- Estimate basis: 0 rows/day x 2 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| SEAS | string | 0.0 | "DJF" |
| YR | number | 0.0 | "1950" |
| TOTAL | number | 0.0 | "25.01" |
| ANOM | number | 0.0 | "-1.32" |

### cpc.nino-weekly

- URL: `https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for`
- Content-Type: -. Cache-Control: max-age=0, no-store, no-cache, must-revalidate. Expires: 0.
- Shape: text, 2359 lines
- First lines: Weekly SST data starts week centered on 2Sept1981 / Nino1+2      Nino3        Nino34        Nino4 / Week          SST SSTA     SST SSTA     SST SSTA     SST SSTA

### cpc.ao-daily

- URL: `https://ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.ao.cdas.z1000.19500101_current.csv`
- Content-Type: text/csv. Cache-Control: private. Expires: -.
- Shape: CSV, 4 columns
- Time (columns [0, 1, 2]): 1950-01-01 00:00 to 2026-10-18 00:00 UTC, span 28049.0 d, step 24.0 h, age of newest 65.9 h
- Estimate basis: 1 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1950" |
| month | number | 0.0 | "1" |
| day | number | 0.0 | "1" |
| ao_index_cdas | number | 0.0 | "-2.5114431381225586" |

### cpc.nao-daily

- URL: `https://ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.nao.cdas.z500.19500101_current.csv`
- Content-Type: text/csv. Cache-Control: private. Expires: -.
- Shape: CSV, 4 columns
- Time (columns [0, 1, 2]): 1950-01-01 00:00 to 2026-10-18 00:00 UTC, span 28049.0 d, step 24.0 h, age of newest 65.9 h
- Estimate basis: 1 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1950" |
| month | number | 0.0 | "1" |
| day | number | 0.0 | "1" |
| nao_index_cdas | number | 0.0 | "0.36500000953674316" |

### cpc.aao-daily

- URL: `https://ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.aao.cdas.z700.19790101_current.csv`
- Content-Type: text/csv. Cache-Control: private. Expires: -.
- Shape: CSV, 4 columns
- Time (columns [0, 1, 2]): 1979-01-01 00:00 to 2026-10-18 00:00 UTC, span 17457.0 d, step 24.0 h, age of newest 65.9 h
- Estimate basis: 1 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1979" |
| month | number | 0.0 | "1" |
| day | number | 0.0 | "1" |
| aao_index_cdas | number | 0.0 | "-1.5563026666641235" |

### cpc.pna-daily

- URL: `https://ftp.cpc.ncep.noaa.gov/cwlinks/norm.daily.pna.cdas.z500.19500101_current.csv`
- Content-Type: text/csv. Cache-Control: private. Expires: -.
- Shape: CSV, 4 columns
- Time (columns [0, 1, 2]): 1950-01-01 00:00 to 2026-10-18 00:00 UTC, span 28049.0 d, step 24.0 h, age of newest 65.9 h
- Estimate basis: 1 rows/day x 1 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| year | number | 0.0 | "1950" |
| month | number | 0.0 | "1" |
| day | number | 0.0 | "1" |
| pna_index_cdas | number | 0.0 | "-1.3320000171661377" |

### nasa.ozone-hole

- URL: `https://ozonewatch.gsfc.nasa.gov/meteorology/figures/ozone/to3areas_2026_toms+omi+omps.txt`
- Content-Type: text/plain; charset=utf-8. Cache-Control: -. Expires: -.
- Shape: whitespace table, 4 columns
- Time (column 'Name:'): 2026-01-01 00:00 to 2026-12-31 00:00 UTC, span 364.0 d, step 24.0 h, age of newest -1710.1 h
- Estimate basis: 1 rows/day x 8 cols x 5 B

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| Name: | time | 0.0 | "Units:" |
| Ozone | number | 22.2 | "Million" |
| Hole | number | 0.5 | "km!U2!N" |
| Area | number | 0.8 | "2025" |
| c4 | number | 1.1 | "30%" |
| c5 | number | 1.1 | "Mean" |
| c6 | number | 1.1 | "70%" |
| c7 | number | 1.1 | "90%" |
| c8 | number | 1.1 | "Maximum" |

Issues: note: file has empty rows for the rest of the year; the season is Aug to Dec

### static.ne-110m-coastline

- URL: `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_coastline.geojson`
- Content-Type: text/plain; charset=utf-8. Cache-Control: max-age=300. Expires: Tue, 20 Oct 2026 17:59:05 GMT.
- Shape: GeoJSON, 134 features, geometry {'LineString': 134}

| Column | Type | Null % | Sample |
| --- | --- | --- | --- |
| scalerank | number | 0.0 | 1 |
| featurecla | string | 0.0 | "Coastline" |
| min_zoom | number | 0.0 | 1 |

## Discovery

### swpc.index.products

`https://services.swpc.noaa.gov/products/` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| animations/ | 2026-07-23 16:57 | - |
| ccor1/ | 2025-04-07 17:27 | - |
| ccor2/ | 2026-07-23 17:55 | - |
| flares/ | 2025-09-26 19:42 | - |
| geospace/ | 2024-06-20 21:37 | - |
| glotec/ | 2025-02-20 07:12 | - |
| gong/ | 2024-06-20 21:38 | - |
| summary/ | 2026-06-30 20:57 | - |
| 10cm-flux-30-day.json | 2026-10-20 17:53 | 1.3K |
| alerts.json | 2026-10-20 17:53 | 53K |
| kyoto-dst.json | 2026-10-20 17:53 | 7.3K |
| noaa-planetary-k-index-forecast.json | 2026-10-20 17:53 | 6.7K |
| noaa-planetary-k-index.json | 2026-10-20 17:53 | 4.6K |
| noaa-scales.json | 2026-10-20 17:53 | 1.1K |
| solar-cycle-25-f10-7-predicted-range.json | 2022-12-09 21:05 | 22K |
| solar-cycle-25-ssn-predicted-range.json | 2022-09-30 18:21 | 26K |

### swpc.index.json

`https://services.swpc.noaa.gov/json/` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| ace/ | 2024-06-24 18:31 | - |
| geospace/ | 2026-09-09 17:04 | - |
| goes/ | 2024-06-13 16:44 | - |
| lists/ | 2024-06-20 21:37 | - |
| rtsw/ | 2026-06-10 15:39 | - |
| solar-cycle/ | 2025-04-09 17:13 | - |
| stereo/ | 2024-06-24 18:32 | - |
| 45-day-forecast.json | 2026-10-20 17:53 | 6.1K |
| boulder_k_index_1m.json | 2026-10-20 17:51 | 84K |
| edited_events.json | 2026-10-20 17:51 | 381K |
| electron_fluence_forecast.json | 2026-10-20 17:53 | 8.8K |
| enlil_time_series.json | 2026-10-20 17:51 | 1.4M |
| f107_cm_flux.json | 2026-10-20 17:51 | 22K |
| icao-space-weather-advisories.json | 2026-06-09 15:23 | 2 |
| ovation_aurora_latest.json | 2026-10-20 17:53 | 903K |
| planetary_k_index_1m.json | 2026-10-20 17:51 | 27K |
| predicted_f107cm_flux.json | 2026-10-20 17:51 | 2.6K |
| predicted_fredericksburg_a_index.json | 2026-10-20 17:51 | 2.1K |
| predicted_monthly_sunspot_number.json | 2026-10-20 17:51 | 6.8K |
| solar-radio-flux.json | 2026-10-20 17:52 | 49K |
| solar_probabilities.json | 2026-10-20 17:51 | 8.9K |
| solar_regions.json | 2026-10-20 17:51 | 127K |
| sunspot_report.json | 2026-10-20 17:51 | 161K |

### swpc.index.goes-primary

`https://services.swpc.noaa.gov/json/goes/primary/` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| differential-alphas-1-day.json | 2026-10-20 17:52 | 403K |
| differential-alphas-3-day.json | 2026-10-20 17:52 | 1.2M |
| differential-alphas-6-hour.json | 2026-10-20 17:52 | 100K |
| differential-alphas-7-day.json | 2026-10-20 17:52 | 2.8M |
| differential-electrons-1-day.json | 2026-10-20 17:52 | 276K |
| differential-electrons-3-day.json | 2026-10-20 17:52 | 829K |
| differential-electrons-6-hour.json | 2026-10-20 17:52 | 70K |
| differential-electrons-7-day.json | 2026-10-20 17:52 | 1.9M |
| differential-protons-1-day.json | 2026-10-20 17:52 | 523K |
| differential-protons-3-day.json | 2026-10-20 17:52 | 1.5M |
| differential-protons-6-hour.json | 2026-10-20 17:52 | 130K |
| differential-protons-7-day.json | 2026-10-20 17:52 | 3.6M |
| euvs-1-day.json | 2026-10-20 17:52 | 2.3M |
| euvs-3-day.json | 2026-10-20 17:52 | 6.8M |
| euvs-6-hour.json | 2026-10-20 17:52 | 581K |
| euvs-7-day.json | 2026-10-20 17:52 | 16M |
| integral-electron-fluence-7-day.json | 2026-10-20 17:52 | 800 |
| integral-electrons-1-day.json | 2026-10-20 17:52 | 29K |
| integral-electrons-3-day.json | 2026-10-20 17:52 | 87K |
| integral-electrons-6-hour.json | 2026-10-20 17:52 | 7.1K |
| integral-electrons-7-day.json | 2026-10-20 17:52 | 203K |
| integral-proton-fluence-7-day.json | 2026-10-20 17:52 | 1.5K |
| integral-protons-1-day.json | 2026-10-20 17:52 | 237K |
| integral-protons-3-day.json | 2026-10-20 17:52 | 711K |
| integral-protons-6-hour.json | 2026-10-20 17:52 | 59K |
| integral-protons-7-day.json | 2026-10-20 17:52 | 1.6M |
| integral-protons-plot-1-day.json | 2026-10-20 17:52 | 119K |
| integral-protons-plot-3-day.json | 2026-10-20 17:52 | 357K |
| integral-protons-plot-6-hour.json | 2026-10-20 17:52 | 29K |
| integral-protons-plot-7-day.json | 2026-10-20 17:52 | 835K |
| magnetometers-1-day.json | 2026-10-20 17:52 | 256K |
| magnetometers-3-day.json | 2026-10-20 17:52 | 768K |
| magnetometers-6-hour.json | 2026-10-20 17:52 | 64K |
| magnetometers-7-day.json | 2026-10-20 17:52 | 1.7M |
| suvi-flares-7-day.json | 2026-10-20 17:52 | 7.6K |
| suvi-flares-latest.json | 2026-10-20 17:52 | 432 |
| xray-background-7-day.json | 2026-10-20 17:52 | 551 |
| xray-flares-7-day.json | 2026-10-20 17:52 | 29K |
| xray-flares-latest.json | 2026-10-20 17:52 | 454 |
| xrays-1-day.json | 2026-10-20 17:52 | 640K |
| xrays-3-day.json | 2026-10-20 17:52 | 1.9M |
| xrays-6-hour.json | 2026-10-20 17:52 | 158K |
| xrays-7-day.json | 2026-10-20 17:52 | 4.4M |

### swpc.index.rtsw

`https://services.swpc.noaa.gov/json/rtsw/` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| rtsw_ephemerides_1h.json | 2026-10-20 17:52 | 760K |
| rtsw_mag_1m.json | 2026-10-20 17:52 | 1.5M |
| rtsw_wind_1m.json | 2026-10-20 17:52 | 2.5M |

### swpc.index.text

`https://services.swpc.noaa.gov/text/` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| rtsw/ | 2024-03-28 05:01 | - |
| scn/ | 2026-02-26 20:54 | - |
| 27-day-outlook.txt | 2026-10-20 17:53 | 1.6K |
| 3-day-forecast.txt | 2026-10-20 17:53 | 1.7K |
| 3-day-geomag-forecast.txt | 2026-10-20 17:53 | 879 |
| 3-day-solar-geomag-predictions.txt | 2026-10-20 17:53 | 2.6K |
| 45-day-forecast.txt | 2026-10-20 17:53 | 1.5K |
| ace-epam.txt | 2026-10-20 17:53 | 3.7K |
| ace-magnetometer.txt | 2026-10-20 17:53 | 11K |
| ace-sis.txt | 2026-10-20 17:53 | 2.3K |
| ace-swepam.txt | 2026-10-20 17:53 | 9.3K |
| advisory-outlook.txt | 2026-10-20 17:53 | 758 |
| aurora-nowcast-hemi-power.txt | 2026-10-20 17:51 | 12K |
| current-space-weather-indices.txt | 2026-10-20 17:53 | 1.9K |
| daily-geomagnetic-indices.txt | 2026-10-20 17:53 | 3.8K |
| daily-solar-indices.txt | 2026-10-20 17:53 | 2.9K |
| discussion.txt | 2026-10-20 17:53 | 2.8K |
| drap_global_frequencies.txt | 2026-10-20 17:52 | 41K |
| geoalert.txt | 2026-10-20 17:53 | 565 |
| magnetometer-analysis.txt | 2024-06-19 02:21 | 1.8K |
| ovation_latest_aurora_n.txt | 2026-10-20 17:51 | 556K |
| ovation_latest_aurora_s.txt | 2026-10-20 17:51 | 563K |
| relativistic-electron-fluence-statistics.txt | 2026-10-20 17:53 | 1.2K |
| relativistic-electron-fluence-tabular.txt | 2026-10-20 17:53 | 4.1K |
| sgarf.txt | 2026-10-20 17:53 | 1.9K |
| sgas.txt | 2026-10-20 17:53 | 1.1K |
| solar-geophysical-event-reports.txt | 2026-10-20 17:53 | 1.7K |
| solar-regions.txt | 2026-10-20 17:53 | 699 |
| solar_radio_flux.txt | 2026-10-20 17:51 | 5.4K |
| srs.txt | 2026-10-20 17:53 | 783 |
| storm-corrections-today.txt | 2026-10-20 17:53 | 1.6K |
| storm-corrections-yesterday.txt | 2026-10-20 17:53 | 1.0K |
| storm-errors-today.txt | 2026-10-20 17:53 | 2.2K |
| storm-errors-yesterday.txt | 2026-10-20 17:53 | 1.0K |
| tracking-frames-1-day-utc.json | 2026-07-07 19:13 | 33 |
| tracking-frames-1-day.json | 2026-07-07 19:13 | 33 |
| tracking-frames-3-day-utc.json | 2026-07-07 19:13 | 33 |
| tracking-frames-3-day.json | 2026-07-07 19:13 | 33 |
| tracking-frames-7-day-utc.json | 2026-07-07 19:13 | 33 |
| tracking-frames-7-day.json | 2026-07-07 19:13 | 33 |
| tracking-frames-ace-1-day-utc.json | 2026-07-07 19:13 | 2.7K |
| tracking-frames-ace-1-day.json | 2026-07-07 19:13 | 2.2K |
| tracking-frames-ace-3-day-utc.json | 2026-07-07 19:13 | 5.1K |
| tracking-frames-ace-3-day.json | 2026-07-07 19:13 | 4.5K |
| tracking-frames-ace-7-day-utc.json | 2026-07-07 19:13 | 11K |
| tracking-frames-ace-7-day.json | 2026-07-07 19:13 | 11K |
| tracking-schedule-1-day-utc.json | 2026-07-07 19:13 | 497 |
| tracking-schedule-1-day.json | 2026-07-07 19:13 | 586 |
| tracking-schedule-3-day-utc.json | 2026-07-07 19:13 | 853 |
| tracking-schedule-3-day.json | 2026-07-07 19:13 | 942 |
| tracking-schedule-7-day-utc.json | 2026-07-07 19:13 | 2.7K |
| tracking-schedule-7-day.json | 2026-07-07 19:13 | 2.7K |
| weekly.txt | 2026-10-20 17:53 | 1.9K |
| wwv.txt | 2026-10-20 17:53 | 538 |

### swpc.index.solar-cycle

`https://services.swpc.noaa.gov/json/solar-cycle/` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| 2019-predicted-solar-cycle.json | 2026-10-20 17:53 | 25K |
| cycle_update.png | 2026-10-20 17:53 | 163K |
| f10-7cm-flux-smoothed.json | 2026-10-20 17:53 | 17K |
| f10-7cm-flux.json | 2026-10-20 17:53 | 11K |
| observed-solar-cycle-indices.json | 2026-10-20 17:53 | 500K |
| predicted-solar-cycle.json | 2026-10-20 17:53 | 17K |
| solar-cycle-25-f10-7cm-flux-predicted-high-low.json | 2026-10-20 17:53 | 71K |
| solar-cycle-25-predicted.json | 2026-10-20 17:53 | 17K |
| solar-cycle-25-ssn-predicted-high-low.json | 2026-10-20 17:53 | 88K |
| sunspots-smoothed.json | 2026-10-20 17:53 | 154K |
| sunspots.json | 2026-10-20 17:53 | 124K |
| swpc_observed_ssn.json | 2026-10-20 17:51 | 466K |

### usgs.geomag-observatories

`https://geomag.usgs.gov/ws/observatories/` · HTTP 200 

- Shape: GeoJSON, 43 features, geometry {'Point': 42, 'none': 1}

### ndbc.active-stations

`https://www.ndbc.noaa.gov/activestations.xml` · HTTP 200 

- Shape: XML <stations>, 1352 <station> children

### erddap.oisst-nrt-info

`https://coastwatch.pfeg.noaa.gov/erddap/info/ncdcOisst21NrtAgg/index.csv` · HTTP 200 

- title: SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2.1, Preliminary, Glo
- time_coverage_start: 2020-05-04T12:00:00Z
- time_coverage_end: 2026-10-19T12:00:00Z
- dimensions: time: nValues=2331, evenlySpaced=false, averageSpacing=1 day 0h 17m 55s; zlev: nValues=1, onlyValue=0.0; latitude: nValues=720, evenlySpaced=true, averageSpacing=0.25; longitude: nValues=1440, evenlyS
- variables: sst, anom, err, ice
- Shape: ERDDAP dataset info

### erddap.search-sla

`https://coastwatch.pfeg.noaa.gov/erddap/search/index.csv?page=1&itemsPerPage=40&searchFor=sea%20level%20anomaly%20global%20daily` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| nesdisSSH1day | griddap | NOAA CoastWatch, Sea Surface Height Anomalies and Geostrophic Currents from Altimetry, Global, 2017-present, E |
| nesdisSSH1day_Lon0360 | griddap | NOAA CoastWatch, Sea Surface Height Anomalies and Geostrophic Currents from Altimetry, Global, 2017-present, E |
| ncdcOisst21Agg | griddap | SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2.1, Final, Global, 0.25\u00b0, 1981-present |
| jplMURSST42mday | griddap | Multi-scale Ultra-high Resolution (MUR) SST Analysis fv04.2, Global, 0.25\u00b0,\n2002-present, Monthly |
| ncdcOisst21NrtAgg | griddap | SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2.1, Preliminary, Global, 0.25\u00b0, 2020-present |
| ncdcOisst21Agg_LonPM180 | griddap | SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2.1, Final, Global, 0.25\u00b0, 1981-present, Lon+/ |
| jplMURSST42mday_Lon0360 | griddap | Multi-scale Ultra-high Resolution (MUR) SST Analysis fv04.2, Global, 0.25\u00b0,\n2002-present, Monthly, Lon03 |
| ncdcOisst21NrtAgg_LonPM180 | griddap | SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2.1, Preliminary, Global, 0.25\u00b0, 2020-present, |
| jplMURSST42 | griddap | Multi-scale High Resolution (MUR) SST Analysis, SST Anomaly, fv04.2, Global, 0.25\u00b0, 2002-present |
| NOAA_DHW | griddap | NOAA Coral Reef Watch Operational Daily Near-Real-Time Global 5-km Satellite Coral Bleaching Monitoring Produc |
| pmelTaoDyDyn | tabledap | TAO/TRITON, RAMA, and PIRATA Buoys, Daily, 1980-present, Dynamic Height |
| ncdcOisst2Agg | griddap | SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2, Final, Global, 0.25\u00b0;, 1982-2020 |
| ncdcOisst2Agg_LonPM180 | griddap | SST, Daily Optimum Interpolation (OI), AVHRR Only, Version 2, Final, Global, 0.25\u00b0;, 1982-2020, Lon+/-180 |
| pmelTaoMonDyn | tabledap | TAO/TRITON, RAMA, and PIRATA Buoys, Monthly, 1980-present, Dynamic Height |
| pmelTao5dayDyn | tabledap | TAO/TRITON, RAMA, and PIRATA Buoys, 5-Day, 1980-present, Dynamic Height |

### erddap.search-crw

`https://coastwatch.pfeg.noaa.gov/erddap/search/index.csv?page=1&itemsPerPage=40&searchFor=coral%20reef%20watch%20degree%20heating%20week%20daily` · HTTP 200 

| Name | Modified / type | Size / title |
| --- | --- | --- |
| NOAA_DHW | griddap | NOAA Coral Reef Watch Operational Daily Near-Real-Time Global 5-km Satellite Coral Bleaching Monitoring Produc |

