"""Adapter swpc_table: Kp, Dst, F10.7, Kp forecast."""
import unittest

from helpers import StoreCase, common


class SwpcTableTest(StoreCase):
    def test_kp(self):
        s = self.parse("space.kp")["series"]
        self.assertEqual(len(s["rows"]), 61)
        last = max(s["rows"])
        self.assertEqual(common.iso(last), "2026-10-20T12:00:00Z")
        self.assertEqual(s["rows"][last], [2.0])
        self.assertTrue(s["last"])        # Kp keeps 'last' in the summaries

    def test_kp_store_and_daily_summary(self):
        out = self.process("space.kp")
        self.assertEqual(out["status"], "ok")
        shard = self.read("space.kp", "r/2026-10.json")
        self.assertEqual(shard["dt"], 10800)
        self.assertEqual(shard["q"]["kp"], {"type": "lin", "scale": 100})
        d1 = self.read("space.kp", "d1/all.json")
        self.assertIn("kp.max", d1["cols"])
        self.assertIn("kp.last", d1["cols"])

    def test_dst(self):
        s = self.parse("space.dst")["series"]
        self.assertEqual(len(s["rows"]), 168)
        self.assertEqual(s["rows"][max(s["rows"])], [-15.0])

    def test_f107(self):
        s = self.parse("space.f107")["series"]
        self.assertEqual(len(s["rows"]), 30)
        self.assertEqual(s["rows"][common.parse_iso("2026-10-19")], [121.0])

    def test_kp_forecast_is_latest_only(self):
        r = self.parse("space.kp-forecast")
        f = r["forecast"]
        self.assertEqual(len(f["rows"]), 81)
        kinds = {v[1] for v in f["rows"].values()}
        self.assertEqual(kinds, {0, 1, 2})
        self.assertEqual(common.iso(f["issued"]), "2026-10-20T12:00:00Z")
        self.process("space.kp-forecast")
        latest = self.read("space.kp-forecast", "latest.json")
        self.assertEqual(latest["series"]["n"], 81)
        self.assertEqual(self.store.list({"id": "space.kp-forecast", "kind": "forecast"}, "r"), [])


if __name__ == "__main__":
    unittest.main()
