"""Summary tiers: min, mean, max keep the peaks (plan 5.3)."""
import unittest

from helpers import StoreCase, common
from lib import rollup
from lib import store as st

DS = {"id": "test.fast", "kind": "series", "class": "A", "dt": 60,
      "retention": {"r": "7d", "m5": "30d", "h1": "1y", "d1": "5y"}}
COLS = [{"name": "x", "q": {"type": "log10", "scale": 1000}}]


class RollupTest(StoreCase):
    def test_summarize_keeps_peak(self):
        t0 = common.parse_iso("2026-10-20T10:00:00Z")
        rows = {t0 + 60 * i: [1e-6] for i in range(60)}
        rows[t0 + 60 * 17] = [3e-4]        # a short X-class peak
        out = rollup.summarize(rows, 1, 3600)
        mn, mean, mx = out[t0]
        self.assertEqual(mn, 1e-6)
        self.assertEqual(mx, 3e-4)
        self.assertGreater(mean, 1e-6)

    def test_summarize_skips_null_and_last(self):
        out = rollup.summarize({0: [None], 60: [2.0], 120: [4.0], 180: [None]}, 1, 300,
                               rollup.STATS + ("last",))
        self.assertEqual(out[0], [2.0, 3.0, 4.0, 4.0])

    def test_mean_only_when_bucket_equals_step(self):
        self.assertEqual(rollup.stats_for(300, 300), ("mean",))
        self.assertEqual(rollup.stats_for(3600, 300), ("min", "mean", "max"))
        self.assertEqual(rollup.stats_for(3600, 60, last=True), ("min", "mean", "max", "last"))

    def test_update_all_tiers_and_peak_survives_raw_prune(self):
        t0 = common.parse_iso("2026-10-10T10:00:00Z")
        rows = {t0 + 60 * i: [1e-6] for i in range(180)}
        rows[t0 + 60 * 75] = [2e-4]
        self.store.merge_series(DS, "r", rows, COLS, 60, "day")
        rollup.update(self.store, DS, COLS, min(rows), max(rows))
        self.store.prune_tier(DS, "r", "day", 7 * 86400)       # raw day is older than 7 d
        self.assertEqual(self.store.list(DS, "r"), [])
        for tier, span in (("m5", "month"), ("h1", "month"), ("d1", "all")):
            names = ["x.min", "x.mean", "x.max"]
            got = self.store.load_rows(DS, tier, span, names, 0, 2 ** 40)
            peak = max(v[2] for v in got.values())
            self.assertAlmostEqual(peak, 2e-4, delta=2e-4 * 0.003, msg=tier)
        h1 = self.store.read(DS, "h1/2026-10.json")
        self.assertEqual(h1["dt"], 3600)
        self.assertEqual(h1["n"], 3)


if __name__ == "__main__":
    unittest.main()
