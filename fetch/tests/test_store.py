"""Store: quantize, merge, never shrink, prune, sparse grid, atomic write (plan 5)."""
import os
import unittest

from helpers import StoreCase, common
from lib import store as st

DS = {"id": "test.series", "kind": "series", "class": "A", "dt": 60,
      "retention": {"r": "7d", "m5": "30d", "h1": "1y", "d1": "5y"}}
COLS = [{"name": "a", "q": {"type": "lin", "scale": 10}}, {"name": "b", "q": {"type": "log10", "scale": 1000}}]


class QuantizeTest(StoreCase):
    def test_linear_round_trip(self):
        q = {"type": "lin", "scale": 10}
        for v in (0.0, -2.4, 381.4, 6.78):
            self.assertAlmostEqual(st.dequantize(st.quantize(v, q), q), v, delta=0.05)

    def test_log_round_trip(self):
        q = {"type": "log10", "scale": 1000}
        for v in (1e-9, 5.15e-7, 0.27, 350.0, 1e5):
            back = st.dequantize(st.quantize(v, q), q)
            self.assertLess(abs(back - v) / v, 0.0024)

    def test_missing(self):
        q = {"type": "log10", "scale": 1000}
        self.assertIsNone(st.quantize(None, q))
        self.assertIsNone(st.quantize(float("nan"), q))
        self.assertIsNone(st.quantize(0, q))         # log of zero
        self.assertIsNone(st.quantize(-1e-9, q))
        self.assertIsNone(st.dequantize(None, q))


class ShardCodecTest(StoreCase):
    def test_regular_round_trip_and_trim(self):
        start = common.parse_iso("2026-10-20")
        rows = {start + 600: [1.5, 1e-6], start + 660: [None, 2e-6], start + 1200: [3.0, None]}
        shard = st.encode_series("x", rows, COLS, 60, start, start + 86400)
        self.assertEqual(shard["t0"], start + 600)       # empty slots at the start are trimmed
        self.assertEqual(shard["n"], 11)                 # and at the end
        self.assertIsNone(shard["cols"]["a"][1])          # a gap stays null
        back = st.decode_series(shard)
        self.assertEqual(sorted(back), sorted(rows))
        self.assertAlmostEqual(back[start + 660][1], 2e-6, delta=1e-8)

    def test_irregular_delta_times(self):
        rows = {100: [1.0, None], 250: [2.0, None], 1000: [3.0, None]}
        shard = st.encode_series("x", rows, COLS)
        self.assertEqual(shard["t0"], 100)
        self.assertEqual(shard["t"], [0, 150, 750])
        self.assertEqual(sorted(st.decode_series(shard)), [100, 250, 1000])


class MergeTest(StoreCase):
    def test_merge_overlap_and_replace(self):
        t = common.parse_iso("2026-10-20T10:00:00Z")
        self.store.merge_series(DS, "r", {t: [1.0, None], t + 60: [2.0, None]}, COLS, 60, "day")
        self.store.merge_series(DS, "r", {t + 60: [5.0, None], t + 120: [6.0, None]}, COLS, 60, "day")
        rows = st.decode_series(self.store.read(DS, "r/2026-10-20.json"))
        self.assertEqual([rows[t][0], rows[t + 60][0], rows[t + 120][0]], [1.0, 5.0, 6.0])

    def test_null_does_not_remove_old_value(self):
        t = common.parse_iso("2026-10-20T10:00:00Z")
        self.store.merge_series(DS, "r", {t: [1.0, 1e-6]}, COLS, 60, "day")
        self.store.merge_series(DS, "r", {t: [None, 2e-6]}, COLS, 60, "day")
        rows = st.decode_series(self.store.read(DS, "r/2026-10-20.json"))
        self.assertEqual(rows[t][0], 1.0)

    def test_merge_splits_by_day(self):
        t = common.parse_iso("2026-10-19T23:59:00Z")
        self.store.merge_series(DS, "r", {t: [1.0, None], t + 60: [2.0, None]}, COLS, 60, "day")
        self.assertEqual(self.store.list(DS, "r"), ["2026-10-19", "2026-10-20"])

    def test_atomic_write_reports_change(self):
        path = os.path.join(self.tmp, "x", "f.json")
        self.assertTrue(common.write_json(path, {"a": 1}))
        self.assertFalse(common.write_json(path, {"a": 1}))
        self.assertTrue(common.write_json(path, {"a": 2}))
        self.assertEqual([f for f in os.listdir(os.path.dirname(path)) if f.startswith(".tmp")], [])


class NeverShrinkTest(StoreCase):
    def test_check_raises(self):
        old = st.encode_series("x", {100: [1.0, None], 160: [2.0, None]}, COLS, 60, 100, 400)
        new = st.encode_series("x", {100: [1.0, None]}, COLS, 60, 100, 400)
        with self.assertRaises(st.ShrinkError):
            st.check_never_shrink(old, new)
        st.check_never_shrink(old, new, window_start=150 + 60)   # old time outside the window: allowed

    def test_shard_on_disk_is_not_replaced(self):
        t = common.parse_iso("2026-10-20T10:00:00Z")
        self.store.merge_series(DS, "r", {t: [1.0, None], t + 60: [2.0, None]}, COLS, 60, "day")
        before = self.store.read(DS, "r/2026-10-20.json")
        # Simulate a broken merge: new columns do not include the old column.
        with self.assertRaises(st.ShrinkError):
            self.store.merge_series(DS, "r", {t + 120: [None, 1e-6]},
                                    [{"name": "c", "q": {"type": "lin", "scale": 1}},
                                     {"name": "b", "q": {"type": "log10", "scale": 1000}}], 60, "day")
        self.assertEqual(self.store.read(DS, "r/2026-10-20.json"), before)


class PruneTest(StoreCase):
    def test_prune_day_shards(self):
        for d in range(10):
            t = self.now - d * 86400
            self.store.merge_series(DS, "r", {t - t % 60: [float(d), None]}, COLS, 60, "day")
        self.assertEqual(len(self.store.list(DS, "r")), 10)
        removed = self.store.prune_tier(DS, "r", "day", 7 * 86400)
        # The cutoff is 7 d before 18:00. The day shard that contains the cutoff stays.
        self.assertEqual(removed, 2)
        self.assertEqual(self.store.list(DS, "r")[0], common.ymd(self.now - 7 * 86400))

    def test_prune_trims_all_shard(self):
        rows = {common.day_start(self.now) - d * 86400: [float(d), None] for d in range(20)}
        self.store.merge_series(DS, "d1", rows, COLS, 86400, "all")
        self.store.prune_tier(DS, "d1", "all", 10 * 86400)
        shard = self.store.read(DS, "d1/all.json")
        self.assertGreaterEqual(shard["t0"], self.now - 11 * 86400)
        self.assertLessEqual(shard["n"], 11)

    def test_prune_event_months(self):
        ds = {"id": "test.events", "kind": "events"}
        ev = lambda i, t: {"id": i, "t_start": t, "type": "x"}
        self.store.merge_events(ds, [ev("a", self.now - 400 * 86400), ev("b", self.now)], 365 * 86400)
        self.assertEqual([e["id"] for e in self.store.all_events(ds)], ["b"])

    def test_event_moves_month(self):
        ds = {"id": "test.events", "kind": "events"}
        t = common.parse_iso("2026-10-01T01:00:00Z")
        self.store.merge_events(ds, [{"id": "a", "t_start": t, "type": "x"}])
        self.store.merge_events(ds, [{"id": "a", "t_start": t - 7200, "type": "x"}])
        self.assertEqual(len(self.store.all_events(ds)), 1)


class SparseGridTest(StoreCase):
    def test_round_trip_zero_fill(self):
        q = {"type": "lin", "scale": 1}
        vals = [0] * 50 + [3, 7, 0, 9] + [0] * 40 + [12] + [0] * 5
        enc = st.encode_grid(vals, q, fill=0)
        self.assertEqual(enc, [50, 2, 3, 7, 1, 1, 9, 40, 1, 12])
        self.assertEqual(st.decode_grid(enc, q, len(vals), fill=0), vals)

    def test_round_trip_null_fill_with_zero_values(self):
        q = {"type": "lin", "scale": 100}
        vals = [None, None, 0.0, -1.25, None, 2.5, 0.0]
        enc = st.encode_grid(vals, q, fill=None)
        back = st.decode_grid(enc, q, len(vals), fill=None)
        self.assertEqual(back, vals)        # a zero anomaly is not land

    def test_empty_grid(self):
        q = {"type": "lin", "scale": 1}
        self.assertEqual(st.encode_grid([0] * 10, q, 0), [])
        self.assertEqual(st.decode_grid([], q, 10, 0), [0] * 10)


if __name__ == "__main__":
    unittest.main()
