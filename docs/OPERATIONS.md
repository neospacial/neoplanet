# Operations

This guide tells you how to set up the dashboard and keep it running.

## 0. Setup (one time, after the first merge to `main`)

1. **Pages:** Settings > **Pages** > Build and deployment > Source: **GitHub Actions**.
2. **Workflow permissions:** Settings > **Actions** > **General** > Workflow permissions: **Read and write permissions**. Click **Save**. The monthly keep-alive commit needs this.
3. **Secrets (optional):** Settings > **Secrets and variables** > **Actions** > **Secrets** tab > **New repository secret**.
   - `NASA_API_KEY` (from https://api.nasa.gov). Without it, DONKI uses `DEMO_KEY` and shows status "degraded".
   - `FIRMS_MAP_KEY` (from https://firms.modaps.eosdis.nasa.gov/api/map_key/). Without it, the pipeline uses the no-key 24-hour fire file. The status stays "ok".
4. **First run:** Actions > **run** > **Run workflow**. Set tier to `all` and backfill to `true`. Wait approx. 3 to 6 minutes. Then open `https://<owner>.github.io/<repository>/`.
5. After this, the schedule runs every 30 minutes (minutes 13 and 43 of each hour).

If the Pages deploy fails with "environment protection rules": Settings > Environments > github-pages > Deployment branches: allow `main`.

## 1. Read the data health widget (W13)

Open the page. Select **Widgets** > **Data health**, or select the preset **Overview**. The widget shows one row for each dataset.

| Column | Meaning |
| --- | --- |
| Status | `ok`: the last fetch worked and the data is new. `stale`: the data is older than `max_age_days` (or 10 x the tier). `degraded`: the pipeline uses a fallback (DONKI without `NASA_API_KEY`, or the sea level fallback). `error`: the last fetch failed. The page keeps the last good data. |
| Data age | The time since the newest value in the data. |
| Size | The size of the dataset in the store. |
| Budget | The size against `budget_mb` in `sources.json`. Amber: more than the budget. Red: more than 2 x the budget. |
| Message | The reason for the status. Example: `fetch failed: HTTP 503`. |

The first line gives the total store size against the 150 MB budget and the 1 GB site limit. Each warning from the manifest shows below it.

Each widget also shows a badge when its data is old: `▲ stale` (amber) after 3 x the cadence, and `■ error` (red) after 10 x the cadence.

If the manifest is older than 2 hours, the page shows a banner. Then the scheduled run does not work. Do these steps:

1. Open **Actions** > **run**. Look at the newest runs.
2. If no run is new, GitHub can have disabled the schedule. Make one commit on `main`. Then click **Run workflow**.
3. If the runs fail, open the newest failed run and read the log of the step **Run the pipeline**.

The same information is in `data/manifest.json` on the site, and in the summary of each run (Actions > run > the run > Summary). The summary has a table with the size of each dataset and of each class.

## 2. Datasets that fail on the runner

Three datasets have `"status": "runner"` in `sources.json`. They failed from the audit workspace:

| Dataset | Effect if it fails |
| --- | --- |
| `ocean.coral-alert` | Status `error`. The ocean map hides the "Coral alert" button. |
| `climate.mjo` | Status `error`. The page hides the widget. |
| `climate.gmsl` | The pipeline uses the area-weighted mean of the `ocean.sla` grid. Status `degraded`. |

## 3. Replace a broken URL with the audit

Do this when a dataset stays in status `error` and the message shows an HTTP error (example: `HTTP 404`) or a changed format (`parse failed` or `validation failed`).

1. Open **Actions** > **audit** > **Run workflow**.
2. In **only**, type the endpoint ID prefix (example: `swpc.` or `nsidc.`). Click **Run workflow**.
3. Open the run. Read the report in the summary. Download the artifact `phase0-audit` for the samples.
4. Find a working URL. The report lists directory listings and ERDDAP search results.
5. Change the `url` of the dataset in `sources.json`.
6. If the format changed, put the new sample in `fixtures/` and update the adapter in `fetch/adapters/`.
7. Run the tests: `python3 -m unittest discover -s fetch/tests`.
8. Run `python3 tools/sources_md.py` to update `docs/SOURCES.md`.
9. Open a pull request. Merge it when the tests pass.

If a source announces an end date, put the date in the `sunset` field (`YYYY-MM-DD`). The manifest gives a warning 60 days before that date.

## 4. Rotate a key

The pipeline reads two keys from GitHub secrets: `NASA_API_KEY` and `FIRMS_MAP_KEY`. No file contains a key.

1. Get a new key: https://api.nasa.gov or https://firms.modaps.eosdis.nasa.gov/api/map_key/.
2. Open the repository on github.com. Click **Settings** > **Secrets and variables** > **Actions**.
3. On the **Secrets** tab, click the pencil icon next to the secret name.
4. Paste the new key. Click **Update secret**.
5. Open **Actions** > **run** > **Run workflow** to use the key at once. If you do nothing, the next scheduled run uses it.
6. Revoke the old key on the site of the provider.

If `NASA_API_KEY` is missing, the pipeline uses `DEMO_KEY` and the DONKI datasets show status `degraded`. If `FIRMS_MAP_KEY` is missing, the pipeline uses the no-key fire file and the status stays `ok`.

## 5. The store

- The store lives in the GitHub Actions cache (key prefix `store-`). The run keeps the 3 newest entries.
- If no cache entry exists, the run downloads `data/` from the live site one time (plan 4.3).
- If the cache and the site are both lost: open **Actions** > **run** > **Run workflow** with tier `all` and backfill `true` (plan 4.4).
- The deploy stops when the store is larger than 300 MB. Find the dataset that is over its budget in the data health widget. Make its retention shorter in `sources.json`, or remove the dataset.

## 6. Run the pipeline on your computer

```sh
python3 -m unittest discover -s fetch/tests     # tests, no network
python3 tools/serve.py                          # fixture data on http://localhost:8000/?now=2026-10-20T18:00:00Z
python3 fetch/run.py --tier all --only space.   # real sources (network)
```
