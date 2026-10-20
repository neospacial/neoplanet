# Fixtures (v0.3.0)

Real responses from each source, saved by the Phase 0 audit (tools/audit, v0.1.1) on 2026-10-20.
The file name is the audit endpoint ID. `sources.json` gives the fixture for each dataset.

Trim rules (to keep the repository small):

- JSON lists with more than 600 items: the newest 600 items. A header row stays.
- CSV and text files with more than 1,200 lines: the header block and the newest 800 lines.
- FIRMS fires: the header and the first 3,000 points.
- ERDDAP grid CSV: every second latitude and longitude (2 degree test grid). Header and units rows stay.
- OVATION aurora: the full 1 degree grid (needed for the 2 degree regrid test).

Known content:

- `ndbc.dart-21414.txt` is from a station whose newest data was 40 days old. Use it for the format and the stale-station rule (plan 9.4d).
- `nhc.current-storms.json` has an empty storm list (rule 9.4g).
- No fixture exists for DONKI (rate limited during the audit), coral alert, MJO, and global mean sea level (blocked from the audit workspace). Write their adapters from the documented formats and mark the tests "skipped until a fixture exists". Run `audit.yml` on the runner to get real samples (artifact `phase0-audit`, folder `samples/`).
