# Data sources, attribution, and licenses

This file comes from `sources.json` v0.3.0. Do not edit it by hand. Run `python3 tools/sources_md.py`.

This dashboard is not an official warning service. Each alert links to the official issuer.

The pipeline uses data services only. It sends the User-Agent `public-data-dashboard/<VERSION> (+<repository URL>)` and obeys rate limits, `Retry-After`, and cache headers. Two sources use a free key. The keys are GitHub secrets (`NASA_API_KEY`, `FIRMS_MAP_KEY`). No file contains a key.

Legend: [L] = the license is not a US Government license. Show the attribution.

## Space weather and near space

| Dataset | ID | Source | Attribution | License | Tier | Status |
| --- | --- | --- | --- | --- | --- | --- |
| NOAA space weather scales R/S/G | `space.scales` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| SWPC alerts, watches, warnings | `space.alerts` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| Planetary Kp (3 h) | `space.kp` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| Estimated Kp (1 min) | `space.kp-1m` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| Kp forecast | `space.kp-forecast` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1h | ok |
| GOES X-ray flux (2 channels) | `space.xray` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| GOES X-ray flare list | `space.xray-flares` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1h | ok |
| GOES integral protons (5 min) | `space.protons` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| GOES integral electrons (5 min) | `space.electrons` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| GOES magnetometer (1 min) | `space.goes-mag` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| Solar wind plasma (1 min): speed, density, temperature | `space.sw-plasma` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| Solar wind magnetic field (1 min): Bt, Bx, By, Bz GSM | `space.sw-mag` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| OVATION aurora probability grid | `space.aurora` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1h | ok |
| Aurora hemispheric power | `space.hemi-power` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 30m | ok |
| Dst index (WDC Kyoto via SWPC) [L] | `space.dst` | services.swpc.noaa.gov | WDC for Geomagnetism, Kyoto (via NOAA SWPC) | WDC Kyoto: non-commercial use, attribution required | 1h | ok |
| WSA-Enlil solar wind prediction | `space.enlil` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1h | ok |
| 3-day forecast (text) | `space.3day-forecast` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1h | ok |
| Forecast discussion (text) | `space.discussion` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1h | ok |
| 27-day outlook (text) | `space.27day` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1d | ok |
| F10.7 cm solar radio flux | `space.f107` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1d | ok |
| 45-day Ap and F10.7 forecast | `space.45day` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1d | ok |
| Flare and proton event probabilities | `space.flare-prob` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1d | ok |
| Solar active regions | `space.solar-regions` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1d | ok |
| Solar cycle observed indices (monthly) | `space.cycle-observed` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1w | ok |
| Solar cycle prediction | `space.cycle-predicted` | services.swpc.noaa.gov | NOAA SWPC | US Government work | 1w | ok |
| NASA DONKI CME | `space.donki-cme` | api.nasa.gov (key: `NASA_API_KEY`) | NASA CCMC DONKI | US Government work | 1h | key |
| NASA DONKI FLR | `space.donki-flr` | api.nasa.gov (key: `NASA_API_KEY`) | NASA CCMC DONKI | US Government work | 1h | key |
| NASA DONKI GST | `space.donki-gst` | api.nasa.gov (key: `NASA_API_KEY`) | NASA CCMC DONKI | US Government work | 1h | key |
| NASA DONKI notifications | `space.donki-notifications` | api.nasa.gov (key: `NASA_API_KEY`) | NASA CCMC DONKI | US Government work | 1h | key |
| NEO close approaches (next 60 days, < 0.05 au) | `space.neo-cad` | ssd-api.jpl.nasa.gov | NASA JPL CNEOS | US Government work | 1d | ok |
| Fireballs | `space.fireballs` | ssd-api.jpl.nasa.gov | NASA JPL CNEOS | US Government work | 1d | ok |
| Sentry impact risk list | `space.sentry` | ssd-api.jpl.nasa.gov | NASA JPL CNEOS | US Government work | 1d | ok |
| USGS ground magnetometers H, D, Z (1 min) | `space.geomag` | geomag.usgs.gov | USGS Geomagnetism Program | US Government work | 1h | ok |
| SILSO daily sunspot number [L] | `space.ssn-daily` | www.sidc.be | SILSO, Royal Observatory of Belgium | CC BY-NC 4.0 | 1w | ok |
| SILSO estimated international sunspot number [L] | `space.ssn-estimated` | www.sidc.be | SILSO, Royal Observatory of Belgium | CC BY-NC 4.0 | 1d | ok |

## Geohazards

| Dataset | ID | Source | Attribution | License | Tier | Status |
| --- | --- | --- | --- | --- | --- | --- |
| USGS earthquakes M2.5+ | `geo.quakes` | earthquake.usgs.gov | USGS Earthquake Hazards Program | US Government work | 30m | ok |
| Tsunami messages NTWC | `geo.tsunami-ntwc` | www.tsunami.gov | NOAA/NWS Tsunami Warning Centers | US Government work | 30m | ok |
| Tsunami messages PTWC | `geo.tsunami-ptwc` | www.tsunami.gov | NOAA/NWS Tsunami Warning Centers | US Government work | 30m | ok |
| GDACS global disaster alerts [L] | `geo.gdacs` | www.gdacs.org | GDACS (EC JRC, UN OCHA) | GDACS terms: attribution required | 30m | ok |
| NASA EONET natural events | `geo.eonet` | eonet.gsfc.nasa.gov | NASA EONET | US Government work | 1h | ok |
| USGS elevated volcanoes | `geo.volcanoes` | volcanoes.usgs.gov | USGS Volcano Hazards Program | US Government work | 1d | ok |
| NDBC DART tsunami buoys (water column height) | `geo.dart` | www.ndbc.noaa.gov | NOAA NDBC | US Government work | 30m | ok |

## Global weather events

| Dataset | ID | Source | Attribution | License | Tier | Status |
| --- | --- | --- | --- | --- | --- | --- |
| NHC/CPHC active tropical storms | `weather.nhc` | www.nhc.noaa.gov | NOAA National Hurricane Center | US Government work | 30m | ok |
| IBTrACS active storm tracks (global) | `weather.ibtracs` | www.ncei.noaa.gov | NOAA NCEI IBTrACS | US Government work | 1h | ok |
| Active fires (VIIRS, 24 h), 1 deg cell counts | `weather.fires` | firms.modaps.eosdis.nasa.gov | NASA FIRMS | US Government work | 1h | ok |

## Global ocean

| Dataset | ID | Source | Attribution | License | Tier | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Sea surface temperature anomaly (OISST v2.1 NRT), 1 deg | `ocean.sst-anom` | coastwatch.pfeg.noaa.gov | NOAA NCEI OISST via NOAA CoastWatch ERDDAP | US Government work | 1d | ok |
| Sea level anomaly (altimetry), 1 deg | `ocean.sla` | coastwatch.pfeg.noaa.gov | NOAA CoastWatch | US Government work | 1d | ok |
| Coral bleaching alert area, 7-day max, 2 deg | `ocean.coral-alert` | coastwatch.pfeg.noaa.gov | NOAA Coral Reef Watch | US Government work | 1d | runner |

## Climate records

| Dataset | ID | Source | Attribution | License | Tier | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Global land and ocean temperature anomaly (NCEI, monthly) | `climate.temp-ncei` | www.ncei.noaa.gov | NOAA NCEI Climate at a Glance | US Government work | 1w | ok |
| Global temperature anomaly (NASA GISTEMP v4, monthly) | `climate.temp-gistemp` | data.giss.nasa.gov | NASA GISS GISTEMP v4 | US Government work | 1w | ok |
| CO2 daily, Mauna Loa | `climate.co2-daily` | gml.noaa.gov | NOAA GML | US Government work | 1d | ok |
| CO2 monthly, Mauna Loa | `climate.co2-monthly` | gml.noaa.gov | NOAA GML | US Government work | 1w | ok |
| CO2 global monthly mean | `climate.co2-global` | gml.noaa.gov | NOAA GML | US Government work | 1w | ok |
| CH4 global monthly mean | `climate.ch4-global` | gml.noaa.gov | NOAA GML | US Government work | 1w | ok |
| N2O global monthly mean | `climate.n2o-global` | gml.noaa.gov | NOAA GML | US Government work | 1w | ok |
| SF6 global monthly mean | `climate.sf6-global` | gml.noaa.gov | NOAA GML | US Government work | 1w | ok |
| Arctic sea ice extent (daily) | `climate.seaice-north` | noaadata.apps.nsidc.org | NSIDC Sea Ice Index G02135 v4 | US Government work | 1d | ok |
| Antarctic sea ice extent (daily) | `climate.seaice-south` | noaadata.apps.nsidc.org | NSIDC Sea Ice Index G02135 v4 | US Government work | 1d | ok |
| ENSO Oceanic Nino Index | `climate.oni` | www.cpc.ncep.noaa.gov | NOAA CPC | US Government work | 1w | ok |
| Weekly Nino region SST and anomaly | `climate.nino-weekly` | www.cpc.ncep.noaa.gov | NOAA CPC | US Government work | 1w | ok |
| Daily AO index | `climate.ao` | ftp.cpc.ncep.noaa.gov | NOAA CPC | US Government work | 1d | ok |
| Daily NAO index | `climate.nao` | ftp.cpc.ncep.noaa.gov | NOAA CPC | US Government work | 1d | ok |
| Daily AAO index | `climate.aao` | ftp.cpc.ncep.noaa.gov | NOAA CPC | US Government work | 1d | ok |
| Daily PNA index | `climate.pna` | ftp.cpc.ncep.noaa.gov | NOAA CPC | US Government work | 1d | ok |
| Antarctic ozone hole area and minimum | `climate.ozone-hole` | ozonewatch.gsfc.nasa.gov | NASA Ozone Watch | US Government work | 1d | ok |
| MJO RMM index [L] | `climate.mjo` | www.bom.gov.au | Australian Bureau of Meteorology | BoM terms: attribution required | 1d | runner |
| Global mean sea level (NOAA STAR) | `climate.gmsl` | www.star.nesdis.noaa.gov | NOAA STAR Laboratory for Satellite Altimetry | US Government work | 1w | runner |

## Static files

| File | Source | License |
| --- | --- | --- |
| `static/coast-110m.json` | raw.githubusercontent.com | Public domain (Natural Earth) |

## Notes on terms

- WDC for Geomagnetism, Kyoto (Dst): non-commercial use, attribution required. Not a US Government license. The page shows the attribution in the widget and in the footer.
- SILSO, Royal Observatory of Belgium: CC BY-NC 4.0. Not a US Government license. The page shows the attribution in the widget and in the footer.
- GDACS (EC JRC, UN OCHA): attribution required. Not a US Government license. The page shows the attribution in the widget and in the footer.
- Australian Bureau of Meteorology (MJO): attribution required. Not a US Government license. The page shows the attribution in the widget and in the footer.
- This project is non-commercial (plan 17, Q5).
