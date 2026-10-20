# Phase 0: endpoint audit (v0.1.1)

This audit checks every candidate data source in the plan before we write the pipeline.
It runs in GitHub Actions because the runner can reach the government sites.

## What it measures

For each endpoint in `endpoints.json`:

| Item | Use in the plan |
| --- | --- |
| HTTP status, redirect, response time | Find dead or moved URLs (plan 8, the [V] marks). |
| ETag, Last-Modified, and a test conditional GET (304) | Decide how each adapter detects new data (plan 9.1, step 2). |
| Cache-Control, Expires | Set the poll interval for each source (plan 9.2). |
| Server gzip, body size, local gzip size | Check the bandwidth and fetch time. |
| Shape, columns, types, null %, samples | Write the adapter and its schema check (plan 9.1, step 5). |
| First and last time, step, age of newest data | Confirm the cadence and the latency. |
| Estimated store size (quantized format) | Correct the size table (plan 6.4). |
| Directory listings and ERDDAP search results | Find the correct file names and dataset IDs. |

Each response is also saved in `samples/`. These files become the test fixtures in Phase 1.

## How to run

1. The files are in the repository:
   - `tools/audit/audit.py`
   - `tools/audit/endpoints.json`
   - `.github/workflows/audit.yml`
2. Optional: add these repository secrets (Settings > Secrets and variables > Actions):
   - `NASA_API_KEY` from https://api.nasa.gov. If it is not set, the audit uses `DEMO_KEY` (low rate limit).
   - `FIRMS_MAP_KEY` from https://firms.modaps.eosdis.nasa.gov/api/map_key/. If it is not set, the audit skips the FIRMS API test. The no-key FIRMS file is tested.
3. Open Actions > "audit" > Run workflow. Leave the fields blank for a full run (approx. 2 to 5 minutes).
4. Read the report on the run summary page. Download the artifact `phase0-audit` for `report.json` and `samples/`.

To test one group again, enter prefixes in the "only" field, for example `swpc.,nasa.donki`.

## GitHub Pages check

After you turn on Pages (Settings > Pages > Source: GitHub Actions), put one test JSON file on the site.
Then run the workflow again with `pages_url` set to that file URL.
The report then shows if Pages sends gzip and how it answers a conditional GET.

## Runner minutes

Standard GitHub-hosted runners are free for public repositories. Verify this in Settings > Billing for your account.
One full audit uses approx. 5 minutes.

## Local run

`python3 tools/audit/audit.py --endpoints tools/audit/endpoints.json --out audit-out` (Python 3.9+, no packages). Many government sites block
cloud IP ranges, so a local run can show failures that do not occur on the runner.

## After the run

1. Send the `report.md` (or the artifact zip) back.
2. For each item in "Action items", pick one action: replace the URL, add a time hint, or remove the dataset.
3. Update the plan table 6.4 with the measured sizes.
4. Phase 1 starts with the endpoints that passed.
